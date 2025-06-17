#!/usr/bin/env python3
"""
Real Gemini Agent Implementation
Specialized AI agent using Gemini Pro for analysis, optimization, and architectural review
"""

import asyncio
import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.packages.ai.real_model_manager import RealModelManager, RealGenerationRequest, ModelType

logger = logging.getLogger(__name__)

@dataclass
class AnalysisTask:
    """Task for code/system analysis"""
    task_id: str
    title: str
    description: str
    analysis_type: str = "general"  # general, performance, security, architecture
    target_code: Optional[str] = None
    target_system: Optional[str] = None
    context: Optional[str] = None
    requirements: List[str] = field(default_factory=list)
    deadline: Optional[datetime] = None

@dataclass
class AnalysisResult:
    """Result of analysis"""
    task_id: str
    agent_id: str
    analysis_type: str
    findings: Dict[str, Any]
    recommendations: List[str]
    severity_score: float = 0.0  # 0-1 scale
    confidence_score: float = 0.0  # 0-1 scale
    analysis_time: float = 0.0
    cost: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class RealGeminiAgent:
    """Real Gemini Agent for analysis and optimization"""
    
    def __init__(self, model_manager: RealModelManager, agent_id: Optional[str] = None):
        self.agent_id = agent_id or f"gemini-{uuid.uuid4().hex[:8]}"
        self.model_manager = model_manager
        self.specialties = [
            "performance_analysis",
            "security_analysis", 
            "architecture_review",
            "code_optimization",
            "database_optimization",
            "system_design",
            "scalability_analysis",
            "cost_optimization",
            "technical_documentation",
            "risk_assessment"
        ]
        self.performance_metrics = {
            "analyses_completed": 0,
            "success_rate": 1.0,
            "average_confidence_score": 0.0,
            "average_response_time": 0.0,
            "total_cost": 0.0,
            "critical_issues_found": 0
        }
        self.is_busy = False
        self.current_task: Optional[str] = None
        
    async def analyze_code(self, task: AnalysisTask) -> AnalysisResult:
        """Perform comprehensive code analysis"""
        start_time = time.time()
        self.is_busy = True
        self.current_task = task.task_id
        
        try:
            logger.info(f"🔍 {self.agent_id} starting {task.analysis_type} analysis: {task.title}")
            
            # Create specialized prompt based on analysis type
            prompt = self._create_analysis_prompt(task)
            
            # Perform analysis using Gemini
            request = RealGenerationRequest(
                prompt=prompt,
                model_preference=ModelType.GEMINI_PRO,
                max_tokens=2000,
                temperature=0.1,  # Low temperature for analytical consistency
                system_prompt=self._get_analysis_system_prompt(task.analysis_type),
                context=task.context,
                task_type="analysis"
            )
            
            response = await self.model_manager.generate_response(request)
            
            if not response.success:
                raise Exception(response.error_message or "Analysis failed")
            
            # Parse analysis results
            findings, recommendations, severity_score, confidence_score = self._parse_analysis_results(
                response.content, task.analysis_type
            )
            
            # Create result
            result = AnalysisResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                analysis_type=task.analysis_type,
                findings=findings,
                recommendations=recommendations,
                severity_score=severity_score,
                confidence_score=confidence_score,
                analysis_time=time.time() - start_time,
                cost=response.cost,
                success=True,
                metadata={
                    "model_used": response.model_used.value,
                    "tokens_used": response.tokens_used,
                    "analysis_depth": "comprehensive"
                }
            )
            
            # Update performance metrics
            await self._update_performance_metrics(result)
            
            logger.info(f"✅ {self.agent_id} completed analysis (Confidence: {confidence_score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"❌ {self.agent_id} analysis failed: {e}")
            return AnalysisResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                analysis_type=task.analysis_type,
                findings={},
                recommendations=[],
                severity_score=0.0,
                confidence_score=0.0,
                analysis_time=time.time() - start_time,
                cost=0.0,
                success=False,
                error_message=str(e)
            )
        finally:
            self.is_busy = False
            self.current_task = None
    
    def _create_analysis_prompt(self, task: AnalysisTask) -> str:
        """Create specialized prompt based on analysis type"""
        
        base_prompt = f"""
Perform a comprehensive {task.analysis_type} analysis for the following:

**Task**: {task.title}
**Description**: {task.description}
**Analysis Type**: {task.analysis_type}
"""
        
        if task.target_code:
            base_prompt += f"""
**Code to Analyze**:
```
{task.target_code}
```
"""
        
        if task.target_system:
            base_prompt += f"""
**System to Analyze**: {task.target_system}
"""
        
        if task.requirements:
            base_prompt += "\n**Requirements**:\n"
            for req in task.requirements:
                base_prompt += f"- {req}\n"
        
        # Add analysis-specific instructions
        if task.analysis_type == "performance":
            base_prompt += self._get_performance_analysis_instructions()
        elif task.analysis_type == "security":
            base_prompt += self._get_security_analysis_instructions()
        elif task.analysis_type == "architecture":
            base_prompt += self._get_architecture_analysis_instructions()
        else:
            base_prompt += self._get_general_analysis_instructions()
        
        return base_prompt
    
    def _get_performance_analysis_instructions(self) -> str:
        """Get performance analysis specific instructions"""
        return """

**Performance Analysis Instructions**:
1. **Time Complexity**: Analyze algorithmic complexity (Big O notation)
2. **Space Complexity**: Evaluate memory usage patterns
3. **Bottlenecks**: Identify performance bottlenecks and hotspots
4. **Database Performance**: Analyze query efficiency and indexing
5. **Caching Opportunities**: Identify areas for caching improvements
6. **Scalability**: Assess horizontal and vertical scaling potential
7. **Resource Utilization**: CPU, memory, I/O efficiency

**Output Format**:
- **Performance Score**: X/10
- **Critical Issues**: List of performance problems
- **Optimization Opportunities**: Specific improvement suggestions
- **Estimated Impact**: Expected performance gains
- **Implementation Priority**: High/Medium/Low for each recommendation
"""
    
    def _get_security_analysis_instructions(self) -> str:
        """Get security analysis specific instructions"""
        return """

**Security Analysis Instructions**:
1. **Vulnerability Assessment**: Check for common security vulnerabilities
2. **Input Validation**: Analyze input sanitization and validation
3. **Authentication/Authorization**: Review access control mechanisms
4. **Data Protection**: Assess data encryption and privacy measures
5. **Injection Attacks**: Check for SQL, XSS, command injection risks
6. **Configuration Security**: Review security configurations
7. **Dependency Security**: Analyze third-party library vulnerabilities

**Output Format**:
- **Security Score**: X/10
- **Critical Vulnerabilities**: High-risk security issues
- **Medium/Low Issues**: Less critical security concerns
- **Compliance**: OWASP, GDPR, SOC2 compliance assessment
- **Remediation Steps**: Specific security improvements
"""
    
    def _get_architecture_analysis_instructions(self) -> str:
        """Get architecture analysis specific instructions"""
        return """

**Architecture Analysis Instructions**:
1. **Design Patterns**: Evaluate architectural patterns and their appropriateness
2. **Modularity**: Assess component separation and coupling
3. **Scalability**: Review system's ability to handle growth
4. **Maintainability**: Evaluate code organization and documentation
5. **Reliability**: Assess fault tolerance and error handling
6. **Technology Stack**: Review technology choices and compatibility
7. **Integration**: Analyze system integration points and APIs

**Output Format**:
- **Architecture Score**: X/10
- **Strengths**: Well-designed architectural aspects
- **Weaknesses**: Areas needing improvement
- **Refactoring Suggestions**: Specific architectural improvements
- **Technology Recommendations**: Better technology choices
"""
    
    def _get_general_analysis_instructions(self) -> str:
        """Get general analysis instructions"""
        return """

**General Analysis Instructions**:
1. **Code Quality**: Assess overall code quality and maintainability
2. **Best Practices**: Check adherence to industry best practices
3. **Documentation**: Evaluate code documentation quality
4. **Testing**: Assess test coverage and quality
5. **Error Handling**: Review exception handling and logging
6. **Dependencies**: Analyze external dependencies and their management
7. **Deployment**: Review deployment and configuration aspects

**Output Format**:
- **Overall Score**: X/10
- **Key Findings**: Most important discoveries
- **Recommendations**: Prioritized improvement suggestions
- **Risk Assessment**: Potential risks and mitigation strategies
"""
    
    def _get_analysis_system_prompt(self, analysis_type: str) -> str:
        """Get system prompt for specific analysis type"""
        base_prompt = """You are an expert software architect and security analyst with extensive experience in:

- Performance optimization and scalability
- Security vulnerability assessment
- Code quality and best practices
- System architecture and design patterns
- Database optimization and query analysis
- Cloud infrastructure and DevOps
- Risk assessment and mitigation strategies

You provide thorough, actionable analysis with specific recommendations and clear prioritization."""
        
        type_specific = {
            "performance": """
You specialize in performance analysis and optimization. You can:
- Identify performance bottlenecks and inefficiencies
- Analyze algorithmic complexity and suggest optimizations
- Recommend caching strategies and database optimizations
- Assess scalability and resource utilization
- Provide specific performance improvement recommendations
""",
            "security": """
You specialize in cybersecurity and vulnerability assessment. You can:
- Identify security vulnerabilities and attack vectors
- Assess compliance with security standards (OWASP, NIST)
- Recommend security best practices and controls
- Analyze authentication and authorization mechanisms
- Provide specific security remediation steps
""",
            "architecture": """
You specialize in software architecture and system design. You can:
- Evaluate architectural patterns and design decisions
- Assess system modularity and coupling
- Recommend architectural improvements and refactoring
- Analyze technology stack appropriateness
- Provide scalability and maintainability guidance
"""
        }
        
        return base_prompt + type_specific.get(analysis_type, "")
    
    def _parse_analysis_results(self, content: str, analysis_type: str) -> tuple[Dict[str, Any], List[str], float, float]:
        """Parse analysis results from generated content"""
        import re
        
        findings = {}
        recommendations = []
        severity_score = 0.5  # Default medium severity
        confidence_score = 0.8  # Default high confidence
        
        # Extract score if present
        score_pattern = r'(?:Score|Rating):\s*(\d+(?:\.\d+)?)/10'
        score_match = re.search(score_pattern, content, re.IGNORECASE)
        if score_match:
            score = float(score_match.group(1))
            severity_score = 1.0 - (score / 10.0)  # Convert to severity (lower score = higher severity)
        
        # Extract sections based on analysis type
        if analysis_type == "performance":
            findings = self._extract_performance_findings(content)
        elif analysis_type == "security":
            findings = self._extract_security_findings(content)
        elif analysis_type == "architecture":
            findings = self._extract_architecture_findings(content)
        else:
            findings = self._extract_general_findings(content)
        
        # Extract recommendations
        recommendations = self._extract_recommendations(content)
        
        # Calculate confidence based on content quality
        confidence_score = self._calculate_confidence_score(content, findings, recommendations)
        
        return findings, recommendations, severity_score, confidence_score
    
    def _extract_performance_findings(self, content: str) -> Dict[str, Any]:
        """Extract performance-specific findings"""
        findings = {
            "complexity_analysis": "",
            "bottlenecks": [],
            "optimization_opportunities": [],
            "resource_usage": "",
            "scalability_assessment": ""
        }
        
        # Extract complexity information
        complexity_pattern = r'(?:Time|Space)\s+Complexity[:\s]+(.*?)(?:\n|$)'
        complexity_matches = re.findall(complexity_pattern, content, re.IGNORECASE)
        if complexity_matches:
            findings["complexity_analysis"] = "; ".join(complexity_matches)
        
        # Extract bottlenecks
        bottleneck_pattern = r'(?:Bottleneck|Performance Issue)[:\s]+(.*?)(?:\n|$)'
        bottleneck_matches = re.findall(bottleneck_pattern, content, re.IGNORECASE)
        findings["bottlenecks"] = bottleneck_matches
        
        return findings
    
    def _extract_security_findings(self, content: str) -> Dict[str, Any]:
        """Extract security-specific findings"""
        findings = {
            "vulnerabilities": [],
            "security_score": 0.0,
            "compliance_issues": [],
            "risk_level": "medium"
        }
        
        # Extract vulnerabilities
        vuln_keywords = ["vulnerability", "security issue", "exploit", "injection", "xss"]
        for keyword in vuln_keywords:
            pattern = rf'{keyword}[:\s]+(.*?)(?:\n|$)'
            matches = re.findall(pattern, content, re.IGNORECASE)
            findings["vulnerabilities"].extend(matches)
        
        # Determine risk level
        if any(word in content.lower() for word in ["critical", "high risk", "severe"]):
            findings["risk_level"] = "high"
        elif any(word in content.lower() for word in ["low risk", "minor", "informational"]):
            findings["risk_level"] = "low"
        
        return findings
    
    def _extract_architecture_findings(self, content: str) -> Dict[str, Any]:
        """Extract architecture-specific findings"""
        findings = {
            "design_patterns": [],
            "modularity_assessment": "",
            "scalability_issues": [],
            "technology_recommendations": []
        }
        
        # Extract design patterns mentioned
        pattern_keywords = ["singleton", "factory", "observer", "mvc", "microservices", "monolith"]
        for pattern in pattern_keywords:
            if pattern in content.lower():
                findings["design_patterns"].append(pattern)
        
        return findings
    
    def _extract_general_findings(self, content: str) -> Dict[str, Any]:
        """Extract general findings"""
        findings = {
            "code_quality": "",
            "best_practices": [],
            "issues_found": [],
            "strengths": []
        }
        
        # Extract issues and strengths
        issue_pattern = r'(?:Issue|Problem|Concern)[:\s]+(.*?)(?:\n|$)'
        issue_matches = re.findall(issue_pattern, content, re.IGNORECASE)
        findings["issues_found"] = issue_matches
        
        strength_pattern = r'(?:Strength|Good|Positive)[:\s]+(.*?)(?:\n|$)'
        strength_matches = re.findall(strength_pattern, content, re.IGNORECASE)
        findings["strengths"] = strength_matches
        
        return findings
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from content"""
        recommendations = []
        
        # Look for recommendation sections
        rec_patterns = [
            r'(?:Recommendation|Suggestion)[:\s]+(.*?)(?:\n|$)',
            r'(?:Should|Consider|Implement)[:\s]+(.*?)(?:\n|$)',
            r'(?:Improve|Optimize|Fix)[:\s]+(.*?)(?:\n|$)'
        ]
        
        for pattern in rec_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            recommendations.extend(matches)
        
        # Remove duplicates and clean up
        recommendations = list(set([rec.strip() for rec in recommendations if rec.strip()]))
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _calculate_confidence_score(self, content: str, findings: Dict[str, Any], recommendations: List[str]) -> float:
        """Calculate confidence score based on analysis quality"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on content length and detail
        if len(content) > 500:
            confidence += 0.1
        if len(content) > 1000:
            confidence += 0.1
        
        # Increase confidence based on findings quality
        if findings and any(findings.values()):
            confidence += 0.1
        
        # Increase confidence based on recommendations
        if len(recommendations) >= 3:
            confidence += 0.1
        if len(recommendations) >= 5:
            confidence += 0.1
        
        # Check for specific technical terms (indicates depth)
        technical_terms = ["algorithm", "complexity", "performance", "security", "architecture", "scalability"]
        term_count = sum(1 for term in technical_terms if term in content.lower())
        confidence += min(term_count * 0.05, 0.2)
        
        return min(confidence, 1.0)
    
    async def optimize_performance(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Provide performance optimization suggestions"""
        prompt = f"""
Analyze the following {language} code and provide specific performance optimization recommendations:

```{language}
{code}
```

**Focus Areas**:
1. Algorithmic efficiency improvements
2. Memory usage optimization
3. I/O operation optimization
4. Caching opportunities
5. Database query optimization (if applicable)

**Provide**:
- Current performance assessment
- Specific optimization techniques
- Optimized code examples
- Expected performance improvements
"""
        
        request = RealGenerationRequest(
            prompt=prompt,
            model_preference=ModelType.GEMINI_PRO,
            max_tokens=1500,
            temperature=0.2,
            system_prompt="You are a performance optimization expert specializing in code efficiency and scalability.",
            task_type="optimization"
        )
        
        response = await self.model_manager.generate_response(request)
        
        return {
            "optimization_suggestions": response.content,
            "success": response.success,
            "cost": response.cost,
            "agent_id": self.agent_id
        }
    
    async def assess_security(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Perform security assessment of code"""
        prompt = f"""
Perform a comprehensive security analysis of the following {language} code:

```{language}
{code}
```

**Security Checklist**:
1. Input validation and sanitization
2. SQL injection vulnerabilities
3. XSS vulnerabilities
4. Authentication and authorization issues
5. Data encryption and privacy
6. Error handling and information disclosure
7. Dependency vulnerabilities

**Provide**:
- Security risk assessment (High/Medium/Low)
- Specific vulnerabilities found
- Remediation recommendations
- Secure code examples
"""
        
        request = RealGenerationRequest(
            prompt=prompt,
            model_preference=ModelType.GEMINI_PRO,
            max_tokens=1500,
            temperature=0.1,
            system_prompt="You are a cybersecurity expert specializing in code security analysis and vulnerability assessment.",
            task_type="security_analysis"
        )
        
        response = await self.model_manager.generate_response(request)
        
        return {
            "security_assessment": response.content,
            "success": response.success,
            "cost": response.cost,
            "agent_id": self.agent_id
        }
    
    async def _update_performance_metrics(self, result: AnalysisResult):
        """Update agent performance metrics"""
        self.performance_metrics["analyses_completed"] += 1
        self.performance_metrics["total_cost"] += result.cost
        
        # Update success rate
        current_success_rate = self.performance_metrics["success_rate"]
        analyses_completed = self.performance_metrics["analyses_completed"]
        
        if result.success:
            self.performance_metrics["success_rate"] = (
                (current_success_rate * (analyses_completed - 1) + 1.0) / analyses_completed
            )
        else:
            self.performance_metrics["success_rate"] = (
                (current_success_rate * (analyses_completed - 1) + 0.0) / analyses_completed
            )
        
        # Update average confidence score
        if result.success:
            current_avg_confidence = self.performance_metrics["average_confidence_score"]
            self.performance_metrics["average_confidence_score"] = (
                (current_avg_confidence * (analyses_completed - 1) + result.confidence_score) / analyses_completed
            )
        
        # Update average response time
        current_avg_time = self.performance_metrics["average_response_time"]
        self.performance_metrics["average_response_time"] = (
            (current_avg_time * (analyses_completed - 1) + result.analysis_time) / analyses_completed
        )
        
        # Count critical issues
        if result.severity_score > 0.7:  # High severity
            self.performance_metrics["critical_issues_found"] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "specialties": self.specialties,
            "is_busy": self.is_busy,
            "current_task": self.current_task,
            "performance_metrics": self.performance_metrics.copy()
        }
    
    def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        return [
            "Performance analysis and optimization",
            "Security vulnerability assessment",
            "Architecture review and design",
            "Code quality analysis",
            "Database optimization",
            "Scalability assessment",
            "Risk analysis and mitigation",
            "Technology stack evaluation",
            "Compliance assessment",
            "Technical documentation review"
        ]


