#!/usr/bin/env python3
"""
Comprehensive Test Suite for External Integrations
Phase 4 - GitHub, Slack, JIRA Integration Testing
"""

import pytest
import asyncio
import json
import hmac
import hashlib
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

# Import the components to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from packages.integrations.external_integrations import (
    GitHubIntegration,
    IntegrationConfig,
    IntegrationType,
    EventType,
    ExternalEvent
)

class TestGitHubIntegration:
    """Test suite for GitHub Integration"""
    
    @pytest.fixture
    def github_config(self):
        """Create GitHub integration config for testing"""
        return IntegrationConfig(
            name="test_github",
            type=IntegrationType.GITHUB,
            enabled=True,
            credentials={
                "token": "test_token",
                "app_id": "12345",
                "private_key": "test_private_key"
            },
            settings={
                "organization": "test_org",
                "base_url": "https://api.github.com"
            },
            secret_token="test_secret"
        )
    
    @pytest.fixture
    def github_integration(self, github_config):
        """Create GitHub integration instance"""
        return GitHubIntegration(github_config)
    
    @pytest.fixture
    def sample_pr_payload(self):
        """Sample pull request webhook payload"""
        return {
            "action": "opened",
            "pull_request": {
                "number": 123,
                "title": "Fix critical bug in authentication",
                "diff_url": "https://api.github.com/repos/test_org/test_repo/pulls/123.diff",
                "base": {
                    "repo": {
                        "full_name": "test_org/test_repo"
                    }
                }
            }
        }
    
    @pytest.fixture
    def sample_headers(self):
        """Sample webhook headers"""
        return {
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=test_signature"
        }
    
    def test_signature_verification(self, github_integration):
        """Test webhook signature verification"""
        payload = '{"test": "data"}'
        
        # Create valid signature
        expected_signature = hmac.new(
            github_integration.config.secret_token.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        valid_signature = f"sha256={expected_signature}"
        assert github_integration._verify_signature(payload, valid_signature)
        
        # Test invalid signature
        invalid_signature = "sha256=invalid_signature"
        assert not github_integration._verify_signature(payload, invalid_signature)
    
    @pytest.mark.asyncio
    async def test_handle_pull_request_webhook(self, github_integration, sample_headers, sample_pr_payload):
        """Test handling pull request webhook"""
        with patch.object(github_integration, '_verify_signature', return_value=True), \
             patch.object(github_integration, '_analyze_pull_request_comprehensive') as mock_analyze, \
             patch.object(github_integration, '_post_comprehensive_review') as mock_post_review:
            
            mock_analyze.return_value = {
                "quality_score": 85,
                "issues": ["Minor code style issue"],
                "suggestions": ["Consider adding error handling"],
                "security_concerns": [],
                "performance_notes": []
            }
            
            result = await github_integration.handle_webhook(sample_headers, sample_pr_payload)
            
            assert result["status"] == "processed"
            assert result["action"] == "opened"
            assert result["pr_number"] == 123
            assert result["ai_enhanced"] == True
            
            mock_analyze.assert_called_once()
            mock_post_review.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_comprehensive_pr_analysis(self, github_integration, sample_pr_payload):
        """Test comprehensive pull request analysis"""
        pr = sample_pr_payload["pull_request"]
        
        with patch.object(github_integration, '_fetch_diff') as mock_fetch_diff, \
             patch('packages.chat.multi_agent_chat.multi_agent_chat') as mock_chat:
            
            mock_fetch_diff.return_value = "diff content here"
            mock_chat.create_collaboration_session.return_value = "test_session_id"
            mock_chat.process_user_message.return_value = {
                "agent_responses": [
                    {
                        "agent_role": "code_analyst",
                        "content": "Code analysis: Found minor issues in error handling"
                    },
                    {
                        "agent_role": "security_auditor", 
                        "content": "Security analysis: No critical vulnerabilities found"
                    }
                ]
            }
            
            result = await github_integration._analyze_pull_request_comprehensive(pr)
            
            assert "quality_score" in result
            assert "issues" in result
            assert "suggestions" in result
            assert "security_concerns" in result
            
            mock_chat.create_collaboration_session.assert_called_once()
            mock_chat.process_user_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_pull_request(self, github_integration):
        """Test creating a pull request"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json.return_value = {
                "number": 456,
                "html_url": "https://github.com/test_org/test_repo/pull/456",
                "id": 789
            }
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            result = await github_integration.create_pull_request(
                repo="test_repo",
                title="Test PR",
                body="Test description",
                head="feature-branch",
                base="main"
            )
            
            assert result["success"] == True
            assert result["pr_number"] == 456
            assert result["pr_url"] == "https://github.com/test_org/test_repo/pull/456"
    
    @pytest.mark.asyncio
    async def test_create_issue(self, github_integration):
        """Test creating an issue"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json.return_value = {
                "number": 789,
                "html_url": "https://github.com/test_org/test_repo/issues/789",
                "id": 101112
            }
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            result = await github_integration.create_issue(
                repo="test_repo",
                title="Test Issue",
                body="Test issue description",
                labels=["bug", "high-priority"]
            )
            
            assert result["success"] == True
            assert result["issue_number"] == 789
    
    def test_extract_issues_from_response(self, github_integration):
        """Test extracting issues from agent response"""
        content = """
        Code Analysis Results:
        - This is a major issue with memory management
        - Found a problem with null pointer handling
        - The algorithm looks good overall
        - Another issue: missing error validation
        """
        
        issues = github_integration._extract_issues(content)
        
        assert len(issues) > 0
        assert any("issue" in issue.lower() for issue in issues)
        assert any("problem" in issue.lower() for issue in issues)
    
    def test_extract_security_concerns(self, github_integration):
        """Test extracting security concerns from agent response"""
        content = """
        Security Analysis:
        - Found a potential security vulnerability in authentication
        - The input validation is unsafe for user data
        - No SQL injection risks detected
        - Security headers are properly configured
        """
        
        concerns = github_integration._extract_security_concerns(content)
        
        assert len(concerns) > 0
        assert any("security" in concern.lower() for concern in concerns)
        assert any("unsafe" in concern.lower() for concern in concerns)
    
    def test_format_comprehensive_review(self, github_integration):
        """Test formatting comprehensive review comment"""
        analysis = {
            "quality_score": 85,
            "issues": ["Memory leak in loop", "Missing error handling"],
            "suggestions": ["Add try-catch blocks", "Use smart pointers"],
            "security_concerns": ["Potential buffer overflow"],
            "performance_notes": ["Consider caching results"]
        }
        
        formatted_review = github_integration._format_comprehensive_review(analysis)
        
        assert "reVoAgent AI-Powered Code Review" in formatted_review
        assert "Overall Quality Score: 85/100" in formatted_review
        assert "Code Issues Detected:" in formatted_review
        assert "Security Analysis:" in formatted_review
        assert "Performance Considerations:" in formatted_review
        assert "AI Recommendations:" in formatted_review
        assert "Memory leak in loop" in formatted_review
        assert "Potential buffer overflow" in formatted_review

