"""
Python Code Analyzer Module

This module provides functionality to analyze Python codebases using Abstract Syntax Trees (AST).
It extracts information about project structure, dependencies, classes, and functions.
"""

import ast
import os
import zipfile
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class PythonAnalyzer:
    """
    Analyzes Python code using AST to extract structure and dependencies.
    
    This class provides methods to analyze Python projects from ZIP files or directories,
    extracting information about:
    - Project structure (files and folders)
    - Programming languages used
    - Import dependencies between files
    - Classes and their methods
    - Functions and their parameters
    """
    
    def __init__(self) -> None:
        """Initialize the PythonAnalyzer with empty state."""
        self.languages: Set[str] = set()
        self.file_count: int = 0
        self.folder_count: int = 0
        self.structure: Dict[str, Any] = {}
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.classes: Dict[str, List[Dict[str, Any]]] = {}
        self.functions: Dict[str, List[Dict[str, Any]]] = {}
        self.file_details: Dict[str, Dict[str, Any]] = {}
        self.lines_of_code: int = 0
        self.internal_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.external_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.cyclomatic_complexity: Dict[str, int] = {}
        self.code_duplication: Dict[str, List[str]] = {}
    
    def analyze_zip(self, zip_path: str) -> Dict[str, Any]:
        """
        Analyze a ZIP file containing Python code.
        
        Args:
            zip_path: Path to the ZIP file to analyze
            
        Returns:
            Dictionary containing analysis results including file counts,
            languages, structure, and dependencies
            
        Raises:
            zipfile.BadZipFile: If the ZIP file is corrupted
            OSError: If file operations fail
        """
        self._reset()
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall('temp_extract')
            
            self._analyze_directory('temp_extract')
            
            # Clean up
            import shutil
            shutil.rmtree('temp_extract', ignore_errors=True)
            
            logger.info(f"Successfully analyzed ZIP file: {zip_path}")
            return self._get_results()
        
        except Exception as e:
            logger.error(f"Error analyzing ZIP file {zip_path}: {str(e)}")
            raise
    
    def analyze_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Analyze a directory containing Python code.
        
        Args:
            directory_path: Path to the directory to analyze
            
        Returns:
            Dictionary containing analysis results including file counts,
            languages, structure, and dependencies
            
        Raises:
            OSError: If directory operations fail
        """
        self._reset()
        self._analyze_directory(directory_path)
        logger.info(f"Successfully analyzed directory: {directory_path}")
        return self._get_results()
    
    def _reset(self) -> None:
        """Reset analyzer state to initial values."""
        self.languages = set()
        self.file_count = 0
        self.folder_count = 0
        self.structure = {}
        self.dependencies = defaultdict(set)
        self.classes = {}
        self.functions = {}
        self.file_details = {}
        self.lines_of_code = 0
        self.internal_dependencies = defaultdict(set)
        self.external_dependencies = defaultdict(set)
    
    def _analyze_directory(self, directory_path: str) -> None:
        """
        Recursively analyze directory structure and contents.
        
        Args:
            directory_path: Path to the directory to analyze
        """
        self.structure = self._build_directory_structure(directory_path)
        
        for root, dirs, files in os.walk(directory_path):
            self.folder_count += len(dirs)
            
            for file in files:
                file_path = os.path.join(root, file)
                self.file_count += 1
                
                # Detect language by extension
                if file.endswith('.py'):
                    self.languages.add('Python')
                    self._analyze_python_file(file_path, directory_path)
                elif file.endswith('.js'):
                    self.languages.add('JavaScript')
                elif file.endswith('.html'):
                    self.languages.add('HTML')
                elif file.endswith('.css'):
                    self.languages.add('CSS')
                elif file.endswith('.java'):
                    self.languages.add('Java')
                elif file.endswith('.cpp') or file.endswith('.h'):
                    self.languages.add('C++')
                elif file.endswith('.c'):
                    self.languages.add('C')
    
    def _build_directory_structure(self, directory_path: str) -> Dict[str, Any]:
        """
        Build a nested dictionary representing directory structure.
        
        Args:
            directory_path: Path to the directory to analyze
            
        Returns:
            Nested dictionary where keys are file/folder names and values
            are either None (for files) or nested dicts (for folders)
        """
        structure: Dict[str, Any] = {}
        base_path = directory_path.rstrip(os.sep)
        
        for root, dirs, files in os.walk(base_path):
            relative_path = os.path.relpath(root, base_path)
            if relative_path == '.':
                current_level = structure
            else:
                current_level = self._get_nested_level(structure, relative_path.split(os.sep))
            
            for dir_name in dirs:
                current_level[dir_name] = {}
            
            for file_name in files:
                current_level[file_name] = None
        
        return structure
    
    def _get_nested_level(self, structure: Dict[str, Any], path_parts: List[str]) -> Dict[str, Any]:
        """
        Navigate to nested level in structure dictionary.
        
        Args:
            structure: The structure dictionary to navigate
            path_parts: List of path components to traverse
            
        Returns:
            Dictionary at the specified nested level
        """
        current = structure
        for part in path_parts:
            if part not in current:
                current[part] = {}
            current = current[part]
        return current
    
    def _analyze_python_file(self, file_path: str, base_path: str) -> None:
        """
        Analyze a single Python file using AST.
        
        Args:
            file_path: Path to the Python file to analyze
            base_path: Base path for calculating relative paths
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            relative_path = os.path.relpath(file_path, base_path)
            
            # Count lines of code
            lines = content.split('\n')
            code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
            self.lines_of_code += len(code_lines)
            
            # Extract file details
            self.file_details[relative_path] = {
                'total_lines': len(lines),
                'code_lines': len(code_lines),
                'comment_lines': len([line for line in lines if line.strip().startswith('#')]),
                'blank_lines': len([line for line in lines if not line.strip()])
            }
            
            # Extract imports for dependency analysis
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.dependencies[relative_path].add(alias.name)
                        # Check if it's an external dependency
                        if not alias.name.startswith('.'):
                            self.external_dependencies[relative_path].add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module if node.module else ''
                    for alias in node.names:
                        full_import = f"{module}.{alias.name}" if module else alias.name
                        self.dependencies[relative_path].add(full_import)
                        # Check if it's internal (starts with .)
                        if module and module.startswith('.'):
                            self.internal_dependencies[relative_path].add(full_import)
                        else:
                            self.external_dependencies[relative_path].add(full_import)
            
            # Calculate cyclomatic complexity for this file
            complexity = self._calculate_cyclomatic_complexity(tree)
            self.cyclomatic_complexity[relative_path] = complexity
            
            # Detect code duplication
            duplicates = self._detect_code_duplication(content)
            if duplicates:
                self.code_duplication[relative_path] = duplicates
            
            # Extract classes and functions with more details
            self.classes[relative_path] = []
            self.functions[relative_path] = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'methods': [],
                        'bases': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases],
                        'docstring': ast.get_docstring(node),
                        'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list],
                        'line_number': node.lineno
                    }
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                'name': item.name,
                                'args': [arg.arg for arg in item.args.args],
                                'docstring': ast.get_docstring(item),
                                'decorators': [self._get_decorator_name(dec) for dec in item.decorator_list],
                                'line_number': item.lineno
                            }
                            class_info['methods'].append(method_info)
                    self.classes[relative_path].append(class_info)
                
                elif isinstance(node, ast.FunctionDef):
                    # Only capture top-level functions
                    if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) if hasattr(parent, 'body') and node in parent.body):
                        self.functions[relative_path].append({
                            'name': node.name,
                            'args': [arg.arg for arg in node.args.args],
                            'docstring': ast.get_docstring(node),
                            'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list],
                            'line_number': node.lineno,
                            'returns': self._get_return_type(node) if node.returns else None
                        })
        
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_decorator_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return str(decorator)
    
    def _get_return_type(self, node: ast.FunctionDef) -> str:
        """Extract return type annotation."""
        if isinstance(node.returns, ast.Name):
            return node.returns.id
        elif isinstance(node.returns, ast.Attribute):
            return f"{self._get_decorator_name(node.returns.value)}.{node.returns.attr}"
        elif isinstance(node.returns, ast.Subscript):
            return str(node.returns)
        return str(node.returns) if node.returns else None
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """
        Calculate cyclomatic complexity of a Python file.
        
        Cyclomatic complexity = number of decision points + 1
        Decision points: if, for, while, except, and, or, comprehensions
        """
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1
        
        return complexity
    
    def _detect_code_duplication(self, content: str) -> List[str]:
        """
        Detect potential code duplication by finding repeated code blocks.
        
        Returns list of duplicated line ranges.
        """
        lines = content.split('\n')
        code_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        
        # Find repeated sequences of 3+ lines
        duplicates = []
        seen_blocks = {}
        
        for i in range(len(code_lines) - 2):
            block = '\n'.join(code_lines[i:i+3])
            if block in seen_blocks:
                duplicates.append(f"Lines {i+1}-{i+3} similar to lines {seen_blocks[block]+1}-{seen_blocks[block]+3}")
            else:
                seen_blocks[block] = i
        
        return duplicates[:5]  # Return top 5 duplicates
    
    def _get_results(self) -> Dict[str, Any]:
        """
        Compile and return analysis results.
        
        Returns:
            Dictionary containing all analysis results with proper types
        """
        return {
            'file_count': self.file_count,
            'folder_count': self.folder_count,
            'languages': list(self.languages),
            'structure': self.structure,
            'dependencies': dict(self.dependencies),
            'internal_dependencies': dict(self.internal_dependencies),
            'external_dependencies': dict(self.external_dependencies),
            'classes': self.classes,
            'functions': self.functions,
            'file_details': self.file_details,
            'lines_of_code': self.lines_of_code,
            'total_classes': sum(len(classes) for classes in self.classes.values()),
            'total_functions': sum(len(funcs) for funcs in self.functions.values()),
            'cyclomatic_complexity': self.cyclomatic_complexity,
            'code_duplication': self.code_duplication,
            'average_complexity': sum(self.cyclomatic_complexity.values()) / len(self.cyclomatic_complexity) if self.cyclomatic_complexity else 0
        }
