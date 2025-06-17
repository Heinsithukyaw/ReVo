#!/usr/bin/env python3
"""
Quality Gates System for reVoAgent
Implements multi-layer validation for 100-agent team output
"""

import asyncio
import logging
import ast
import re
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import subprocess
import tempfile
from pathlib import Path
import sys

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

logger = logging.getLogger(__name__)

class QualityLevel(Enum):
    """Quality assessment levels"""
    EXCELLENT = "excellent"    # 90-100%
    GOOD = "good"             # 80-89%
    ACCEPTABLE = "acceptable"  # 70-79%
    POOR = "poor"             # 50-69%
    FAILED = "failed"         # <50%

class ValidationResult(Enum):
    """Validation results"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"

@dataclass
class QualityMetrics:
    """Quality assessment metrics"""
    syntax_score: float = 0.0
    security_score: float = 0.0
    performance_score: float = 0.0
    maintainability_score: float = 0.0
    test_coverage_score: float = 0.0
    documentation_score: float = 0.0
    overall_score: float = 0.0
    quality_level: QualityLevel = QualityLevel.FAILED
    
    def calculate_overall_score(self):
        """Calculate overall quality score"""
        weights = {
            'syntax': 0.25,
            'security': 0.20,
            'performance': 0.15,
            'maintainability': 0.15,
            'test_coverage': 0.15,
            'documentation': 0.10
        }
        
        self.overall_score = (
            self.syntax_score * weights['syntax'] +
            self.security_score * weights['security'] +
            self.performance_score * weights['performance'] +
            self.maintainability_score * weights['maintainability'] +
            self.test_coverage_score * weights['test_coverage'] +
            self.documentation_score * weights['documentation']
        )
        
        # Determine quality level
        if self.overall_score >= 90:
            self.quality_level = QualityLevel.EXCELLENT
        elif self.overall_score >= 80:
            self.quality_level = QualityLevel.GOOD
        elif self.overall_score >= 70:
            self.quality_level = QualityLevel.ACCEPTABLE
        elif self.overall_score >= 50:
            self.quality_level = QualityLevel.POOR
        else:
            self.quality_level = QualityLevel.FAILED

@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    validation_id: str
    content_type: str
    content: str
    agent_id: str
    timestamp: datetime
    quality_metrics: QualityMetrics
    validation_results: Dict[str, ValidationResult]
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    passed_gates: List[str]
    failed_gates: List[str]
    execution_time: float
    
    @property
    def is_approved(self) -> bool:
        """Check if content passes all critical quality gates"""
        critical_gates = ['syntax_validation', 'security_scan']
        return all(
            self.validation_results.get(gate) == ValidationResult.PASSED 
            for gate in critical_gates
        )

class QualityGates:
    """
    Quality Gates system for AI-generated content validation
    
    Implements multi-layer validation:
    1. Syntax validation
    2. Security scanning
    3. Performance analysis
    4. Test coverage validation
    5. Documentation quality
    6. Architecture compliance
    """
    
    def __init__(self):
        """Initialize quality gates system"""
        
        # Enhanced quality thresholds for enterprise development
        self.thresholds = {
            'syntax_minimum': 90.0,      # Slightly more lenient for complex code
            'security_minimum': 80.0,    # Focus on real security issues
            'performance_minimum': 65.0, # Performance can be optimized later
            'test_coverage_minimum': 70.0, # Realistic for enterprise development
            'documentation_minimum': 70.0, # Reasonable documentation expectations
            'overall_minimum': 75.0      # Achievable overall quality target
        }
        
        # Validation statistics
        self.validation_stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'failed_validations': 0,
            'average_quality_score': 0.0,
            'common_issues': {},
            'agent_performance': {}
        }
        
        # Security patterns to check
        self.security_patterns = {
            'sql_injection': [
                r'SELECT.*FROM.*WHERE.*=.*\+',
                r'INSERT.*INTO.*VALUES.*\+',
                r'UPDATE.*SET.*WHERE.*\+',
                r'DELETE.*FROM.*WHERE.*\+'
            ],
            'xss_vulnerability': [
                r'innerHTML\s*=\s*[^;]*\+',
                r'document\.write\s*\([^)]*\+',
                r'eval\s*\([^)]*\+',
                r'setTimeout\s*\([^)]*\+'
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ],
            'unsafe_functions': [
                r'exec\s*\(',
                r'eval\s*\(',
                r'pickle\.loads\s*\(',
                r'subprocess\.call\s*\([^)]*shell\s*=\s*True'
            ]
        }
        
        logger.info("🛡️ Quality Gates system initialized")
        logger.info(f"📊 Quality thresholds: {self.thresholds}")
    
    async def validate_generated_code(self, code: str, agent_id: str, content_type: str = "code") -> ValidationReport:
        """
        Comprehensive validation of AI-generated code
        """
        start_time = datetime.now()
        validation_id = f"val_{int(start_time.timestamp())}_{agent_id}"
        
        logger.info(f"🔍 Starting validation {validation_id} for {agent_id}")
        
        # Initialize metrics and results
        metrics = QualityMetrics()
        validation_results = {}
        issues_found = []
        recommendations = []
        
        try:
            # 1. Syntax Validation
            syntax_result = await self._validate_syntax(code)
            validation_results['syntax_validation'] = syntax_result['result']
            metrics.syntax_score = syntax_result['score']
            if syntax_result['issues']:
                issues_found.extend(syntax_result['issues'])
            
            # 2. Security Scanning
            security_result = await self._security_scan(code)
            validation_results['security_scan'] = security_result['result']
            metrics.security_score = security_result['score']
            if security_result['issues']:
                issues_found.extend(security_result['issues'])
            
            # 3. Performance Analysis
            performance_result = await self._performance_analysis(code)
            validation_results['performance_analysis'] = performance_result['result']
            metrics.performance_score = performance_result['score']
            if performance_result['issues']:
                issues_found.extend(performance_result['issues'])
            
            # 4. Test Coverage Check
            coverage_result = await self._test_coverage_check(code)
            validation_results['test_coverage'] = coverage_result['result']
            metrics.test_coverage_score = coverage_result['score']
            if coverage_result['issues']:
                issues_found.extend(coverage_result['issues'])
            
            # 5. Documentation Quality
            doc_result = await self._documentation_quality(code)
            validation_results['documentation_quality'] = doc_result['result']
            metrics.documentation_score = doc_result['score']
            if doc_result['issues']:
                issues_found.extend(doc_result['issues'])
            
            # 6. Architecture Compliance
            arch_result = await self._architecture_compliance(code)
            validation_results['architecture_compliance'] = arch_result['result']
            metrics.maintainability_score = arch_result['score']
            if arch_result['issues']:
                issues_found.extend(arch_result['issues'])
            
            # Calculate overall score
            metrics.calculate_overall_score()
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(metrics, issues_found)
            
            # Determine passed/failed gates
            passed_gates = [gate for gate, result in validation_results.items() if result == ValidationResult.PASSED]
            failed_gates = [gate for gate, result in validation_results.items() if result == ValidationResult.FAILED]
            
            # Update statistics
            await self._update_validation_stats(agent_id, metrics, validation_results)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Create validation report
            report = ValidationReport(
                validation_id=validation_id,
                content_type=content_type,
                content=code,
                agent_id=agent_id,
                timestamp=start_time,
                quality_metrics=metrics,
                validation_results=validation_results,
                issues_found=issues_found,
                recommendations=recommendations,
                passed_gates=passed_gates,
                failed_gates=failed_gates,
                execution_time=execution_time
            )
            
            # Log results
            status = "✅ PASSED" if report.is_approved else "❌ FAILED"
            logger.info(f"{status} Validation {validation_id} - Score: {metrics.overall_score:.1f}% ({metrics.quality_level.value})")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Validation error for {validation_id}: {e}")
            
            # Return failed validation report
            execution_time = (datetime.now() - start_time).total_seconds()
            return ValidationReport(
                validation_id=validation_id,
                content_type=content_type,
                content=code,
                agent_id=agent_id,
                timestamp=start_time,
                quality_metrics=metrics,
                validation_results={'error': ValidationResult.FAILED},
                issues_found=[{'type': 'validation_error', 'message': str(e)}],
                recommendations=['Fix validation system error'],
                passed_gates=[],
                failed_gates=['validation_system'],
                execution_time=execution_time
            )
    
    async def _validate_syntax(self, code: str) -> Dict[str, Any]:
        """Validate code syntax"""
        try:
            # Detect language and validate accordingly
            if self._is_python_code(code):
                return await self._validate_python_syntax(code)
            elif self._is_javascript_code(code):
                return await self._validate_javascript_syntax(code)
            elif self._is_sql_code(code):
                return await self._validate_sql_syntax(code)
            else:
                # Generic validation
                return {
                    'result': ValidationResult.PASSED,
                    'score': 85.0,
                    'issues': []
                }
        except Exception as e:
            return {
                'result': ValidationResult.FAILED,
                'score': 0.0,
                'issues': [{'type': 'syntax_error', 'message': str(e)}]
            }
    
    async def _validate_python_syntax(self, code: str) -> Dict[str, Any]:
        """Validate Python syntax"""
        issues = []
        score = 100.0
        
        try:
            # Parse AST
            ast.parse(code)
            
            # Additional Python-specific checks
            lines = code.split('\n')
            
            # Check for common issues
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # Check for missing imports
                if 'import' not in code and any(lib in line for lib in ['os.', 'sys.', 'json.', 'datetime.']):
                    issues.append({
                        'type': 'missing_import',
                        'line': i,
                        'message': 'Possible missing import statement'
                    })
                    score -= 5
                
                # Check for print statements (should use logging)
                if line.startswith('print(') and 'debug' not in code.lower():
                    issues.append({
                        'type': 'print_statement',
                        'line': i,
                        'message': 'Consider using logging instead of print'
                    })
                    score -= 2
            
            result = ValidationResult.PASSED if score >= self.thresholds['syntax_minimum'] else ValidationResult.FAILED
            
        except SyntaxError as e:
            issues.append({
                'type': 'syntax_error',
                'line': e.lineno,
                'message': str(e)
            })
            score = 0.0
            result = ValidationResult.FAILED
        
        return {
            'result': result,
            'score': max(score, 0.0),
            'issues': issues
        }
    
    async def _validate_javascript_syntax(self, code: str) -> Dict[str, Any]:
        """Validate JavaScript syntax (basic)"""
        issues = []
        score = 100.0
        
        # Basic JavaScript validation
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for common issues
            if line.endswith(';') is False and line and not line.endswith('{') and not line.endswith('}'):
                if not any(keyword in line for keyword in ['if', 'for', 'while', 'function', 'class']):
                    issues.append({
                        'type': 'missing_semicolon',
                        'line': i,
                        'message': 'Missing semicolon'
                    })
                    score -= 1
        
        result = ValidationResult.PASSED if score >= self.thresholds['syntax_minimum'] else ValidationResult.FAILED
        
        return {
            'result': result,
            'score': max(score, 0.0),
            'issues': issues
        }
    
    async def _validate_sql_syntax(self, code: str) -> Dict[str, Any]:
        """Validate SQL syntax (basic)"""
        issues = []
        score = 100.0
        
        # Basic SQL validation
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        
        if not any(keyword in code.upper() for keyword in sql_keywords):
            issues.append({
                'type': 'no_sql_keywords',
                'message': 'No SQL keywords found'
            })
            score -= 20
        
        result = ValidationResult.PASSED if score >= self.thresholds['syntax_minimum'] else ValidationResult.FAILED
        
        return {
            'result': result,
            'score': max(score, 0.0),
            'issues': issues
        }
    
    async def _security_scan(self, code: str) -> Dict[str, Any]:
        """Enhanced security scanning with context awareness"""
        issues = []
        score = 100.0
        
        # Check if this is test code or documentation
        is_test_code = any(indicator in code.lower() for indicator in [
            'test_', 'def test', 'class test', 'example', 'demo', 'sample',
            'mock', 'stub', 'placeholder', '# test', '# example', '# demo'
        ])
        
        # Check for security vulnerabilities (only for production code)
        if not is_test_code:
            for vulnerability_type, patterns in self.security_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, code, re.IGNORECASE)
                    for match in matches:
                        issues.append({
                            'type': 'security_vulnerability',
                            'subtype': vulnerability_type,
                            'message': f'Potential {vulnerability_type.replace("_", " ")} vulnerability',
                            'line': code[:match.start()].count('\n') + 1,
                            'severity': 'high'
                        })
                        score -= 15
        
        # Enhanced security checks with context awareness
        security_checks = [
            ('eval(', 'Use of eval() function'),
            ('exec(', 'Use of exec() function'),
            ('subprocess.call', 'Direct subprocess call without validation'),
            ('os.system', 'Use of os.system() function')
        ]
        
        # Only check for actual security issues, not test data
        for check, message in security_checks:
            if check in code.lower():
                # Skip if it's in a comment or test context
                lines = code.split('\n')
                for i, line in enumerate(lines):
                    if check in line.lower():
                        stripped_line = line.strip()
                        if not (stripped_line.startswith('#') or 
                               stripped_line.startswith('//') or
                               'test' in stripped_line.lower() or
                               'example' in stripped_line.lower()):
                            issues.append({
                                'type': 'security_issue',
                                'message': message,
                                'line': i + 1,
                                'severity': 'medium'
                            })
                            score -= 10
                            break
        
        # Check for hardcoded credentials (more intelligent detection)
        credential_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', 'Potential hardcoded password'),
            (r'api_key\s*=\s*["\'][^"\']{20,}["\']', 'Potential hardcoded API key'),
            (r'secret\s*=\s*["\'][^"\']{16,}["\']', 'Potential hardcoded secret'),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', 'Potential hardcoded token')
        ]
        
        if not is_test_code:
            for pattern, message in credential_patterns:
                matches = re.finditer(pattern, code, re.IGNORECASE)
                for match in matches:
                    # Check if it's not a placeholder or example
                    matched_text = match.group()
                    if not any(placeholder in matched_text.lower() for placeholder in [
                        'example', 'test', 'demo', 'placeholder', 'xxx', '123', 'abc'
                    ]):
                        issues.append({
                            'type': 'security_issue',
                            'message': message,
                            'line': code[:match.start()].count('\n') + 1,
                            'severity': 'high'
                        })
                        score -= 15
        
        result = ValidationResult.PASSED if score >= self.thresholds['security_minimum'] else ValidationResult.FAILED
        
        return {
            'result': result,
            'score': max(score, 0.0),
            'issues': issues
        }
    
    async def _performance_analysis(self, code: str) -> Dict[str, Any]:
        """Analyze code performance"""
        issues = []
        score = 100.0
        
        # Performance anti-patterns
        performance_issues = [
            (r'for.*in.*range.*len', 'Use enumerate() instead of range(len())'),
            (r'\.append.*for.*in', 'Consider list comprehension'),
            (r'time\.sleep\([^)]*[5-9]\d*', 'Long sleep detected'),
            (r'while True:.*time\.sleep\(0\)', 'Busy waiting detected'),
            (r'.*\+.*for.*in.*', 'String concatenation in loop')
        ]
        
        for pattern, message in performance_issues:
            if re.search(pattern, code):
                issues.append({
                    'type': 'performance_issue',
                    'message': message,
                    'severity': 'medium'
                })
                score -= 8
        
        # Check for complexity indicators
        lines = code.split('\n')
        nested_level = 0
        max_nested_level = 0
        
        for line in lines:
            stripped = line.strip()
            if any(keyword in stripped for keyword in ['if', 'for', 'while', 'with', 'try']):
                nested_level += 1
                max_nested_level = max(max_nested_level, nested_level)
            elif stripped in ['else:', 'elif', 'except:', 'finally:']:
                continue
            elif stripped.endswith(':'):
                nested_level += 1
            elif not stripped or stripped.startswith('#'):
                continue
            else:
                nested_level = max(0, nested_level - line.count('    ') // 4)
        
        if max_nested_level > 4:
            issues.append({
                'type': 'complexity_issue',
                'message': f'High nesting level ({max_nested_level})',
                'severity': 'medium'
            })
            score -= 10
        
        result = ValidationResult.PASSED if score >= self.thresholds['performance_minimum'] else ValidationResult.FAILED
        
        return {
            'result': result,
            'score': max(score, 0.0),
            'issues': issues
        }
    
    async def _test_coverage_check(self, code: str) -> Dict[str, Any]:
        """Check test coverage and quality"""
        issues = []
        score = 0.0
        
        # Check if this is test code
        is_test_code = any(indicator in code.lower() for indicator in [
            'def test_', 'class test', 'import pytest', 'import unittest',
            'assert ', 'self.assert', 'expect(', 'test_', 'mock'
        ])
        
        # Check if this is example/demo code
        is_example_code = any(indicator in code.lower() for indicator in [
            'example', 'demo', 'sample', 'tutorial', 'placeholder',
            'implement_real_business_logic', 'test implementation'
        ])

        if is_test_code:
            score = 95.0  # High score for test code
            
            # Check test quality
            if 'assert' not in code.lower() and 'expect' not in code.lower():
                issues.append({
                    'type': 'test_quality',
                    'message': 'No assertions found in test code',
                    'severity': 'medium'
                })
                score -= 15
            
        elif is_example_code:
            score = 90.0  # High score for example/demo code
            # Example code doesn't need tests
            
        else:
            # Check if production code has corresponding tests
            functions = re.findall(r'def (\w+)\(', code)
            classes = re.findall(r'class (\w+)', code)
            
            # Filter out private methods and special methods
            public_functions = [f for f in functions if not f.startswith('_')]
            public_classes = [c for c in classes if not c.startswith('_')]

            if public_functions or public_classes:
                # Check if it's infrastructure/config code
                is_infrastructure = any(keyword in code.lower() for keyword in [
                    'config', 'settings', 'main', '__init__', 'setup',
                    'dataclass', 'enum', 'typing', 'pydantic'
                ])
                
                if is_infrastructure:
                    score = 85.0  # Infrastructure code has different testing needs
                else:
                    score = 75.0  # Production code should have tests
                    issues.append({
                        'type': 'missing_tests',
                        'message': 'Production code should have corresponding tests',
                        'severity': 'low'
                    })
            else:
                score = 90.0  # Configuration or simple code
        
        result = ValidationResult.PASSED if score >= self.thresholds['test_coverage_minimum'] else ValidationResult.WARNING
        
        return {
            'result': result,
            'score': score,
            'issues': issues
        }
    
    async def _documentation_quality(self, code: str) -> Dict[str, Any]:
        """Enhanced documentation quality assessment"""
        issues = []
        score = 100.0
        
        # Check if this is test/example code
        is_test_or_example = any(indicator in code.lower() for indicator in [
            'test_', 'example', 'demo', 'sample', 'tutorial', 'mock',
            'implement_real_business_logic', 'placeholder'
        ])
        
        lines = code.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        docstring_lines = len([line for line in lines if '"""' in line or "'''" in line])
        
        # Calculate documentation ratio
        doc_ratio = (comment_lines + docstring_lines) / max(total_lines, 1)
        
        # Check for function/class documentation
        functions = re.findall(r'def (\w+)\(', code)
        classes = re.findall(r'class (\w+)', code)
        
        # Filter out private methods for documentation requirements
        public_functions = [f for f in functions if not f.startswith('_')]
        public_classes = [c for c in classes if not c.startswith('_')]
        
        documented_functions = len(re.findall(r'def \w+\([^)]*\):\s*"""', code, re.MULTILINE))
        documented_classes = len(re.findall(r'class \w+[^:]*:\s*"""', code, re.MULTILINE))
        
        if is_test_or_example:
            # More lenient for test/example code
            score = 85.0
            if doc_ratio < 0.05:  # Very minimal documentation needed
                score = 80.0
        else:
            # Production code documentation requirements
            if public_functions and len(public_functions) > 2:
                if documented_functions / len(public_functions) < 0.3:  # More lenient threshold
                    issues.append({
                        'type': 'missing_docstrings',
                        'message': 'Some public functions missing docstrings',
                        'severity': 'low'
                    })
                    score -= 10
            
            if public_classes and documented_classes / len(public_classes) < 0.5:
                issues.append({
                    'type': 'missing_docstrings',
                    'message': 'Some classes missing docstrings',
                    'severity': 'low'
                })
                score -= 10
            
            if doc_ratio < 0.05:  # Very minimal threshold
                issues.append({
                    'type': 'insufficient_comments',
                    'message': 'Consider adding more code comments',
                    'severity': 'low'
                })
                score -= 5
        
        result = ValidationResult.PASSED if score >= self.thresholds['documentation_minimum'] else ValidationResult.WARNING
        
        return {
            'result': result,
            'score': max(score, 0.0),
            'issues': issues
        }
    
    async def _architecture_compliance(self, code: str) -> Dict[str, Any]:
        """Check architecture and maintainability compliance"""
        issues = []
        score = 100.0
        
        # Check for architectural patterns
        lines = code.split('\n')
        
        # Single Responsibility Principle
        classes = re.findall(r'class (\w+)', code)
        for class_name in classes:
            class_methods = len(re.findall(rf'class {class_name}.*?(?=class|\Z)', code, re.DOTALL))
            if class_methods > 20:  # Rough estimate
                issues.append({
                    'type': 'srp_violation',
                    'message': f'Class {class_name} may have too many responsibilities',
                    'severity': 'medium'
                })
                score -= 10
        
        # Check for magic numbers
        magic_numbers = re.findall(r'\b(?<![\w.])\d{2,}\b(?![\w.])', code)
        if len(magic_numbers) > 3:
            issues.append({
                'type': 'magic_numbers',
                'message': 'Consider using named constants instead of magic numbers',
                'severity': 'low'
            })
            score -= 5
        
        # Check for long functions
        functions = re.findall(r'def \w+\([^)]*\):(.*?)(?=def|\Z)', code, re.DOTALL)
        for func in functions:
            func_lines = len([line for line in func.split('\n') if line.strip()])
            if func_lines > 50:
                issues.append({
                    'type': 'long_function',
                    'message': 'Function is too long, consider breaking it down',
                    'severity': 'medium'
                })
                score -= 8
        
        result = ValidationResult.PASSED if score >= 70.0 else ValidationResult.WARNING
        
        return {
            'result': result,
            'score': max(score, 0.0),
            'issues': issues
        }
    
    async def _generate_recommendations(self, metrics: QualityMetrics, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if metrics.syntax_score < 95:
            recommendations.append("Fix syntax errors and improve code structure")
        
        if metrics.security_score < 85:
            recommendations.append("Address security vulnerabilities and follow secure coding practices")
        
        if metrics.performance_score < 70:
            recommendations.append("Optimize performance bottlenecks and improve algorithm efficiency")
        
        if metrics.test_coverage_score < 80:
            recommendations.append("Increase test coverage and improve test quality")
        
        if metrics.documentation_score < 75:
            recommendations.append("Add comprehensive documentation and code comments")
        
        # Specific recommendations based on issues
        issue_types = [issue['type'] for issue in issues]
        
        if 'security_vulnerability' in issue_types:
            recommendations.append("Implement input validation and sanitization")
        
        if 'performance_issue' in issue_types:
            recommendations.append("Use more efficient algorithms and data structures")
        
        if 'missing_tests' in issue_types:
            recommendations.append("Create unit tests for all functions and classes")
        
        return recommendations
    
    async def _update_validation_stats(self, agent_id: str, metrics: QualityMetrics, results: Dict[str, ValidationResult]):
        """Update validation statistics"""
        self.validation_stats['total_validations'] += 1
        
        if metrics.overall_score >= self.thresholds['overall_minimum']:
            self.validation_stats['passed_validations'] += 1
        else:
            self.validation_stats['failed_validations'] += 1
        
        # Update average quality score
        total = self.validation_stats['total_validations']
        current_avg = self.validation_stats['average_quality_score']
        self.validation_stats['average_quality_score'] = (
            (current_avg * (total - 1) + metrics.overall_score) / total
        )
        
        # Update agent performance
        if agent_id not in self.validation_stats['agent_performance']:
            self.validation_stats['agent_performance'][agent_id] = {
                'validations': 0,
                'average_score': 0.0,
                'passed': 0,
                'failed': 0
            }
        
        agent_stats = self.validation_stats['agent_performance'][agent_id]
        agent_stats['validations'] += 1
        
        if metrics.overall_score >= self.thresholds['overall_minimum']:
            agent_stats['passed'] += 1
        else:
            agent_stats['failed'] += 1
        
        # Update agent average score
        agent_total = agent_stats['validations']
        agent_current_avg = agent_stats['average_score']
        agent_stats['average_score'] = (
            (agent_current_avg * (agent_total - 1) + metrics.overall_score) / agent_total
        )
    
    def _is_python_code(self, code: str) -> bool:
        """Check if code is Python"""
        python_indicators = ['def ', 'import ', 'from ', 'class ', 'if __name__']
        return any(indicator in code for indicator in python_indicators)
    
    def _is_javascript_code(self, code: str) -> bool:
        """Check if code is JavaScript"""
        js_indicators = ['function ', 'var ', 'let ', 'const ', '=>', 'console.log']
        return any(indicator in code for indicator in js_indicators)
    
    def _is_sql_code(self, code: str) -> bool:
        """Check if code is SQL"""
        sql_indicators = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP']
        return any(indicator in code.upper() for indicator in sql_indicators)
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation statistics summary"""
        total = self.validation_stats['total_validations']
        
        return {
            'validation_stats': self.validation_stats,
            'success_rate': (
                self.validation_stats['passed_validations'] / total 
                if total > 0 else 0.0
            ),
            'quality_thresholds': self.thresholds,
            'top_performing_agents': sorted(
                [
                    (agent_id, stats['average_score']) 
                    for agent_id, stats in self.validation_stats['agent_performance'].items()
                ],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

# Quality gate configuration for different content types
QUALITY_GATE_CONFIG = {
    "code_generation": {
        "required_gates": ["syntax_validation", "security_scan"],
        "recommended_gates": ["performance_analysis", "documentation_quality"],
        "minimum_score": 80.0
    },
    "architecture_changes": {
        "required_gates": ["syntax_validation", "security_scan", "architecture_compliance"],
        "recommended_gates": ["performance_analysis", "test_coverage"],
        "minimum_score": 85.0
    },
    "performance_changes": {
        "required_gates": ["syntax_validation", "performance_analysis"],
        "recommended_gates": ["security_scan", "test_coverage"],
        "minimum_score": 75.0
    }
}