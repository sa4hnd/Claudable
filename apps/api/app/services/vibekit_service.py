"""
VibeKit Service
Handles communication with VibeKit Node.js bridge for sandbox operations
"""
import asyncio
import os
import httpx
import json
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from app.core.terminal_ui import ui


class VibeKitService:
    """VibeKit service for sandbox operations"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id
        self.bridge_url = os.getenv("VIBEKIT_BRIDGE_URL", "http://localhost:3001")
        self.sandbox_id = None
        self.session_id = None
        self.client = httpx.AsyncClient(timeout=600.0)  # 10 minutes for long-running commands
    
    async def initialize_sandbox(self) -> str:
        """Initialize E2B sandbox and return sandbox ID"""
        try:
            ui.info(f"Initializing VibeKit sandbox for project: {self.project_id}", "VibeKit")
            
            response = await self.client.post(
                f"{self.bridge_url}/api/sandbox/initialize",
                json={"projectId": self.project_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.sandbox_id = data["sandboxId"]
                ui.success(f"Sandbox initialized: {self.sandbox_id}", "VibeKit")
                return self.sandbox_id
            else:
                error_msg = f"Failed to initialize sandbox: {response.text}"
                ui.error(error_msg, "VibeKit")
                raise Exception(error_msg)
                
        except Exception as e:
            ui.error(f"Error initializing sandbox: {e}", "VibeKit")
            raise
    
    async def generate_code(self, prompt: str, streaming: bool = True) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate code using VibeKit Claude Code agent"""
        try:
            ui.info(f"Generating code with prompt: {prompt[:100]}...", "VibeKit")
            
            if streaming:
                # For streaming, we'll use Server-Sent Events
                async with self.client.stream(
                    "POST",
                    f"{self.bridge_url}/api/sandbox/generate-code",
                    json={
                        "projectId": self.project_id,
                        "prompt": prompt,
                        "streaming": True
                    },
                    headers={"Accept": "text/event-stream"}
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])  # Remove "data: " prefix
                                    yield data
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.aread()
                        raise Exception(f"Code generation failed: {error_text.decode()}")
            else:
                response = await self.client.post(
                    f"{self.bridge_url}/api/sandbox/generate-code",
                    json={
                        "projectId": self.project_id,
                        "prompt": prompt,
                        "streaming": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    yield {"type": "code_generation", "content": data["code"]}
                else:
                    raise Exception(f"Code generation failed: {response.text}")
                    
        except Exception as e:
            ui.error(f"Error generating code: {e}", "VibeKit")
            yield {"type": "error", "error": str(e)}
    
    async def execute_command(self, command: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute command in sandbox"""
        try:
            ui.info(f"Executing command: {command}", "VibeKit")
            
            response = await self.client.post(
                f"{self.bridge_url}/api/sandbox/execute-command",
                json={
                    "projectId": self.project_id,
                    "command": command,
                    "options": options or {}
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                ui.success(f"Command executed successfully", "VibeKit")
                return data
            else:
                error_msg = f"Command execution failed: {response.text}"
                ui.error(error_msg, "VibeKit")
                raise Exception(error_msg)
                
        except Exception as e:
            ui.error(f"Error executing command: {e}", "VibeKit")
            raise
    
    async def get_host(self, port: int) -> str:
        """Get host URL for sandbox port"""
        try:
            ui.info(f"Getting host URL for port: {port}", "VibeKit")
            
            response = await self.client.get(
                f"{self.bridge_url}/api/sandbox/host/{self.project_id}/{port}"
            )
            
            if response.status_code == 200:
                data = response.json()
                host_url = data["hostUrl"]
                ui.success(f"Host URL: {host_url}", "VibeKit")
                return host_url
            else:
                error_msg = f"Failed to get host URL: {response.text}"
                ui.error(error_msg, "VibeKit")
                raise Exception(error_msg)
                
        except Exception as e:
            ui.error(f"Error getting host URL: {e}", "VibeKit")
            raise
    
    async def get_session(self) -> str:
        """Get current VibeKit session"""
        try:
            response = await self.client.get(
                f"{self.bridge_url}/api/sandbox/session/{self.project_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data["session"]
                return self.session_id
            else:
                raise Exception(f"Failed to get session: {response.text}")
                
        except Exception as e:
            ui.error(f"Error getting session: {e}", "VibeKit")
            raise
    
    async def set_session(self, session_id: str) -> None:
        """Set VibeKit session"""
        try:
            response = await self.client.post(
                f"{self.bridge_url}/api/sandbox/session/{self.project_id}",
                json={"sessionId": session_id}
            )
            
            if response.status_code == 200:
                self.session_id = session_id
                ui.success(f"Session set: {session_id}", "VibeKit")
            else:
                raise Exception(f"Failed to set session: {response.text}")
                
        except Exception as e:
            ui.error(f"Error setting session: {e}", "VibeKit")
            raise
    
    async def cleanup(self) -> None:
        """Cleanup sandbox resources"""
        try:
            ui.info(f"Cleaning up sandbox for project: {self.project_id}", "VibeKit")
            
            response = await self.client.delete(
                f"{self.bridge_url}/api/sandbox/{self.project_id}"
            )
            
            if response.status_code == 200:
                ui.success("Sandbox cleaned up successfully", "VibeKit")
            else:
                ui.warning(f"Sandbox cleanup warning: {response.text}", "VibeKit")
                
        except Exception as e:
            ui.error(f"Error cleaning up sandbox: {e}", "VibeKit")
        finally:
            await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check VibeKit bridge health"""
        try:
            response = await self.client.get(f"{self.bridge_url}/api/health")
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": response.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Global VibeKit service instances cache
_vibekit_services = {}


def get_vibekit_service(project_id: str) -> VibeKitService:
    """Get or create VibeKit service for project"""
    if project_id not in _vibekit_services:
        _vibekit_services[project_id] = VibeKitService(project_id)
    return _vibekit_services[project_id]


async def cleanup_all_sandboxes():
    """Cleanup all active sandboxes"""
    for project_id, service in _vibekit_services.items():
        try:
            await service.cleanup()
        except Exception as e:
            ui.error(f"Error cleaning up sandbox for project {project_id}: {e}", "VibeKit")
    _vibekit_services.clear()

