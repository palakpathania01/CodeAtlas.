"""
Security Analyzer using Machine Learning Patterns

This module uses pattern recognition and ML-inspired techniques to detect
security vulnerabilities and security anti-patterns in Python code.
"""

import ast
import re
from typing import Dict, List, Any, Set
import logging

logger = logging.getLogger(__name__)


class SecurityAnalyzer:
    """
    ML-inspired security analyzer that identifies security vulnerabilities
    and anti-patterns using pattern recognition and heuristic analysis.
    """
    
    def __init__(self):
        """Initialize the security analyzer."""
        self.security_patterns = {
            'sql_injection': [],
            'hardcoded_secrets': [],
            'weak_cryptography': [],
            'insecure_deserialization': [],
            'command_injection': [],
            'path_traversal': [],
            'weak_random': [],
            'insecure_tls': []
        }
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a single Python file for security vulnerabilities.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Dictionary containing detected security issues and severity levels
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Reset security patterns
            self._reset_patterns()
            
            # Detect various security patterns
            self._detect_sql_injection(tree, content)
            self._detect_hardcoded_secrets(content)
            self._detect_weak_cryptography(tree)
            self._detect_insecure_deserialization(tree)
            self._detect_command_injection(tree)
            self._detect_path_traversal(tree)
            self._detect_weak_random(tree)
            self._detect_insecure_tls(tree)
            
            # Calculate overall security score
            total_issues = sum(len(issues) for issues in self.security_patterns.values())
            severity = self._calculate_severity(total_issues)
            security_score = self._calculate_security_score(total_issues)
            
            return {
                'total_issues': total_issues,
                'severity': severity,
                'security_score': security_score,
                'security_patterns': self.security_patterns,
                'recommendations': self._generate_security_recommendations()
            }
        
        except Exception as e:
            logger.error(f"Error analyzing security for {file_path}: {str(e)}")
            return {
                'total_issues': 0,
                'severity': 'Unknown',
                'security_score': 0,
                'security_patterns': {},
                'recommendations': ['Error analyzing file for security']
            }
    
    def _reset_patterns(self) -> None:
        """Reset security pattern storage."""
        self.security_patterns = {
            'sql_injection': [],
            'hardcoded_secrets': [],
            'weak_cryptography': [],
            'insecure_deserialization': [],
            'command_injection': [],
            'path_traversal': [],
            'weak_random': [],
            'insecure_tls': []
        }
    
    def _detect_sql_injection(self, tree: ast.AST, content: str) -> None:
        """Detect potential SQL injection vulnerabilities."""
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Str):
                if any(keyword in node.s.upper() for keyword in sql_keywords):
                    # Check if string contains user input
                    if '%' in node.s or '{}' in node.s:
                        self.security_patterns['sql_injection'].append(
                            f"Potential SQL injection: string formatting in SQL query"
                        )
    
    def _detect_hardcoded_secrets(self, content: str) -> None:
        """Detect hardcoded secrets and credentials."""
        # Common secret patterns
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']{8,}["\']',
            r'api_key\s*=\s*["\'][^"\']{20,}["\']',
            r'secret_key\s*=\s*["\'][^"\']{20,}["\']',
            r'token\s*=\s*["\'][^"\']{20,}["\']',
            r'aws_access_key\s*=\s*["\'][A-Z0-9]{20}["\']',
            r'aws_secret_key\s*=\s*["\'][A-Za-z0-9/+=]{40}["\']'
        ]
        
        for pattern in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                self.security_patterns['hardcoded_secrets'].append(
                    f"Hardcoded secret detected at line {content[:match.start()].count(chr(10)) + 1}"
                )
    
    def _detect_weak_cryptography(self, tree: ast.AST) -> None:
        """Detect weak cryptographic algorithms."""
        weak_algorithms = ['md5', 'sha1', 'des', 'rc4']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if node.attr.lower() in weak_algorithms:
                    self.security_patterns['weak_cryptography'].append(
                        f"Weak cryptographic algorithm: {node.attr}"
                    )
            
            elif isinstance(node, ast.Name):
                if node.id.lower() in weak_algorithms:
                    self.security_patterns['weak_cryptography'].append(
                        f"Weak cryptographic algorithm: {node.id}"
                    )
    
    def _detect_insecure_deserialization(self, tree: ast.AST) -> None:
        """Detect insecure deserialization patterns."""
        dangerous_functions = ['pickle', 'eval', 'exec']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['loads', 'load']:
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id in dangerous_functions:
                                self.security_patterns['insecure_deserialization'].append(
                                    f"Insecure deserialization: {node.func.value.id}.{node.func.attr}"
                                )
    
    def _detect_command_injection(self, tree: ast.AST) -> None:
        """Detect potential command injection vulnerabilities."""
        dangerous_functions = ['os.system', 'subprocess.call', 'subprocess.Popen']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['system', 'call', 'Popen']:
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id in ['os', 'subprocess']:
                                self.security_patterns['command_injection'].append(
                                    f"Potential command injection: {node.func.value.id}.{node.func.attr}"
                                )
    
    def _detect_path_traversal(self, tree: ast.AST) -> None:
        """Detect potential path traversal vulnerabilities."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['open', 'read', 'write']:
                        # Check if using user input without validation
                        if node.args:
                            self.security_patterns['path_traversal'].append(
                                "Potential path traversal: file operation with user input"
                            )
    
    def _detect_weak_random(self, tree: ast.AST) -> None:
        """Detect weak random number generation."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'random':
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id == 'random':
                                self.security_patterns['weak_random'].append(
                                    "Weak random number generation: use secrets module instead"
                                )
    
    def _detect_insecure_tls(self, tree: ast.AST) -> None:
        """Detect insecure TLS/SSL configurations."""
        insecure_configs = ['verify=False', 'ssl_version=ssl.PROTOCOL_TLSv1']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Str):
                if any(config in node.s for config in insecure_configs):
                    self.security_patterns['insecure_tls'].append(
                        "Insecure TLS/SSL configuration detected"
                    )
    
    def _calculate_severity(self, total_issues: int) -> str:
        """Calculate severity level based on issue count."""
        if total_issues == 0:
            return "None"
        elif total_issues <= 2:
            return "Low"
        elif total_issues <= 5:
            return "Medium"
        else:
            return "High"
    
    def _calculate_security_score(self, total_issues: int) -> float:
        """Calculate overall security score."""
        # Start with 100 and deduct points for each issue
        score = 100 - (total_issues * 10)
        return max(0, min(100, score))
    
    def _generate_security_recommendations(self) -> List[str]:
        """Generate recommendations for fixing security issues."""
        recommendations = []
        
        if self.security_patterns['sql_injection']:
            recommendations.append("Use parameterized queries to prevent SQL injection")
        
        if self.security_patterns['hardcoded_secrets']:
            recommendations.append("Move secrets to environment variables or secure vault")
        
        if self.security_patterns['weak_cryptography']:
            recommendations.append("Use strong cryptographic algorithms (SHA-256, AES)")
        
        if self.security_patterns['insecure_deserialization']:
            recommendations.append("Avoid using pickle for untrusted data; use JSON instead")
        
        if self.security_patterns['command_injection']:
            recommendations.append("Validate and sanitize user input before command execution")
        
        if self.security_patterns['path_traversal']:
            recommendations.append("Validate and sanitize file paths to prevent path traversal")
        
        if self.security_patterns['weak_random']:
            recommendations.append("Use secrets module for cryptographic random numbers")
        
        if self.security_patterns['insecure_tls']:
            recommendations.append("Use secure TLS configurations with proper certificate verification")
        
        return recommendations