class TestExternalIntegrationManager:
    """Test suite for External Integration Manager"""
    
    @pytest.fixture
    def integration_manager(self):
        """Create integration manager instance"""
        from packages.integrations.external_integrations import ExternalIntegrationManager
        return ExternalIntegrationManager()
    
    def test_register_github_integration(self, integration_manager):
        """Test registering GitHub integration"""
        config = IntegrationConfig(
            name="test_github",
            type=IntegrationType.GITHUB,
            enabled=True,
            credentials={"token": "test_token"},
            settings={"organization": "test_org"}
        )
        
        integration_manager.register_integration(config)
        
        assert "test_github" in integration_manager.integrations
        assert isinstance(integration_manager.integrations["test_github"], GitHubIntegration)
    
    @pytest.mark.asyncio
    async def test_handle_webhook_routing(self, integration_manager):
        """Test webhook routing to correct integration"""
        # Register GitHub integration
        config = IntegrationConfig(
            name="test_github",
            type=IntegrationType.GITHUB,
            enabled=True,
            credentials={"token": "test_token"},
            settings={"organization": "test_org"}
        )
        integration_manager.register_integration(config)
        
        # Mock the integration's handle_webhook method
        with patch.object(integration_manager.integrations["test_github"], 'handle_webhook') as mock_handle:
            mock_handle.return_value = {"status": "processed"}
            
            headers = {"X-GitHub-Event": "pull_request"}
            payload = {"action": "opened"}
            
            result = await integration_manager.handle_webhook("test_github", headers, payload)
            
            assert result["status"] == "processed"
            mock_handle.assert_called_once_with(headers, payload)
    
    def test_get_integration_status(self, integration_manager):
        """Test getting integration status"""
        # Register multiple integrations
        github_config = IntegrationConfig(
            name="github_integration",
            type=IntegrationType.GITHUB,
            enabled=True,
            credentials={"token": "test_token"},
            settings={}
        )
        integration_manager.register_integration(github_config)
        
        status = integration_manager.get_integration_status()
        
        assert status["total_integrations"] == 1
        assert "github_integration" in status["integrations"]
        assert status["integrations"]["github_integration"]["type"] == "github"
        assert status["integrations"]["github_integration"]["enabled"] == True
    
    @pytest.mark.asyncio
    async def test_event_handler_registration(self, integration_manager):
        """Test event handler registration and emission"""
        # Register event handler
        handler_called = False
        
        async def test_handler(event):
            nonlocal handler_called
            handler_called = True
            assert event.type == EventType.PULL_REQUEST
        
        integration_manager.register_event_handler(EventType.PULL_REQUEST, test_handler)
        
        # Emit event
        event = ExternalEvent(
            id="test_event",
            type=EventType.PULL_REQUEST,
            source=IntegrationType.GITHUB,
            data={"test": "data"},
            timestamp=datetime.now(timezone.utc)
        )
        
        await integration_manager.emit_event(event)
        
        assert handler_called

if __name__ == "__main__":
    pytest.main([__file__, "-v"])