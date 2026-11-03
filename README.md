# 🗺️ CodeAtlas

**CodeAtlas** is an intelligent software project analysis platform that automatically analyzes codebases, visualizes their structure and relationships, and helps users understand unfamiliar projects quickly.

## 🎯 Features

### 🔐 User Authentication
- User registration and login
- Secure password hashing with bcrypt
- JWT-based authentication
- User-specific project access

### 📦 Project Upload
- Upload projects as ZIP files
- Add projects via GitHub repository URLs
- Automatic project organization

### 🔍 Automatic Code Analysis
- Detects programming languages used
- Identifies files and folders
- Extracts classes and functions (Python)
- Analyzes project structure
- Maps dependencies between files

### 🗂️ Project Structure Explorer
- Visual tree representation of project hierarchy
- Easy navigation through complex codebases
- File and folder organization display

### 🕸️ Dependency Mapping
- Visual representation of file dependencies
- Import analysis for Python projects
- Understanding module relationships

### 📊 Project Dashboard
- Overview of all uploaded projects
- Quick access to project analysis
- Project statistics and metadata

## 🚀 Technology Stack

### Backend
- **Python** - Core language
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **SQLite** - Database

### Frontend
- **HTML5/CSS3/JavaScript** - User interface
- **Responsive Design** - Mobile-friendly

### Code Analysis
- **Python AST** - Abstract Syntax Tree parsing
- **File-system analysis** - Structure detection

### Authentication
- **Passlib** - Password hashing
- **JWT** - Token-based authentication
- **OAuth2** - Security protocol

## 📋 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CodeAtlas
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Unix
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   uvicorn app:app --reload
   ```

5. **Access the application**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Frontend: Open `frontend/index.html` in your browser

## 🎮 Usage

### 1. Register a User Account
- Navigate to the application
- Click "Login" → "Register"
- Fill in username, email, and password
- Submit the form

### 2. Upload a Project
- Click "Upload Project" after logging in
- Choose upload method:
  - **ZIP Upload**: Select a ZIP file containing your project
  - **GitHub URL**: Enter a GitHub repository URL
- Provide project name and description
- Click "Upload & Analyze"

### 3. View Project Analysis
- Go to "Dashboard" to see all projects
- Click on a project card to view its analysis
- Explore different tabs:
  - **Overview**: File count, folder count, languages
  - **Structure**: Visual tree of project hierarchy
  - **Dependencies**: File import relationships

## 🔧 API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token
- `GET /users/me` - Get current user info

### Projects
- `POST /projects/upload` - Upload ZIP project
- `POST /projects/github` - Add GitHub project
- `GET /projects` - List all user projects
- `GET /projects/{project_id}` - Get specific project

### Analysis
- `POST /projects/{project_id}/analyze` - Analyze a project
- `GET /projects/{project_id}/analysis` - Get project analysis
- `GET /projects/{project_id}/structure` - Get project structure
- `GET /projects/{project_id}/dependencies` - Get project dependencies

## 📁 Project Structure

```
CodeAtlas/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── backend/              # Backend modules
│   ├── __init__.py
│   ├── auth.py          # Authentication functions
│   ├── database.py      # Database configuration
│   └── models.py        # SQLAlchemy models
├── analyser/            # Code analysis modules
│   ├── __init__.py
│   └── python_analyzer.py  # Python AST analyzer
├── frontend/            # Frontend files
│   ├── index.html       # Main HTML page
│   ├── styles.css       # Styling
│   └── script.js        # JavaScript logic
├── uploads/             # Uploaded project files
└── venv/               # Virtual environment
```

## 🔐 Security Notes

- Change the `SECRET_KEY` in `backend/auth.py` for production
- Use environment variables for sensitive configuration
- Implement rate limiting for production deployment
- Add HTTPS for secure communication

## 🚧 Future Enhancements

- [ ] GitHub repository cloning and analysis
- [ ] Multi-language support (JavaScript, Java, etc.)
- [ ] AI-powered code explanations
- [ ] Advanced dependency visualization
- [ ] Code quality metrics
- [ ] Team collaboration features
- [ ] Export analysis reports

## 📝 License

This project is developed for educational purposes.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues, questions, or suggestions, please open an issue in the repository.

---

**One-line explanation**: "CodeAtlas is an intelligent software project analysis platform that automatically analyzes a codebase, visualizes its structure and relationships, and helps users understand unfamiliar projects."
