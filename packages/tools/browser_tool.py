"""Browser automation tool for reVoAgent platform."""

import asyncio
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .base import BaseTool


class BrowserTool(BaseTool):
    """
    Browser automation tool using Playwright.
    
    Capabilities:
    - Web page navigation
    - Element interaction (click, fill, etc.)
    - Data extraction
    - Screenshot capture
    - Form automation
    """
    
    def _initialize(self) -> None:
        """Initialize browser tool."""
        super()._initialize()
        self.browser = None
        self.page = None
        self.context = None
    
    def get_description(self) -> str:
        """Get tool description."""
        return "Browser automation for web navigation, interaction, data extraction, and testing"
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema."""
        return {
            "required": ["action"],
            "optional": ["url", "selector", "text", "filename", "timeout", "wait_for"],
            "actions": [
                "navigate", "click", "fill", "extract", "screenshot", 
                "wait", "scroll", "select", "submit", "get_text"
            ]
        }
    
    def get_capabilities(self) -> List[str]:
        """Get tool capabilities."""
        return [
            "web_navigation",
            "element_interaction", 
            "data_extraction",
            "screenshot_capture",
            "form_automation",
            "web_testing"
        ]
    
    def get_dependencies(self) -> List[str]:
        """Get tool dependencies."""
        return ["playwright", "playwright-python"]
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute browser automation."""
        # Apply sandbox restrictions
        safe_params = self._apply_sandbox_restrictions(parameters)
        
        # Validate parameters
        if not self.validate_parameters(safe_params):
            raise ValueError("Invalid parameters for browser tool")
        
        action = safe_params["action"]
        
        # Initialize browser if needed
        if not self.browser:
            await self._initialize_browser()
        
        try:
            # Execute the appropriate browser action
            if action == "navigate":
                return await self._navigate(safe_params)
            elif action == "click":
                return await self._click(safe_params)
            elif action == "fill":
                return await self._fill(safe_params)
            elif action == "extract":
                return await self._extract(safe_params)
            elif action == "screenshot":
                return await self._screenshot(safe_params)
            elif action == "wait":
                return await self._wait(safe_params)
            elif action == "scroll":
                return await self._scroll(safe_params)
            elif action == "get_text":
                return await self._get_text(safe_params)
            else:
                raise ValueError(f"Unsupported browser action: {action}")
                
        except Exception as e:
            self.logger.error(f"Browser action failed: {e}")
            # Try to recover by reinitializing browser
            await self._cleanup_browser()
            raise
    
    async def _initialize_browser(self) -> None:
        """Initialize browser instance."""
        try:
            # Try to import playwright
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                self.logger.warning("Playwright not installed, attempting to install...")
                await self._install_dependency("playwright")
                # Install browser binaries
                await self._install_playwright_browsers()
                from playwright.async_api import async_playwright
            
            # Launch browser
            self.playwright = await async_playwright().start()
            
            # Use headless mode in sandbox
            headless = self.sandbox_enabled
            
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=['--no-sandbox', '--disable-dev-shm-usage'] if self.sandbox_enabled else []
            )
            
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='reVoAgent/1.0.0 Browser Automation'
            )
            
            self.page = await self.context.new_page()
            
            self.logger.info("Browser initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def _install_playwright_browsers(self) -> None:
        """Install Playwright browser binaries."""
        try:
            process = await asyncio.create_subprocess_exec(
                "playwright", "install", "chromium",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.warning(f"Failed to install Playwright browsers: {stderr.decode()}")
            else:
                self.logger.info("Playwright browsers installed successfully")
                
        except Exception as e:
            self.logger.warning(f"Error installing Playwright browsers: {e}")
    
    async def _navigate(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL."""
        url = parameters.get("url")
        if not url:
            raise ValueError("URL is required for navigation")
        
        # Validate URL in sandbox mode
        if self.sandbox_enabled and not self._is_url_allowed(url):
            raise ValueError(f"URL not allowed in sandbox mode: {url}")
        
        timeout = parameters.get("timeout", 30000)
        
        try:
            response = await self.page.goto(url, timeout=timeout)
            
            return {
                "success": True,
                "url": url,
                "status": response.status if response else None,
                "title": await self.page.title(),
                "message": f"Successfully navigated to {url}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    async def _click(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Click an element."""
        selector = parameters.get("selector")
        if not selector:
            raise ValueError("Selector is required for click action")
        
        timeout = parameters.get("timeout", 10000)
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.click(selector)
            
            return {
                "success": True,
                "selector": selector,
                "message": f"Successfully clicked element: {selector}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "selector": selector,
                "error": str(e)
            }
    
    async def _fill(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fill an input element."""
        selector = parameters.get("selector")
        text = parameters.get("text", "")
        
        if not selector:
            raise ValueError("Selector is required for fill action")
        
        timeout = parameters.get("timeout", 10000)
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.fill(selector, text)
            
            return {
                "success": True,
                "selector": selector,
                "text": text,
                "message": f"Successfully filled element: {selector}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "selector": selector,
                "error": str(e)
            }
    
    async def _extract(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from elements."""
        selector = parameters.get("selector")
        if not selector:
            raise ValueError("Selector is required for extract action")
        
        attribute = parameters.get("attribute", "textContent")
        timeout = parameters.get("timeout", 10000)
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            
            # Extract data from all matching elements
            elements = await self.page.query_selector_all(selector)
            extracted_data = []
            
            for element in elements:
                if attribute == "textContent":
                    data = await element.text_content()
                elif attribute == "innerHTML":
                    data = await element.inner_html()
                elif attribute == "outerHTML":
                    data = await element.inner_html()  # Playwright doesn't have outerHTML
                else:
                    data = await element.get_attribute(attribute)
                
                extracted_data.append(data)
            
            return {
                "success": True,
                "selector": selector,
                "attribute": attribute,
                "data": extracted_data,
                "count": len(extracted_data),
                "message": f"Extracted {len(extracted_data)} items from {selector}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "selector": selector,
                "error": str(e)
            }
    
    async def _screenshot(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot."""
        filename = parameters.get("filename", "screenshot.png")
        full_page = parameters.get("full_page", False)
        
        # Ensure screenshots directory exists
        screenshots_dir = Path(self.config.platform.temp_dir) / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = screenshots_dir / filename
        
        try:
            await self.page.screenshot(
                path=str(filepath),
                full_page=full_page
            )
            
            return {
                "success": True,
                "filename": filename,
                "filepath": str(filepath),
                "full_page": full_page,
                "message": f"Screenshot saved to {filepath}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "filename": filename,
                "error": str(e)
            }
    
    async def _wait(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for an element or condition."""
        selector = parameters.get("selector")
        timeout = parameters.get("timeout", 10000)
        
        if selector:
            try:
                await self.page.wait_for_selector(selector, timeout=timeout)
                return {
                    "success": True,
                    "selector": selector,
                    "message": f"Element appeared: {selector}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "selector": selector,
                    "error": str(e)
                }
        else:
            # Wait for page load
            try:
                await self.page.wait_for_load_state("networkidle", timeout=timeout)
                return {
                    "success": True,
                    "message": "Page loaded successfully"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def _scroll(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Scroll the page."""
        direction = parameters.get("direction", "down")
        amount = parameters.get("amount", 500)
        
        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            elif direction == "top":
                await self.page.evaluate("window.scrollTo(0, 0)")
            elif direction == "bottom":
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            return {
                "success": True,
                "direction": direction,
                "amount": amount,
                "message": f"Scrolled {direction}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "direction": direction,
                "error": str(e)
            }
    
    async def _get_text(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get text content from an element."""
        selector = parameters.get("selector", "body")
        timeout = parameters.get("timeout", 10000)
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            text = await self.page.text_content(selector)
            
            return {
                "success": True,
                "selector": selector,
                "text": text,
                "length": len(text) if text else 0,
                "message": f"Retrieved text from {selector}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "selector": selector,
                "error": str(e)
            }
    
    def _is_url_allowed(self, url: str) -> bool:
        """Check if URL is allowed in sandbox mode."""
        if not self.sandbox_enabled:
            return True
        
        # Allow localhost and common development URLs
        allowed_patterns = [
            "http://localhost",
            "http://127.0.0.1",
            "https://github.com",
            "https://stackoverflow.com",
            "https://docs.python.org"
        ]
        
        return any(url.startswith(pattern) for pattern in allowed_patterns)
    
    async def _cleanup_browser(self) -> None:
        """Cleanup browser resources."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
        except Exception as e:
            self.logger.error(f"Error cleaning up browser: {e}")
    
    async def _tool_specific_health_check(self) -> bool:
        """Check if browser tool is healthy."""
        try:
            if not self.browser:
                await self._initialize_browser()
            
            # Simple health check - navigate to a test page
            if self.page:
                await self.page.goto("data:text/html,<html><body>Health Check</body></html>")
                return True
            
            return False
            
        except Exception:
            return False
    
    def cleanup(self) -> None:
        """Cleanup browser tool resources."""
        super().cleanup()
        # Schedule browser cleanup
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.create_task(self._cleanup_browser())
        except:
            pass