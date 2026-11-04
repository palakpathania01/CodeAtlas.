from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    projects = relationship("Project", back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    source_type = Column(String)  # "zip" or "github"
    source_url = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="projects")
    analyses = relationship("Analysis", back_populates="project")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    file_count = Column(Integer, default=0)
    folder_count = Column(Integer, default=0)
    languages = Column(Text)  # JSON string
    structure = Column(Text)  # JSON string
    dependencies = Column(Text)  # JSON string
    internal_dependencies = Column(Text)  # JSON string
    external_dependencies = Column(Text)  # JSON string
    classes = Column(Text)  # JSON string
    functions = Column(Text)  # JSON string
    file_details = Column(Text)  # JSON string
    lines_of_code = Column(Integer, default=0)
    total_classes = Column(Integer, default=0)
    total_functions = Column(Integer, default=0)
    cyclomatic_complexity = Column(Text)  # JSON string
    code_duplication = Column(Text)  # JSON string
    average_complexity = Column(Integer, default=0)
    ml_analysis = Column(Text)  # JSON string for ML results
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="analyses")