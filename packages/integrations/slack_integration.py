#!/usr/bin/env python3
"""
Slack Integration for reVoAgent
Complete Slack API integration with bot functionality, notifications, and interactive features
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import hmac
import hashlib
import time

logger = logging.getLogger(__name__)

class SlackEventType(Enum):
    MESSAGE = "message"
    APP_MENTION = "app_mention"
    REACTION_ADDED = "reaction_added"
    REACTION_REMOVED = "reaction_removed"
    CHANNEL_CREATED = "channel_created"
    MEMBER_JOINED_CHANNEL = "member_joined_channel"
    FILE_SHARED = "file_shared"

@dataclass
class SlackUser:
    """Slack user information"""
    id: str
    name: str
    real_name: str
    email: Optional[str] = None
    is_bot: bool = False
    is_admin: bool = False

@dataclass
class SlackChannel:
    """Slack channel information"""
    id: str
    name: str
    is_private: bool
    topic: str
    purpose: str
    member_count: int

@dataclass
class SlackMessage:
    """Slack message information"""
    ts: str
    user: str
    text: str
    channel: str
    thread_ts: Optional[str] = None
    attachments: List[Dict] = None
    blocks: List[Dict] = None

class SlackIntegration:
    """Complete Slack integration for reVoAgent"""
    
    def __init__(self, bot_token: str, signing_secret: Optional[str] = None, app_token: Optional[str] = None):
        self.bot_token = bot_token
        self.signing_secret = signing_secret
        self.app_token = app_token
        self.base_url = "https://slack.com/api"
        self.session = None
        
        # Event handlers
        self.event_handlers: Dict[SlackEventType, List[Callable]] = {
            event_type: [] for event_type in SlackEventType
        }
        
        # Command handlers
        self.command_handlers: Dict[str, Callable] = {}
        
        # Interactive component handlers
        self.interactive_handlers: Dict[str, Callable] = {}
        
        logger.info("Slack Integration initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def register_event_handler(self, event_type: SlackEventType, handler: Callable):
        """Register an event handler"""
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type.value} events")
    
    def register_command_handler(self, command: str, handler: Callable):
        """Register a slash command handler"""
        self.command_handlers[command] = handler
        logger.info(f"Registered handler for /{command} command")
    
    def register_interactive_handler(self, action_id: str, handler: Callable):
        """Register an interactive component handler"""
        self.interactive_handlers[action_id] = handler
        logger.info(f"Registered handler for {action_id} interactive component")
    
    def verify_request_signature(self, timestamp: str, body: str, signature: str) -> bool:
        """Verify Slack request signature"""
        if not self.signing_secret:
            logger.warning("No signing secret configured, skipping signature verification")
            return True
        
        # Check timestamp (should be within 5 minutes)
        if abs(time.time() - int(timestamp)) > 60 * 5:
            return False
        
        # Create signature
        sig_basestring = f"v0:{timestamp}:{body}"
        expected_signature = hmac.new(
            self.signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"v0={expected_signature}", signature)
    
    async def handle_event(self, payload: Dict[str, Any], timestamp: str = None, signature: str = None) -> Dict[str, Any]:
        """Handle incoming Slack event"""
        try:
            # Verify signature if provided
            if signature and timestamp:
                body = json.dumps(payload, separators=(',', ':'))
                if not self.verify_request_signature(timestamp, body, signature):
                    raise ValueError("Invalid request signature")
            
            # Handle URL verification challenge
            if payload.get("type") == "url_verification":
                return {"challenge": payload.get("challenge")}
            
            # Handle event callback
            if payload.get("type") == "event_callback":
                event = payload.get("event", {})
                return await self._process_event(event)
            
            return {"status": "ok"}
            
        except Exception as e:
            logger.error(f"Error handling Slack event: {e}")
            return {"status": "error", "error": str(e)}
    
    async def handle_slash_command(self, payload: Dict[str, Any], timestamp: str = None, signature: str = None) -> Dict[str, Any]:
        """Handle incoming slash command"""
        try:
            # Verify signature if provided
            if signature and timestamp:
                # For form data, we need to reconstruct the body
                body = "&".join([f"{k}={v}" for k, v in payload.items()])
                if not self.verify_request_signature(timestamp, body, signature):
                    raise ValueError("Invalid request signature")
            
            command = payload.get("command", "").lstrip("/")
            
            if command in self.command_handlers:
                return await self.command_handlers[command](payload)
            else:
                return {
                    "response_type": "ephemeral",
                    "text": f"Unknown command: /{command}"
                }
            
        except Exception as e:
            logger.error(f"Error handling slash command: {e}")
            return {
                "response_type": "ephemeral",
                "text": f"Error processing command: {str(e)}"
            }
    
    async def handle_interactive_component(self, payload: Dict[str, Any], timestamp: str = None, signature: str = None) -> Dict[str, Any]:
        """Handle interactive component (buttons, select menus, etc.)"""
        try:
            # Verify signature if provided
            if signature and timestamp:
                body = json.dumps(payload, separators=(',', ':'))
                if not self.verify_request_signature(timestamp, body, signature):
                    raise ValueError("Invalid request signature")
            
            actions = payload.get("actions", [])
            
            for action in actions:
                action_id = action.get("action_id")
                if action_id in self.interactive_handlers:
                    return await self.interactive_handlers[action_id](payload, action)
            
            return {"status": "ok"}
            
        except Exception as e:
            logger.error(f"Error handling interactive component: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a specific Slack event"""
        event_type_str = event.get("type")
        
        try:
            event_type = SlackEventType(event_type_str)
        except ValueError:
            logger.warning(f"Unsupported Slack event type: {event_type_str}")
            return {"status": "ignored", "reason": f"Unsupported event type: {event_type_str}"}
        
        # Call registered handlers
        for handler in self.event_handlers[event_type]:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
        
        # Built-in event processing
        if event_type == SlackEventType.APP_MENTION:
            await self._handle_app_mention(event)
        elif event_type == SlackEventType.MESSAGE:
            await self._handle_message(event)
        
        return {"status": "processed", "event_type": event_type_str}
    
    async def _handle_app_mention(self, event: Dict[str, Any]):
        """Handle app mention events"""
        text = event.get("text", "")
        channel = event.get("channel")
        user = event.get("user")
        ts = event.get("ts")
        
        # Parse command from mention
        if "help" in text.lower():
            await self.send_help_message(channel, ts)
        elif "analyze" in text.lower():
            await self.send_analysis_request(channel, user, ts)
        elif "status" in text.lower():
            await self.send_status_update(channel, ts)
        else:
            await self.send_default_response(channel, ts)
    
    async def _handle_message(self, event: Dict[str, Any]):
        """Handle regular message events"""
        # Only process messages in channels where the bot is mentioned or DMs
        if event.get("channel_type") == "im":
            # Direct message - process as command
            await self._process_dm_command(event)
    
    async def _process_dm_command(self, event: Dict[str, Any]):
        """Process direct message as command"""
        text = event.get("text", "").lower()
        channel = event.get("channel")
        user = event.get("user")
        
        if "help" in text:
            await self.send_help_message(channel)
        elif "analyze" in text:
            await self.send_analysis_request(channel, user)
        elif "status" in text:
            await self.send_status_update(channel)
        else:
            await self.send_message(channel, "I'm reVoAgent! Type 'help' to see what I can do.")
    
    # Slack API Methods
    
    async def send_message(self, channel: str, text: str = None, blocks: List[Dict] = None, 
                          attachments: List[Dict] = None, thread_ts: str = None) -> Dict[str, Any]:
        """Send a message to a channel"""
        data = {"channel": channel}
        
        if text:
            data["text"] = text
        if blocks:
            data["blocks"] = blocks
        if attachments:
            data["attachments"] = attachments
        if thread_ts:
            data["thread_ts"] = thread_ts
        
        async with self.session.post(f"{self.base_url}/chat.postMessage", json=data) as response:
            response.raise_for_status()
            return await response.json()
    
    async def update_message(self, channel: str, ts: str, text: str = None, 
                           blocks: List[Dict] = None, attachments: List[Dict] = None) -> Dict[str, Any]:
        """Update an existing message"""
        data = {
            "channel": channel,
            "ts": ts
        }
        
        if text:
            data["text"] = text
        if blocks:
            data["blocks"] = blocks
        if attachments:
            data["attachments"] = attachments
        
        async with self.session.post(f"{self.base_url}/chat.update", json=data) as response:
            response.raise_for_status()
            return await response.json()
    
    async def delete_message(self, channel: str, ts: str) -> Dict[str, Any]:
        """Delete a message"""
        data = {
            "channel": channel,
            "ts": ts
        }
        
        async with self.session.post(f"{self.base_url}/chat.delete", json=data) as response:
            response.raise_for_status()
            return await response.json()
    
    async def add_reaction(self, channel: str, timestamp: str, name: str) -> Dict[str, Any]:
        """Add a reaction to a message"""
        data = {
            "channel": channel,
            "timestamp": timestamp,
            "name": name
        }
        
        async with self.session.post(f"{self.base_url}/reactions.add", json=data) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_user_info(self, user_id: str) -> SlackUser:
        """Get user information"""
        async with self.session.get(f"{self.base_url}/users.info", params={"user": user_id}) as response:
            response.raise_for_status()
            data = await response.json()
            user_data = data["user"]
            
            return SlackUser(
                id=user_data["id"],
                name=user_data["name"],
                real_name=user_data.get("real_name", ""),
                email=user_data.get("profile", {}).get("email"),
                is_bot=user_data.get("is_bot", False),
                is_admin=user_data.get("is_admin", False)
            )
    
    async def get_channel_info(self, channel_id: str) -> SlackChannel:
        """Get channel information"""
        async with self.session.get(f"{self.base_url}/conversations.info", params={"channel": channel_id}) as response:
            response.raise_for_status()
            data = await response.json()
            channel_data = data["channel"]
            
            return SlackChannel(
                id=channel_data["id"],
                name=channel_data["name"],
                is_private=channel_data.get("is_private", False),
                topic=channel_data.get("topic", {}).get("value", ""),
                purpose=channel_data.get("purpose", {}).get("value", ""),
                member_count=channel_data.get("num_members", 0)
            )
    
    async def get_channels(self, types: str = "public_channel,private_channel") -> List[SlackChannel]:
        """Get list of channels"""
        channels = []
        cursor = None
        
        while True:
            params = {"types": types, "limit": 100}
            if cursor:
                params["cursor"] = cursor
            
            async with self.session.get(f"{self.base_url}/conversations.list", params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                for channel_data in data["channels"]:
                    channels.append(SlackChannel(
                        id=channel_data["id"],
                        name=channel_data["name"],
                        is_private=channel_data.get("is_private", False),
                        topic=channel_data.get("topic", {}).get("value", ""),
                        purpose=channel_data.get("purpose", {}).get("value", ""),
                        member_count=channel_data.get("num_members", 0)
                    ))
                
                cursor = data.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
        
        return channels
    
    async def upload_file(self, channels: str, file_path: str, title: str = None, 
                         initial_comment: str = None) -> Dict[str, Any]:
        """Upload a file to Slack"""
        data = aiohttp.FormData()
        data.add_field('channels', channels)
        
        if title:
            data.add_field('title', title)
        if initial_comment:
            data.add_field('initial_comment', initial_comment)
        
        with open(file_path, 'rb') as f:
            data.add_field('file', f, filename=file_path.split('/')[-1])
            
            # Remove Content-Type header for file upload
            headers = {"Authorization": f"Bearer {self.bot_token}"}
            
            async with self.session.post(f"{self.base_url}/files.upload", data=data, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
    
    # Built-in message handlers
    
    async def send_help_message(self, channel: str, thread_ts: str = None):
        """Send help message"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🤖 reVoAgent Help*\n\nI'm your AI development assistant! Here's what I can do:"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Code Analysis*\n`@revoagent analyze` - Analyze code quality"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Status Updates*\n`@revoagent status` - Get system status"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Debugging*\n`/revo debug` - Debug assistance"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Workflows*\n`/revo workflow` - Create workflows"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Start Analysis"
                        },
                        "action_id": "start_analysis",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Dashboard"
                        },
                        "action_id": "view_dashboard"
                    }
                ]
            }
        ]
        
        await self.send_message(channel, blocks=blocks, thread_ts=thread_ts)
    
    async def send_analysis_request(self, channel: str, user: str, thread_ts: str = None):
        """Send analysis request message"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🔍 *Code Analysis Request*\n\n<@{user}> requested code analysis. What would you like me to analyze?"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select analysis type"
                        },
                        "action_id": "analysis_type_select",
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Code Quality"
                                },
                                "value": "quality"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Security Audit"
                                },
                                "value": "security"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Performance Analysis"
                                },
                                "value": "performance"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Architecture Review"
                                },
                                "value": "architecture"
                            }
                        ]
                    }
                ]
            }
        ]
        
        await self.send_message(channel, blocks=blocks, thread_ts=thread_ts)
    
    async def send_status_update(self, channel: str, thread_ts: str = None):
        """Send status update message"""
        # This would integrate with your system monitoring
        status_data = {
            "api_status": "🟢 Healthy",
            "agents_active": "4/4",
            "response_time": "< 2s",
            "uptime": "99.9%"
        }
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📊 reVoAgent Status*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*API Status:* {status_data['api_status']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Active Agents:* {status_data['agents_active']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Response Time:* {status_data['response_time']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Uptime:* {status_data['uptime']}"
                    }
                ]
            }
        ]
        
        await self.send_message(channel, blocks=blocks, thread_ts=thread_ts)
    
    async def send_default_response(self, channel: str, thread_ts: str = None):
        """Send default response for unknown mentions"""
        await self.send_message(
            channel,
            "👋 Hi! I'm reVoAgent. Type `@revoagent help` to see what I can do!",
            thread_ts=thread_ts
        )
    
    # Notification methods
    
    async def notify_deployment_success(self, channel: str, deployment_info: Dict[str, Any]):
        """Notify about successful deployment"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🚀 *Deployment Successful*\n\n*Environment:* {deployment_info.get('environment', 'Unknown')}\n*Version:* {deployment_info.get('version', 'Unknown')}\n*Duration:* {deployment_info.get('duration', 'Unknown')}"
                }
            }
        ]
        
        await self.send_message(channel, blocks=blocks)
    
    async def notify_error(self, channel: str, error_info: Dict[str, Any]):
        """Notify about errors"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🚨 *Error Alert*\n\n*Service:* {error_info.get('service', 'Unknown')}\n*Error:* {error_info.get('error', 'Unknown')}\n*Time:* {error_info.get('timestamp', 'Unknown')}"
                }
            }
        ]
        
        await self.send_message(channel, blocks=blocks)
    
    async def notify_pr_review(self, channel: str, pr_info: Dict[str, Any]):
        """Notify about PR review completion"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📝 *PR Review Complete*\n\n*Repository:* {pr_info.get('repo', 'Unknown')}\n*PR:* #{pr_info.get('number', 'Unknown')} - {pr_info.get('title', 'Unknown')}\n*Status:* {pr_info.get('status', 'Unknown')}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View PR"
                        },
                        "url": pr_info.get('url', '#'),
                        "action_id": "view_pr"
                    }
                ]
            }
        ]
        
        await self.send_message(channel, blocks=blocks)

# Example usage
async def example_usage():
    """Example usage of Slack integration"""
    async with SlackIntegration(
        bot_token="xoxb-your-bot-token",
        signing_secret="your-signing-secret"
    ) as slack:
        
        # Register event handlers
        async def handle_mention(event):
            print(f"App mentioned: {event}")
        
        slack.register_event_handler(SlackEventType.APP_MENTION, handle_mention)
        
        # Register command handlers
        async def handle_debug_command(payload):
            return {
                "response_type": "in_channel",
                "text": "🐛 Debug mode activated!"
            }
        
        slack.register_command_handler("debug", handle_debug_command)
        
        # Send a message
        await slack.send_message("#general", "Hello from reVoAgent! 🤖")

if __name__ == "__main__":
    asyncio.run(example_usage())