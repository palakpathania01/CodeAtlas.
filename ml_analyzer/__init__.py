"""
ML Code Analyzer Module

This module provides machine learning-based code analysis capabilities
for the CodeAtlas platform, including code quality prediction, bug detection,
and security vulnerability analysis.
"""

from .code_quality_analyzer import CodeQualityAnalyzer
from .bug_detector import BugDetector
from .security_analyzer import SecurityAnalyzer

__all__ = ['CodeQualityAnalyzer', 'BugDetector', 'SecurityAnalyzer']
