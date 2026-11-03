from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import timedelta
from pydantic import BaseModel, EmailStr, validator
import json
import shutil
import os
from typing import Optional
import logging

from backend.database import Base, engine, get_db
from backend.models import User, Project, Analysis
from backend.auth import hash_password, verify_password, create_access_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES
from analyser import PythonAnalyzer
from ml_analyzer import CodeQualityAnalyzer, BugDetector, SecurityAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CodeAtlas")

# Mount static files for frontend
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Create database tables
Base.metadata.create_all(bind=engine)

# Serve the frontend at root
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Pydantic models with validation
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @validator('username')
    def username_length(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 20:
            raise ValueError('Username must not exceed 20 characters')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: str  # "zip" or "github"
    source_url: Optional[str] = None
    
    @validator('source_type')
    def validate_source_type(cls, v):
        if v not in ['zip', 'github']:
            raise ValueError('Source type must be either "zip" or "github"')
        return v
    
    @validator('name')
    def name_length(cls, v):
        if len(v) < 2:
            raise ValueError('Project name must be at least 2 characters')
        return v


# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        username = verify_token(token)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/")
def home():
    return {
        "message": "Welcome to CodeAtlas!",
        "status": "Backend is running"
    }


@app.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(
            User.username == user.username
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        # Check if email already exists
        existing_email = db.query(User).filter(
            User.email == user.email
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        new_user = User(
            username=user.username,
            email=user.email,
            password=hash_password(user.password)
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"New user registered: {user.username}")
        
        return {
            "message": "User registered successfully",
            "username": new_user.username,
            "email": new_user.email
        }
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == user_data.username).first()
        
        if not user or not verify_password(user_data.password, user.password):
            logger.warning(f"Failed login attempt for username: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        logger.info(f"User logged in: {user.username}")
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at
    }


# Project upload endpoints
@app.post("/projects/upload")
async def upload_project(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{current_user.username}_{name}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save the uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )
    
    # Create project record
    new_project = Project(
        name=name or file.filename,
        description=description,
        source_type="zip",
        source_url=file_path,
        user_id=current_user.id
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return {
        "message": "Project uploaded successfully",
        "project_id": new_project.id,
        "name": new_project.name,
        "source_type": new_project.source_type
    }


@app.post("/projects/github")
async def add_github_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if project.source_type != "github":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source type must be 'github' for this endpoint"
        )
    
    if not project.source_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub URL is required"
        )
    
    # Create project record
    new_project = Project(
        name=project.name,
        description=project.description,
        source_type="github",
        source_url=project.source_url,
        user_id=current_user.id
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return {
        "message": "GitHub project added successfully",
        "project_id": new_project.id,
        "name": new_project.name,
        "source_url": new_project.source_url
    }


@app.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Delete associated analyses
    db.query(Analysis).filter(Analysis.project_id == project_id).delete()
    
    # Delete project
    db.delete(project)
    db.commit()
    
    logger.info(f"Project deleted: {project.name} by user {current_user.username}")
    
    return {"message": "Project deleted successfully"}


@app.get("/projects")
async def get_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    
    return {
        "projects": [
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "source_type": project.source_type,
                "source_url": project.source_url,
                "created_at": project.created_at
            }
            for project in projects
        ]
    }


@app.get("/projects/{project_id}")
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "source_type": project.source_type,
        "source_url": project.source_url,
        "created_at": project.created_at
    }


