"""
Enhanced GitHub integration with persistent code pattern memory
Extends existing GitHub integration with Cognee memory capabilities
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from github import Github
import os

from ..ai.cognee_model_manager import CogneeModelManager, MemoryEnabledRequest
from ..agents.memory_enabled_agent import CodeAnalystAgent, DebugDetectiveAgent

logger = logging.getLogger(__name__)

class GitHubMemoryIntegration:
    """Enhanced GitHub integration with code pattern memory"""
    
    def __init__(
        self, 
        github_token: str, 
        memory_manager: CogneeModelManager,
        config: Dict[str, Any] = None
    ):
        self.github = Github(github_token)
        self.memory_manager = memory_manager
        self.config = config or {}
        
        # Initialize agents
        self.code_agent = CodeAnalystAgent(
            agent_id="github_code_analyst",
            model_manager=memory_manager
        )
        
        self.debug_agent = DebugDetectiveAgent(
            agent_id="github_debug_detective", 
            model_manager=memory_manager
        )
    
    async def analyze_repository_with_memory(
        self, 
        repo_owner: str, 
        repo_name: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Comprehensive repository analysis with memory persistence"""
        
        try:
            logger.info(f"🔍 Analyzing repository {repo_owner}/{repo_name} with memory...")
            
            repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
            
            # Get repository structure
            repo_structure = await self._get_repository_structure(repo, branch)
            
            # Analyze code files with memory
            analysis_results = []
            code_patterns = []
            
            for file_info in repo_structure["code_files"]:
                file_analysis = await self._analyze_file_with_memory(
                    repo, file_info, repo_owner, repo_name
                )
                
                analysis_results.append(file_analysis)
                code_patterns.extend(file_analysis.get("patterns", []))
            
            # Store repository-level memory
            await self._store_repository_memory(
                repo_owner, repo_name, analysis_results, code_patterns
            )
            
            # Generate repository insights
            repo_insights = await self._generate_repository_insights(
                repo_owner, repo_name, analysis_results
            )
            
            return {
                "repository": f"{repo_owner}/{repo_name}",
                "branch": branch,
                "analysis_summary": {
                    "files_analyzed": len(analysis_results),
                    "patterns_detected": len(code_patterns),
                    "issues_found": sum(len(r.get("issues", [])) for r in analysis_results),
                    "suggestions_count": sum(len(r.get("suggestions", [])) for r in analysis_results)
                },
                "insights": repo_insights,
                "memory_updated": True,
                "cost": 0.0,  # Local models = $0.00
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            raise

    async def _get_repository_structure(self, repo, branch: str) -> Dict[str, Any]:
        """Get repository file structure"""
        try:
            contents = repo.get_contents("", ref=branch)
            code_files = []
            
            def process_contents(contents_list, path_prefix=""):
                for content in contents_list:
                    if content.type == "dir":
                        # Recursively process directories (limit depth)
                        if path_prefix.count("/") < 3:  # Limit depth to avoid too many files
                            try:
                                sub_contents = repo.get_contents(content.path, ref=branch)
                                process_contents(sub_contents, content.path + "/")
                            except:
                                pass  # Skip if can't access directory
                    else:
                        # Check if it's a code file
                        file_ext = content.name.split(".")[-1].lower()
                        if file_ext in ["py", "js", "ts", "java", "cpp", "c", "go", "rs", "rb", "php"]:
                            code_files.append({
                                "path": content.path,
                                "name": content.name,
                                "language": self._get_language_from_extension(file_ext),
                                "size": content.size
                            })
            
            process_contents(contents)
            
            return {
                "total_files": len(code_files),
                "code_files": code_files[:50],  # Limit to first 50 files
                "languages": list(set(f["language"] for f in code_files))
            }
            
        except Exception as e:
            logger.warning(f"Failed to get repository structure: {e}")
            return {"total_files": 0, "code_files": [], "languages": []}

    def _get_language_from_extension(self, ext: str) -> str:
        """Map file extension to programming language"""
        language_map = {
            "py": "Python",
            "js": "JavaScript", 
            "ts": "TypeScript",
            "java": "Java",
            "cpp": "C++",
            "c": "C",
            "go": "Go",
            "rs": "Rust",
            "rb": "Ruby",
            "php": "PHP"
        }
        return language_map.get(ext, ext.upper())

    async def _analyze_file_with_memory(
        self, 
        repo, 
        file_info: Dict[str, Any], 
        repo_owner: str, 
        repo_name: str
    ) -> Dict[str, Any]:
        """Analyze individual file with memory context"""
        
        try:
            # Get file content
            file_content = repo.get_contents(file_info["path"])
            content = file_content.decoded_content.decode('utf-8')
            
            # Limit content size for analysis
            if len(content) > 10000:  # Limit to 10KB
                content = content[:10000] + "\n... (truncated)"
            
            # Check for similar code patterns in memory
            similar_patterns = await self._get_similar_code_patterns(
                content, file_info["language"]
            )
            
            # Analyze with code agent
            analysis_request = f"""
            Analyze this {file_info['language']} file: {file_info['path']}
            Repository: {repo_owner}/{repo_name}
            
            Code:
            {content}
            
            Similar patterns found in memory:
            {json.dumps(similar_patterns[:3], indent=2)}
            
            Provide:
            1. Code quality assessment
            2. Security analysis
            3. Performance considerations
            4. Detected patterns
            5. Improvement suggestions
            6. Comparison with similar code in memory
            """
            
            response = await self.code_agent.process_request(
                analysis_request,
                context={
                    "file_path": file_info["path"],
                    "repository": f"{repo_owner}/{repo_name}",
                    "language": file_info["language"],
                    "similar_patterns": similar_patterns
                }
            )
            
            # Extract structured analysis
            analysis = self._extract_structured_analysis(response["response"])
            
            # Store file-specific memory
            await self._store_file_memory(
                repo_owner, repo_name, file_info["path"], content, analysis
            )
            
            return {
                "file_path": file_info["path"],
                "language": file_info["language"],
                "analysis": analysis,
                "patterns": analysis.get("patterns", []),
                "issues": analysis.get("issues", []),
                "suggestions": analysis.get("suggestions", []),
                "security_score": analysis.get("security_score", 0),
                "quality_score": analysis.get("quality_score", 0),
                "similar_patterns_used": len(similar_patterns)
            }
            
        except Exception as e:
            logger.warning(f"File analysis failed for {file_info['path']}: {e}")
            return {
                "file_path": file_info["path"],
                "error": str(e),
                "analysis": {},
                "patterns": [],
                "issues": [],
                "suggestions": []
            }

    async def _get_similar_code_patterns(
        self, 
        code_content: str, 
        language: str
    ) -> List[Dict[str, Any]]:
        """Find similar code patterns in memory"""
        
        try:
            if not self.memory_manager.cognee_initialized:
                return []
            
            # Search for similar code patterns
            search_query = f"code patterns {language} similar to: {code_content[:200]}"
            
            result = await self.memory_manager.query_knowledge_graph(
                query=search_query,
                query_type="insights"
            )
            
            # Filter and format results
            patterns = []
            for result_item in result.get("results", [])[:5]:
                if isinstance(result_item, dict):
                    patterns.append({
                        "pattern_type": result_item.get("pattern_type", "unknown"),
                        "description": result_item.get("description", ""),
                        "language": result_item.get("language", language),
                        "confidence": result_item.get("confidence", 0.0),
                        "repository": result_item.get("repository", ""),
                        "usage_count": result_item.get("usage_count", 1)
                    })
            
            return patterns
            
        except Exception as e:
            logger.warning(f"Failed to get similar code patterns: {e}")
            return []

    async def _store_repository_memory(
        self,
        repo_owner: str,
        repo_name: str,
        analysis_results: List[Dict[str, Any]],
        code_patterns: List[str]
    ):
        """Store comprehensive repository memory"""
        
        try:
            if not self.memory_manager.cognee_initialized:
                return
            
            # Create repository memory entry
            repo_memory = {
                "repository": f"{repo_owner}/{repo_name}",
                "analysis_timestamp": datetime.now().isoformat(),
                "total_files": len(analysis_results),
                "languages": list(set(r.get("language", "") for r in analysis_results)),
                "patterns": code_patterns,
                "quality_scores": [r.get("quality_score", 0) for r in analysis_results],
                "security_scores": [r.get("security_score", 0) for r in analysis_results],
                "total_issues": sum(len(r.get("issues", [])) for r in analysis_results),
                "total_suggestions": sum(len(r.get("suggestions", [])) for r in analysis_results),
                "analysis_results": analysis_results
            }
            
            # Store using memory manager
            memory_request = MemoryEnabledRequest(
                prompt=f"Repository analysis for {repo_owner}/{repo_name}",
                agent_id="github_code_analyst",
                memory_tags=["github", "repository", "code_analysis", repo_owner, repo_name],
                persist_response=True
            )
            
            # Store the memory entry
            await self.memory_manager.generate_with_memory(memory_request)
            
            logger.info(f"Stored repository memory for {repo_owner}/{repo_name}")
            
        except Exception as e:
            logger.warning(f"Failed to store repository memory: {e}")

    async def _store_file_memory(
        self,
        repo_owner: str,
        repo_name: str,
        file_path: str,
        content: str,
        analysis: Dict[str, Any]
    ):
        """Store file-specific memory"""
        
        try:
            if not self.memory_manager.cognee_initialized:
                return
            
            # Create file memory entry
            file_memory = {
                "repository": f"{repo_owner}/{repo_name}",
                "file_path": file_path,
                "content_hash": hash(content),
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store using memory manager
            memory_request = MemoryEnabledRequest(
                prompt=f"File analysis for {file_path} in {repo_owner}/{repo_name}",
                agent_id="github_code_analyst",
                memory_tags=["github", "file_analysis", repo_owner, repo_name, file_path],
                persist_response=True
            )
            
            await self.memory_manager.generate_with_memory(memory_request)
            
        except Exception as e:
            logger.warning(f"Failed to store file memory: {e}")

    def _extract_structured_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Extract structured data from analysis text"""
        
        # This is a simplified extraction - in practice, you'd want more sophisticated parsing
        analysis = {
            "patterns": [],
            "issues": [],
            "suggestions": [],
            "security_score": 7,  # Default scores
            "quality_score": 7
        }
        
        # Extract patterns (look for pattern indicators)
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if 'pattern' in line.lower() and line:
                if line not in analysis["patterns"]:
                    analysis["patterns"].append(line)
            elif any(word in line.lower() for word in ['issue', 'problem', 'bug', 'error']) and line:
                if line not in analysis["issues"]:
                    analysis["issues"].append(line)
            elif any(word in line.lower() for word in ['suggest', 'recommend', 'improve']) and line:
                if line not in analysis["suggestions"]:
                    analysis["suggestions"].append(line)
        
        # Extract scores if mentioned
        if 'security' in analysis_text.lower():
            # Look for security score patterns
            import re
            score_match = re.search(r'security.*?(\d+)', analysis_text.lower())
            if score_match:
                analysis["security_score"] = min(int(score_match.group(1)), 10)
        
        if 'quality' in analysis_text.lower():
            # Look for quality score patterns
            import re
            score_match = re.search(r'quality.*?(\d+)', analysis_text.lower())
            if score_match:
                analysis["quality_score"] = min(int(score_match.group(1)), 10)
        
        return analysis

    async def _generate_repository_insights(
        self,
        repo_owner: str,
        repo_name: str,
        analysis_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate repository-level insights"""
        
        try:
            # Calculate aggregate metrics
            total_files = len(analysis_results)
            avg_quality = sum(r.get("quality_score", 0) for r in analysis_results) / max(total_files, 1)
            avg_security = sum(r.get("security_score", 0) for r in analysis_results) / max(total_files, 1)
            
            # Collect all patterns
            all_patterns = []
            for result in analysis_results:
                all_patterns.extend(result.get("patterns", []))
            
            # Count pattern frequency
            pattern_counts = {}
            for pattern in all_patterns:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            # Get top patterns
            top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            insights = {
                "overall_quality_score": round(avg_quality, 1),
                "overall_security_score": round(avg_security, 1),
                "total_files_analyzed": total_files,
                "top_patterns": [{"pattern": p[0], "frequency": p[1]} for p in top_patterns],
                "languages_used": list(set(r.get("language", "") for r in analysis_results)),
                "total_issues": sum(len(r.get("issues", [])) for r in analysis_results),
                "total_suggestions": sum(len(r.get("suggestions", [])) for r in analysis_results),
                "recommendations": self._generate_recommendations(analysis_results)
            }
            
            return insights
            
        except Exception as e:
            logger.warning(f"Failed to generate repository insights: {e}")
            return {}

    def _generate_recommendations(self, analysis_results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on analysis results"""
        
        recommendations = []
        
        # Analyze common issues
        all_issues = []
        for result in analysis_results:
            all_issues.extend(result.get("issues", []))
        
        # Count issue frequency
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Generate recommendations based on frequent issues
        if issue_counts:
            top_issue = max(issue_counts.items(), key=lambda x: x[1])
            recommendations.append(f"Address recurring issue: {top_issue[0]}")
        
        # Quality-based recommendations
        avg_quality = sum(r.get("quality_score", 0) for r in analysis_results) / max(len(analysis_results), 1)
        if avg_quality < 6:
            recommendations.append("Improve overall code quality through refactoring")
        
        # Security-based recommendations
        avg_security = sum(r.get("security_score", 0) for r in analysis_results) / max(len(analysis_results), 1)
        if avg_security < 7:
            recommendations.append("Enhance security measures and conduct security audit")
        
        # Default recommendations
        if not recommendations:
            recommendations = [
                "Continue maintaining good code quality",
                "Regular code reviews and testing",
                "Keep dependencies updated"
            ]
        
        return recommendations[:5]  # Limit to 5 recommendations

    async def create_memory_enhanced_pr(
        self,
        repo_owner: str,
        repo_name: str,
        pr_data: Dict[str, Any],
        auto_enhance: bool = True
    ) -> Dict[str, Any]:
        """Create PR with memory-based code insights and suggestions"""
        
        try:
            repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
            
            # Get repository memory context
            repo_context = await self._get_repository_memory_context(repo_owner, repo_name)
            
            # Enhance PR description with memory insights
            enhanced_description = pr_data.get("body", "")
            if auto_enhance and repo_context:
                enhanced_description = await self._enhance_pr_description(
                    enhanced_description, repo_context
                )
            
            # Create the pull request
            pr = repo.create_pull(
                title=pr_data["title"],
                body=enhanced_description,
                head=pr_data["head"],
                base=pr_data["base"]
            )
            
            # Store PR context in memory
            await self._store_pr_memory(repo_owner, repo_name, pr)
            
            return {
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "title": pr.title,
                "enhanced_description": enhanced_description,
                "memory_insights_used": len(repo_context.get("insights", [])),
                "cost": 0.0,
                "created_at": pr.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Memory-enhanced PR creation failed: {e}")
            raise

    async def _get_repository_memory_context(
        self, 
        repo_owner: str, 
        repo_name: str
    ) -> Dict[str, Any]:
        """Get repository memory context"""
        
        try:
            if not self.memory_manager.cognee_initialized:
                return {}
            
            # Query repository memory
            result = await self.memory_manager.query_knowledge_graph(
                query=f"repository {repo_owner}/{repo_name} insights patterns",
                filters={"tags": ["github", "repository", repo_owner, repo_name]}
            )
            
            return {
                "insights": result.get("results", []),
                "repository": f"{repo_owner}/{repo_name}"
            }
            
        except Exception as e:
            logger.warning(f"Failed to get repository memory context: {e}")
            return {}

    async def _enhance_pr_description(
        self,
        description: str,
        repo_context: Dict[str, Any]
    ) -> str:
        """Enhance PR description with memory insights"""
        
        if not repo_context.get("insights"):
            return description
        
        # Add memory insights section
        insights_section = "\n\n## 🧠 Memory-Enhanced Insights\n\n"
        
        for insight in repo_context["insights"][:3]:  # Top 3 insights
            if isinstance(insight, dict):
                insight_desc = insight.get("description", str(insight))
                insights_section += f"- {insight_desc[:100]}...\n"
        
        insights_section += "\n*Generated using reVoAgent's memory-enabled code analysis*"
        
        return description + insights_section

    async def _store_pr_memory(
        self,
        repo_owner: str,
        repo_name: str,
        pr
    ):
        """Store PR context in memory"""
        
        try:
            if not self.memory_manager.cognee_initialized:
                return
            
            # Create PR memory entry
            pr_memory = {
                "repository": f"{repo_owner}/{repo_name}",
                "pr_number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "created_at": pr.created_at.isoformat(),
                "head": pr.head.ref,
                "base": pr.base.ref
            }
            
            # Store using memory manager
            memory_request = MemoryEnabledRequest(
                prompt=f"Pull request #{pr.number} created for {repo_owner}/{repo_name}: {pr.title}",
                agent_id="github_code_analyst",
                memory_tags=["github", "pull_request", repo_owner, repo_name, f"pr_{pr.number}"],
                persist_response=True
            )
            
            await self.memory_manager.generate_with_memory(memory_request)
            
        except Exception as e:
            logger.warning(f"Failed to store PR memory: {e}")

# Factory function
def create_github_memory_integration(
    github_token: str = None,
    memory_manager: CogneeModelManager = None,
    config: Dict[str, Any] = None
) -> GitHubMemoryIntegration:
    """Create GitHub memory integration instance"""
    
    if not github_token:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GitHub token is required")
    
    if not memory_manager:
        raise ValueError("Memory manager is required")
    
    return GitHubMemoryIntegration(github_token, memory_manager, config)