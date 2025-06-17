"""Editor tool for reVoAgent platform."""

import asyncio
from typing import Dict, Any, List
from pathlib import Path

from .base import BaseTool


class EditorTool(BaseTool):
    """
    File editor tool for reVoAgent platform.
    
    Capabilities:
    - File reading and writing
    - Code editing and modification
    - Search and replace operations
    - File creation and deletion
    - Directory operations
    """
    
    def get_description(self) -> str:
        """Get tool description."""
        return "File and code editor for reading, writing, modifying, and managing files and directories"
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema."""
        return {
            "required": ["action"],
            "optional": ["file_path", "content", "line_number", "search", "replace", "encoding"],
            "actions": [
                "read", "write", "append", "create", "delete", 
                "search", "replace", "insert", "list_dir", "mkdir"
            ]
        }
    
    def get_capabilities(self) -> List[str]:
        """Get tool capabilities."""
        return [
            "file_operations",
            "text_editing",
            "code_modification",
            "search_replace",
            "directory_management"
        ]
    
    def get_dependencies(self) -> List[str]:
        """Get tool dependencies."""
        return []  # No external dependencies
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute editor operations."""
        # Apply sandbox restrictions
        safe_params = self._apply_sandbox_restrictions(parameters)
        
        # Validate parameters
        if not self.validate_parameters(safe_params):
            raise ValueError("Invalid parameters for editor tool")
        
        action = safe_params["action"]
        
        # Execute the appropriate editor action
        if action == "read":
            return await self._read_file(safe_params)
        elif action == "write":
            return await self._write_file(safe_params)
        elif action == "append":
            return await self._append_file(safe_params)
        elif action == "create":
            return await self._create_file(safe_params)
        elif action == "delete":
            return await self._delete_file(safe_params)
        elif action == "search":
            return await self._search_file(safe_params)
        elif action == "replace":
            return await self._replace_in_file(safe_params)
        elif action == "insert":
            return await self._insert_line(safe_params)
        elif action == "list_dir":
            return await self._list_directory(safe_params)
        elif action == "mkdir":
            return await self._make_directory(safe_params)
        else:
            raise ValueError(f"Unsupported editor action: {action}")
    
    async def _read_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file."""
        file_path = parameters.get("file_path")
        if not file_path:
            raise ValueError("file_path is required for read action")
        
        encoding = parameters.get("encoding", "utf-8")
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            if not path.is_file():
                return {
                    "success": False,
                    "error": f"Path is not a file: {file_path}"
                }
            
            # Read file content
            content = path.read_text(encoding=encoding)
            
            return {
                "success": True,
                "file_path": str(path),
                "content": content,
                "size": len(content),
                "lines": len(content.split('\n')),
                "encoding": encoding,
                "message": f"Successfully read file: {file_path}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    async def _write_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to a file."""
        file_path = parameters.get("file_path")
        content = parameters.get("content", "")
        
        if not file_path:
            raise ValueError("file_path is required for write action")
        
        encoding = parameters.get("encoding", "utf-8")
        
        try:
            path = Path(file_path)
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            path.write_text(content, encoding=encoding)
            
            return {
                "success": True,
                "file_path": str(path),
                "size": len(content),
                "lines": len(content.split('\n')),
                "encoding": encoding,
                "message": f"Successfully wrote to file: {file_path}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    async def _append_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Append content to a file."""
        file_path = parameters.get("file_path")
        content = parameters.get("content", "")
        
        if not file_path:
            raise ValueError("file_path is required for append action")
        
        encoding = parameters.get("encoding", "utf-8")
        
        try:
            path = Path(file_path)
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Append content to file
            with open(path, 'a', encoding=encoding) as f:
                f.write(content)
            
            return {
                "success": True,
                "file_path": str(path),
                "appended_size": len(content),
                "encoding": encoding,
                "message": f"Successfully appended to file: {file_path}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    async def _create_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new file."""
        file_path = parameters.get("file_path")
        content = parameters.get("content", "")
        
        if not file_path:
            raise ValueError("file_path is required for create action")
        
        encoding = parameters.get("encoding", "utf-8")
        
        try:
            path = Path(file_path)
            
            if path.exists():
                return {
                    "success": False,
                    "file_path": str(path),
                    "error": f"File already exists: {file_path}"
                }
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file with content
            path.write_text(content, encoding=encoding)
            
            return {
                "success": True,
                "file_path": str(path),
                "size": len(content),
                "encoding": encoding,
                "message": f"Successfully created file: {file_path}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    async def _delete_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a file."""
        file_path = parameters.get("file_path")
        
        if not file_path:
            raise ValueError("file_path is required for delete action")
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    "success": False,
                    "file_path": str(path),
                    "error": f"File not found: {file_path}"
                }
            
            if path.is_file():
                path.unlink()
                return {
                    "success": True,
                    "file_path": str(path),
                    "message": f"Successfully deleted file: {file_path}"
                }
            else:
                return {
                    "success": False,
                    "file_path": str(path),
                    "error": f"Path is not a file: {file_path}"
                }
            
        except Exception as e:
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    async def _search_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search for text in a file."""
        file_path = parameters.get("file_path")
        search_text = parameters.get("search")
        
        if not file_path or not search_text:
            raise ValueError("file_path and search are required for search action")
        
        encoding = parameters.get("encoding", "utf-8")
        
        try:
            path = Path(file_path)
            
            if not path.exists() or not path.is_file():
                return {
                    "success": False,
                    "file_path": str(path),
                    "error": f"File not found: {file_path}"
                }
            
            # Read file and search
            content = path.read_text(encoding=encoding)
            lines = content.split('\n')
            
            matches = []
            for line_num, line in enumerate(lines, 1):
                if search_text in line:
                    matches.append({
                        "line_number": line_num,
                        "line_content": line,
                        "match_position": line.find(search_text)
                    })
            
            return {
                "success": True,
                "file_path": str(path),
                "search_text": search_text,
                "matches": matches,
                "match_count": len(matches),
                "message": f"Found {len(matches)} matches for '{search_text}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    async def _replace_in_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Replace text in a file."""
        file_path = parameters.get("file_path")
        search_text = parameters.get("search")
        replace_text = parameters.get("replace", "")
        
        if not file_path or not search_text:
            raise ValueError("file_path and search are required for replace action")
        
        encoding = parameters.get("encoding", "utf-8")
        
        try:
            path = Path(file_path)
            
            if not path.exists() or not path.is_file():
                return {
                    "success": False,
                    "file_path": str(path),
                    "error": f"File not found: {file_path}"
                }
            
            # Read file content
            content = path.read_text(encoding=encoding)
            
            # Count occurrences before replacement
            occurrence_count = content.count(search_text)
            
            # Replace text
            new_content = content.replace(search_text, replace_text)
            
            # Write back to file
            path.write_text(new_content, encoding=encoding)
            
            return {
                "success": True,
                "file_path": str(path),
                "search_text": search_text,
                "replace_text": replace_text,
                "replacements": occurrence_count,
                "message": f"Replaced {occurrence_count} occurrences of '{search_text}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    async def _insert_line(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a line at a specific position in a file."""
        file_path = parameters.get("file_path")
        content = parameters.get("content", "")
        line_number = parameters.get("line_number", 1)
        
        if not file_path:
            raise ValueError("file_path is required for insert action")
        
        encoding = parameters.get("encoding", "utf-8")
        
        try:
            path = Path(file_path)
            
            if not path.exists() or not path.is_file():
                return {
                    "success": False,
                    "file_path": str(path),
                    "error": f"File not found: {file_path}"
                }
            
            # Read file content
            file_content = path.read_text(encoding=encoding)
            lines = file_content.split('\n')
            
            # Insert line at specified position
            if line_number <= 0:
                line_number = 1
            elif line_number > len(lines):
                line_number = len(lines) + 1
            
            lines.insert(line_number - 1, content)
            
            # Write back to file
            new_content = '\n'.join(lines)
            path.write_text(new_content, encoding=encoding)
            
            return {
                "success": True,
                "file_path": str(path),
                "line_number": line_number,
                "content": content,
                "total_lines": len(lines),
                "message": f"Inserted line at position {line_number}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    async def _list_directory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """List directory contents."""
        dir_path = parameters.get("file_path", ".")
        
        try:
            path = Path(dir_path)
            
            if not path.exists():
                return {
                    "success": False,
                    "directory": str(path),
                    "error": f"Directory not found: {dir_path}"
                }
            
            if not path.is_dir():
                return {
                    "success": False,
                    "directory": str(path),
                    "error": f"Path is not a directory: {dir_path}"
                }
            
            # List directory contents
            items = []
            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "path": str(item)
                })
            
            # Sort items by type and name
            items.sort(key=lambda x: (x["type"], x["name"]))
            
            return {
                "success": True,
                "directory": str(path),
                "items": items,
                "count": len(items),
                "message": f"Listed {len(items)} items in {dir_path}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "directory": dir_path,
                "error": str(e)
            }
    
    async def _make_directory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a directory."""
        dir_path = parameters.get("file_path")
        
        if not dir_path:
            raise ValueError("file_path is required for mkdir action")
        
        try:
            path = Path(dir_path)
            
            if path.exists():
                return {
                    "success": False,
                    "directory": str(path),
                    "error": f"Directory already exists: {dir_path}"
                }
            
            # Create directory with parents
            path.mkdir(parents=True, exist_ok=False)
            
            return {
                "success": True,
                "directory": str(path),
                "message": f"Successfully created directory: {dir_path}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "directory": dir_path,
                "error": str(e)
            }
    
    async def _tool_specific_health_check(self) -> bool:
        """Check if editor tool is healthy."""
        try:
            # Test basic file operations
            test_file = Path(self.config.platform.temp_dir) / "editor_health_check.txt"
            test_content = "Health check test"
            
            # Write test file
            test_file.write_text(test_content)
            
            # Read test file
            read_content = test_file.read_text()
            
            # Clean up
            test_file.unlink()
            
            return read_content == test_content
            
        except Exception:
            return False