# Factory function for easy agent creation
async def create_gemini_agent(model_manager: RealModelManager) -> RealGeminiAgent:
    """Create a new Gemini agent"""
    agent = RealGeminiAgent(model_manager)
    logger.info(f"🔍 Created Gemini agent: {agent.agent_id}")
    return agent


if __name__ == "__main__":
    # Test the Gemini agent
    async def test_gemini_agent():
        from src.packages.ai.real_model_manager import create_real_model_manager
        
        # Create model manager and agent
        model_manager = await create_real_model_manager()
        agent = await create_gemini_agent(model_manager)
        
        # Test code analysis
        test_code = """
def get_user_data(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    result = execute_query(query)
    return result

def process_payment(amount, card_number):
    # No input validation
    charge_card(card_number, amount)
    return "Payment processed"
"""
        
        task = AnalysisTask(
            task_id="test_001",
            title="Security Analysis",
            description="Analyze code for security vulnerabilities",
            analysis_type="security",
            target_code=test_code,
            requirements=[
                "Check for SQL injection vulnerabilities",
                "Assess input validation",
                "Review data handling practices"
            ]
        )
        
        result = await agent.analyze_code(task)
        
        print(f"✅ Analysis result:")
        print(f"📝 Success: {result.success}")
        print(f"🎯 Confidence Score: {result.confidence_score:.2f}")
        print(f"⚠️ Severity Score: {result.severity_score:.2f}")
        print(f"💰 Cost: ${result.cost:.6f}")
        print(f"⏱️ Time: {result.analysis_time:.2f}s")
        print(f"📋 Findings: {result.findings}")
        print(f"💡 Recommendations: {result.recommendations}")
        
        await model_manager.shutdown()
    
    asyncio.run(test_gemini_agent())