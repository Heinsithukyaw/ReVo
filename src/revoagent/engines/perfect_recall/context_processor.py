"""
🧠 Perfect Recall Context Processor

Intelligent context extraction and processing for the Perfect Recall Engine.
Implements advanced context understanding from the implementation guide.
"""

import ast
import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class CodeContext:
    """Structured code context information"""
    file_path: str
    functions: List[str]
    classes: List[str]
    imports: List[str]
    variables: List[str]
    complexity_score: float
    dependencies: List[str]

@dataclass
class ConversationContext:
    """Structured conversation context"""
    topic: str
    intent: str  # 'question', 'request', 'error', 'feedback'
    entities: List[str]
    sentiment: float
    follow_up_needed: bool

class ContextProcessor:
    """Intelligent context extraction and processing"""
    
    def __init__(self):
        self.code_patterns = {
            'function_def': re.compile(r'def\s+(\w+)\s*\('),
            'class_def': re.compile(r'class\s+(\w+)'),
            'import_stmt': re.compile(r'(?:from\s+(\S+)\s+)?import\s+(.+)'),
            'variable_assign': re.compile(r'(\w+)\s*='),
        }
    
    async def process_code_context(self, code: str, file_path: str = "") -> CodeContext:
        """Extract structured context from code"""
        functions = []
        classes = []
        imports = []
        variables = []
        dependencies = []
        
        try:
            # Parse AST for comprehensive analysis
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                        dependencies.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(f"from {node.module}")
                        dependencies.append(node.module.split('.')[0])
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append(target.id)
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity(tree)
            
        except SyntaxError:
            # Fallback to regex parsing
            functions = self.code_patterns['function_def'].findall(code)
            classes = self.code_patterns['class_def'].findall(code)
            import_matches = self.code_patterns['import_stmt'].findall(code)
            imports = [f"{match[0]}.{match[1]}" if match[0] else match[1] 
                      for match in import_matches]
            variables = self.code_patterns['variable_assign'].findall(code)
            complexity_score = len(code.split('\n')) * 0.1
        
        return CodeContext(
            file_path=file_path,
            functions=list(set(functions)),
            classes=list(set(classes)),
            imports=list(set(imports)),
            variables=list(set(variables)),
            complexity_score=complexity_score,
            dependencies=list(set(dependencies))
        )
    
    async def process_conversation_context(self, text: str) -> ConversationContext:
        """Extract context from conversation"""
        # Intent detection
        intent = self._detect_intent(text)
        
        # Topic extraction
        topic = self._extract_topic(text)
        
        # Entity extraction
        entities = self._extract_entities(text)
        
        # Sentiment analysis (simple rule-based)
        sentiment = self._analyze_sentiment(text)
        
        # Follow-up detection
        follow_up_needed = self._needs_follow_up(text, intent)
        
        return ConversationContext(
            topic=topic,
            intent=intent,
            entities=entities,
            sentiment=sentiment,
            follow_up_needed=follow_up_needed
        )
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate code complexity score"""
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, ast.FunctionDef):
                complexity += len(node.args.args) * 0.5
            elif isinstance(node, ast.ClassDef):
                complexity += 2
        return min(complexity / 10.0, 1.0)
    
    def _detect_intent(self, text: str) -> str:
        """Simple intent detection"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['error', 'bug', 'issue', 'problem']):
            return 'error'
        elif any(word in text_lower for word in ['how', 'what', 'why', 'when', '?']):
            return 'question'
        elif any(word in text_lower for word in ['create', 'make', 'build', 'generate']):
            return 'request'
        elif any(word in text_lower for word in ['good', 'great', 'thanks', 'perfect']):
            return 'feedback'
        else:
            return 'statement'
    
    def _extract_topic(self, text: str) -> str:
        """Extract main topic from text"""
        # Simple keyword extraction
        tech_keywords = [
            'python', 'javascript', 'react', 'api', 'database', 'algorithm',
            'function', 'class', 'variable', 'loop', 'condition', 'error'
        ]
        
        text_lower = text.lower()
        found_topics = [keyword for keyword in tech_keywords if keyword in text_lower]
        return found_topics[0] if found_topics else 'general'
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities"""
        # Simple pattern-based entity extraction
        entities = []
        
        # File paths
        file_pattern = re.compile(r'[\w/]+\.[\w]+')
        entities.extend(file_pattern.findall(text))
        
        # Function/method calls
        function_pattern = re.compile(r'\w+\(\)')
        entities.extend(function_pattern.findall(text))
        
        # Variables (capitalized words)
        var_pattern = re.compile(r'\b[A-Z][a-z]+\b')
        entities.extend(var_pattern.findall(text))
        
        return list(set(entities))
    
    def _analyze_sentiment(self, text: str) -> float:
        """Simple sentiment analysis (-1 to 1)"""
        positive_words = ['good', 'great', 'excellent', 'perfect', 'awesome', 'love']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'wrong', 'error', 'problem']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def _needs_follow_up(self, text: str, intent: str) -> bool:
        """Determine if follow-up is needed"""
        if intent == 'question':
            return True
        elif intent == 'error':
            return 'solved' not in text.lower()
        elif intent == 'request':
            return 'done' not in text.lower() and 'complete' not in text.lower()
        return False
