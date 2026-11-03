"""
Bug Detector using Machine Learning Patterns

This module uses pattern recognition and ML-inspired techniques to detect
common bugs and anti-patterns in Python code.
"""

import ast
import re
from typing import Dict, List, Any, Set
import logging

logger = logging.getLogger(__name__)


class BugDetector:
    """
    ML-inspired bug detector that identifies common bugs and anti-patterns
    using pattern recognition and heuristic analysis.
    """
    
    def __init__(self):
        """Initialize the bug detector."""
        self.bug_patterns = {
            'unused_imports': [],
            'unused_variables': [],
            'potential_none_errors': [],
            'infinite_loops': [],
            'resource_leaks': [],
            'string_concatenation': [],
            'mutable_defaults': [],
            'comparison_chains': []
        }
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a single Python file for bugs and anti-patterns.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Dictionary containing detected bugs and severity levels
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Reset bug patterns
            self._reset_patterns()
            
            # Detect various bug patterns
            self._detect_unused_imports(tree, content)
            self._detect_unused_variables(tree)
            self._detect_potential_none_errors(tree)
            self._detect_infinite_loops(tree)
            self._detect_resource_leaks(tree)
            self._detect_string_concatenation(tree)
            self._detect_mutable_defaults(tree)
            self._detect_comparison_chains(tree)
            
            # Calculate overall bug score
            total_bugs = sum(len(bugs) for bugs in self.bug_patterns.values())
            severity = self._calculate_severity(total_bugs)
            
            return {
                'total_bugs': total_bugs,
                'severity': severity,
                'bug_patterns': self.bug_patterns,
                'recommendations': self._generate_bug_recommendations()
            }
        
        except Exception as e:
            logger.error(f"Error detecting bugs in {file_path}: {str(e)}")
            return {
                'total_bugs': 0,
                'severity': 'Unknown',
                'bug_patterns': {},
                'recommendations': ['Error analyzing file for bugs']
            }
    
    def _reset_patterns(self) -> None:
        """Reset bug pattern storage."""
        self.bug_patterns = {
            'unused_imports': [],
            'unused_variables': [],
            'potential_none_errors': [],
            'infinite_loops': [],
            'resource_leaks': [],
            'string_concatenation': [],
            'mutable_defaults': [],
            'comparison_chains': []
        }
    
    def _detect_unused_imports(self, tree: ast.AST, content: str) -> None:
        """Detect unused imports."""
        imported_names = set()
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
        
        unused = imported_names - used_names
        for name in unused:
            self.bug_patterns['unused_imports'].append(f"Unused import: {name}")
    
    def _detect_unused_variables(self, tree: ast.AST) -> None:
        """Detect unused variables."""
        defined_vars = set()
        used_vars = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_vars.add(target.id)
            elif isinstance(node, ast.Name):
                used_vars.add(node.id)
        
        unused = defined_vars - used_vars
        for var in unused:
            self.bug_patterns['unused_variables'].append(f"Unused variable: {var}")
    
    def _detect_potential_none_errors(self, tree: ast.AST) -> None:
        """Detect potential None reference errors."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                # Check if we're accessing an attribute without checking for None
                if isinstance(node.value, ast.Name):
                    self.bug_patterns['potential_none_errors'].append(
                        f"Potential None error: {node.value.id}.{node.attr} without None check"
                    )
    
    def _detect_infinite_loops(self, tree: ast.AST) -> None:
        """Detect potential infinite loops."""
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                if node.test is None or isinstance(node.test, ast.Constant) and node.test.value is True:
                    self.bug_patterns['infinite_loops'].append(
                        "Potential infinite loop: while True without break"
                    )
    
    def _detect_resource_leaks(self, tree: ast.AST) -> None:
        """Detect potential resource leaks (file handles, etc.)."""
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                continue  # Properly handled with context manager
            
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['open', 'file']:
                        # Check if not in a with statement
                        parent = getattr(node, 'parent', None)
                        if not isinstance(parent, ast.With):
                            self.bug_patterns['resource_leaks'].append(
                                f"Potential resource leak: {node.func.id}() without context manager"
                            )
    
    def _detect_string_concatenation(self, tree: ast.AST) -> None:
        """Detect inefficient string concatenation in loops."""
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Add):
                        if isinstance(child.left, ast.Str) or isinstance(child.right, ast.Str):
                            self.bug_patterns['string_concatenation'].append(
                                "Inefficient string concatenation in loop - use list join"
                            )
                            break
    
    def _detect_mutable_defaults(self, tree: ast.AST) -> None:
        """Detect mutable default arguments."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        self.bug_patterns['mutable_defaults'].append(
                            f"Mutable default argument in function: {node.name}"
                        )
    
    def _detect_comparison_chains(self, tree: ast.AST) -> None:
        """Detect incorrect comparison chains."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                if len(node.ops) > 1:
                    # Check for incorrect comparison like a < b > c
                    for i in range(len(node.ops) - 1):
                        if type(node.ops[i]) != type(node.ops[i + 1]):
                            self.bug_patterns['comparison_chains'].append(
                                "Incorrect comparison chain detected"
                            )
                            break
    
    def _calculate_severity(self, total_bugs: int) -> str:
        """Calculate severity level based on bug count."""
        if total_bugs == 0:
            return "None"
        elif total_bugs <= 3:
            return "Low"
        elif total_bugs <= 7:
            return "Medium"
        else:
            return "High"
    
    def _generate_bug_recommendations(self) -> List[str]:
        """Generate recommendations for fixing detected bugs."""
        recommendations = []
        
        if self.bug_patterns['unused_imports']:
            recommendations.append("Remove unused imports to clean up code")
        
        if self.bug_patterns['unused_variables']:
            recommendations.append("Remove or use unused variables")
        
        if self.bug_patterns['potential_none_errors']:
            recommendations.append("Add None checks before accessing attributes")
        
        if self.bug_patterns['infinite_loops']:
            recommendations.append("Review loop conditions and add break statements")
        
        if self.bug_patterns['resource_leaks']:
            recommendations.append("Use context managers (with statements) for resource handling")
        
        if self.bug_patterns['string_concatenation']:
            recommendations.append("Use list.join() for string concatenation in loops")
        
        if self.bug_patterns['mutable_defaults']:
            recommendations.append("Use None as default and initialize mutable objects in function body")
        
        if self.bug_patterns['comparison_chains']:
            recommendations.append("Review and fix comparison chains for correctness")
        
        return recommendations
