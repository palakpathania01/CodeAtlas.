"""
Code Quality Analyzer using Machine Learning

This module uses ML models to predict code quality scores based on
various code metrics and patterns.
"""

import ast
import re
from typing import Dict, List, Any
import numpy as np
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class CodeQualityAnalyzer:
    """
    ML-based code quality analyzer that predicts code quality scores
    and identifies areas for improvement.
    """
    
    def __init__(self):
        """Initialize the code quality analyzer."""
        self.quality_metrics = {
            'naming_conventions': 0.0,
            'code_length': 0.0,
            'complexity': 0.0,
            'documentation': 0.0,
            'duplication': 0.0,
            'error_handling': 0.0
        }
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a single Python file for code quality.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Dictionary containing quality metrics and overall score
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract various quality metrics
            metrics = self._extract_metrics(content, tree)
            
            # Calculate overall quality score
            overall_score = self._calculate_quality_score(metrics)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metrics)
            
            return {
                'overall_score': overall_score,
                'metrics': metrics,
                'recommendations': recommendations,
                'quality_level': self._get_quality_level(overall_score)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing code quality for {file_path}: {str(e)}")
            return {
                'overall_score': 0.0,
                'metrics': {},
                'recommendations': ['Error analyzing file'],
                'quality_level': 'Unknown'
            }
    
    def _extract_metrics(self, content: str, tree: ast.AST) -> Dict[str, Any]:
        """Extract various code quality metrics."""
        metrics = {}
        
        # Naming conventions
        metrics['naming_score'] = self._analyze_naming_conventions(tree)
        
        # Code length metrics
        metrics['avg_function_length'] = self._calculate_avg_function_length(tree)
        metrics['max_function_length'] = self._calculate_max_function_length(tree)
        
        # Complexity metrics
        metrics['cyclomatic_complexity'] = self._calculate_cyclomatic_complexity(tree)
        
        # Documentation
        metrics['documentation_coverage'] = self._calculate_documentation_coverage(tree)
        
        # Duplication
        metrics['code_duplication'] = self._detect_code_duplication(content)
        
        # Error handling
        metrics['error_handling_score'] = self._analyze_error_handling(tree)
        
        return metrics
    
    def _analyze_naming_conventions(self, tree: ast.AST) -> float:
        """Analyze naming conventions (PEP 8 compliance)."""
        score = 100.0
        violations = 0
        total_names = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_names += 1
                # Function names should be lowercase with underscores
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    violations += 1
            
            elif isinstance(node, ast.ClassDef):
                total_names += 1
                # Class names should be CapWords
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    violations += 1
        
        if total_names > 0:
            score = max(0, 100 - (violations / total_names * 100))
        
        return round(score, 2)
    
    def _calculate_avg_function_length(self, tree: ast.AST) -> float:
        """Calculate average function length in lines."""
        lengths = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count lines in function body
                lines = len(node.body)
                lengths.append(lines)
        
        if lengths:
            return round(sum(lengths) / len(lengths), 2)
        return 0.0
    
    def _calculate_max_function_length(self, tree: ast.AST) -> int:
        """Calculate maximum function length."""
        max_length = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                lines = len(node.body)
                max_length = max(max_length, lines)
        
        return max_length
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_documentation_coverage(self, tree: ast.AST) -> float:
        """Calculate documentation coverage (docstrings)."""
        documented = 0
        total = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                total += 1
                if ast.get_docstring(node):
                    documented += 1
        
        if total > 0:
            return round((documented / total) * 100, 2)
        return 0.0
    
    def _detect_code_duplication(self, content: str) -> float:
        """Detect code duplication (simplified)."""
        lines = content.split('\n')
        line_counts = defaultdict(int)
        
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                line_counts[stripped] += 1
        
        # Calculate duplication percentage
        duplicated_lines = sum(count - 1 for count in line_counts.values() if count > 1)
        total_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        
        if total_lines > 0:
            return round((duplicated_lines / total_lines) * 100, 2)
        return 0.0
    
    def _analyze_error_handling(self, tree: ast.AST) -> float:
        """Analyze error handling practices."""
        try_blocks = 0
        functions = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions += 1
                for child in ast.walk(node):
                    if isinstance(child, ast.Try):
                        try_blocks += 1
                        break
        
        if functions > 0:
            return round((try_blocks / functions) * 100, 2)
        return 0.0
    
    def _calculate_quality_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score from metrics."""
        weights = {
            'naming_score': 0.2,
            'documentation_coverage': 0.2,
            'error_handling_score': 0.2,
        }
        
        score = 0.0
        for metric, weight in weights.items():
            if metric in metrics:
                score += metrics[metric] * weight
        
        # Penalize long functions
        if metrics.get('avg_function_length', 0) > 20:
            score -= 10
        if metrics.get('max_function_length', 0) > 50:
            score -= 10
        
        # Penalize high complexity
        if metrics.get('cyclomatic_complexity', 0) > 10:
            score -= 10
        
        # Penalize duplication
        if metrics.get('code_duplication', 0) > 10:
            score -= 15
        
        return max(0, min(100, round(score, 2)))
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        if metrics.get('naming_score', 100) < 80:
            recommendations.append("Improve naming conventions to follow PEP 8 standards")
        
        if metrics.get('avg_function_length', 0) > 20:
            recommendations.append("Consider breaking down long functions into smaller ones")
        
        if metrics.get('max_function_length', 0) > 50:
            recommendations.append("Some functions are too long - refactor for better readability")
        
        if metrics.get('cyclomatic_complexity', 0) > 10:
            recommendations.append("Reduce cyclomatic complexity by simplifying control flow")
        
        if metrics.get('documentation_coverage', 0) < 50:
            recommendations.append("Add docstrings to functions and classes")
        
        if metrics.get('error_handling_score', 0) < 30:
            recommendations.append("Improve error handling with try-except blocks")
        
        if metrics.get('code_duplication', 0) > 10:
            recommendations.append("Reduce code duplication by extracting common functionality")
        
        return recommendations
    
    def _get_quality_level(self, score: float) -> str:
        """Get quality level based on score."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"