# Analysis endpoints
@app.post("/projects/{project_id}/analyze")
async def analyze_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    analyzer = PythonAnalyzer()
    quality_analyzer = CodeQualityAnalyzer()
    bug_detector = BugDetector()
    security_analyzer = SecurityAnalyzer()
    
    try:
        temp_dir = None
        if project.source_type == "zip":
            results = analyzer.analyze_zip(project.source_url)
            temp_dir = 'temp_extract'
        elif project.source_type == "github":
            # Clone GitHub repo and analyze
            import subprocess
            import tempfile
            import shutil
            
            # Check if git is available in PATH
            try:
                subprocess.run(['git', '--version'], check=True, capture_output=True, shell=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Git command-line tool is not available. GitHub Desktop alone is not sufficient. Please install Git for Windows from https://git-scm.com/download/win to analyze GitHub repositories, or upload a ZIP file instead."
                )
            
            # Create temp directory for cloning
            temp_dir = tempfile.mkdtemp()
            try:
                # Clone the repository
                subprocess.run(['git', 'clone', project.source_url, temp_dir], check=True, capture_output=True, shell=True)
                results = analyzer.analyze_directory(temp_dir)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone GitHub repo: {e.stderr.decode()}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to clone GitHub repository: {e.stderr.decode()}. Please check the URL and ensure it's a public repository."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported source type"
            )
        
        # Run ML-based analysis on Python files
        ml_results = {
            'code_quality': {},
            'bug_detection': {},
            'security_analysis': {}
        }
        
        # Analyze Python files with ML models
        import os
        if temp_dir and os.path.exists(temp_dir):
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            # Code quality analysis
                            quality_result = quality_analyzer.analyze_file(file_path)
                            ml_results['code_quality'][file] = quality_result
                            
                            # Bug detection
                            bug_result = bug_detector.analyze_file(file_path)
                            ml_results['bug_detection'][file] = bug_result
                            
                            # Security analysis
                            security_result = security_analyzer.analyze_file(file_path)
                            ml_results['security_analysis'][file] = security_result
                        except Exception as e:
                            logger.warning(f"ML analysis failed for {file}: {str(e)}")
        
        # Clean up temp directory
        import shutil
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Convert sets to lists for JSON serialization
        def convert_sets_to_lists(obj):
            if isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, dict):
                return {k: convert_sets_to_lists(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_sets_to_lists(item) for item in obj]
            return obj
        
        results = convert_sets_to_lists(results)
        
        # Create analysis record with ML results
        new_analysis = Analysis(
            project_id=project.id,
            file_count=results['file_count'],
            folder_count=results['folder_count'],
            languages=json.dumps(results['languages']),
            structure=json.dumps(results['structure']),
            dependencies=json.dumps(results['dependencies']),
            internal_dependencies=json.dumps(results.get('internal_dependencies', {})),
            external_dependencies=json.dumps(results.get('external_dependencies', {})),
            classes=json.dumps(results.get('classes', {})),
            functions=json.dumps(results.get('functions', {})),
            file_details=json.dumps(results.get('file_details', {})),
            lines_of_code=results.get('lines_of_code', 0),
            total_classes=results.get('total_classes', 0),
            total_functions=results.get('total_functions', 0),
            ml_analysis=json.dumps(ml_results)
        )
        
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        
        return {
            "message": "Project analyzed successfully with AI/ML insights",
            "analysis_id": new_analysis.id,
            "results": results,
            "ml_results": ml_results
        }
    
    except Exception as e:
        logger.error(f"Error analyzing project: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing project: {str(e)}"
        )


@app.get("/projects/{project_id}/analysis")
async def get_project_analysis(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    analysis = db.query(Analysis).filter(Analysis.project_id == project_id).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found for this project"
        )
    
    return {
        "analysis_id": analysis.id,
        "project_id": analysis.project_id,
        "file_count": analysis.file_count,
        "folder_count": analysis.folder_count,
        "languages": json.loads(analysis.languages) if analysis.languages else [],
        "structure": json.loads(analysis.structure) if analysis.structure else {},
        "dependencies": json.loads(analysis.dependencies) if analysis.dependencies else {},
        "internal_dependencies": json.loads(analysis.internal_dependencies) if analysis.internal_dependencies else {},
        "external_dependencies": json.loads(analysis.external_dependencies) if analysis.external_dependencies else {},
        "classes": json.loads(analysis.classes) if analysis.classes else {},
        "functions": json.loads(analysis.functions) if analysis.functions else {},
        "file_details": json.loads(analysis.file_details) if analysis.file_details else {},
        "lines_of_code": analysis.lines_of_code or 0,
        "total_classes": analysis.total_classes or 0,
        "total_functions": analysis.total_functions or 0,
        "ml_analysis": json.loads(analysis.ml_analysis) if analysis.ml_analysis else {},
        "created_at": analysis.created_at
    }


@app.get("/projects/{project_id}/structure")
async def get_project_structure(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    analysis = db.query(Analysis).filter(Analysis.project_id == project_id).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found for this project"
        )
    
    return {
        "structure": json.loads(analysis.structure) if analysis.structure else {}
    }


@app.get("/projects/{project_id}/dependencies")
async def get_project_dependencies(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    analysis = db.query(Analysis).filter(Analysis.project_id == project_id).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found for this project"
        )
    
    return {
        "dependencies": json.loads(analysis.dependencies) if analysis.dependencies else {}
    }