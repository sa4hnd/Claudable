"""
VibeKit Service for sandbox management
"""
import asyncio
import json
import httpx
from typing import Dict, Any, Optional, AsyncGenerator
from app.core.terminal_ui import ui


class VibeKitService:
    """VibeKit service for managing sandbox operations"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.bridge_url = "http://localhost:3001"
        self.sandbox_id: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout
    
    async def health_check(self) -> Dict[str, Any]:
        """Check VibeKit bridge health"""
        try:
            response = await self.client.get(f"{self.bridge_url}/api/health")
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def initialize_sandbox(self) -> str:
        """Initialize a new sandbox"""
        try:
            ui.info(f"Initializing VibeKit sandbox for project: {self.project_id}", "VibeKit")
            
            response = await self.client.post(
                f"{self.bridge_url}/api/sandbox/initialize",
                json={"projectId": self.project_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.sandbox_id = data.get("sandboxId")
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
                                    ui.info(f"VibeKit received: {data.get('type', 'unknown')} - {data.get('content', '')[:100]}...", "VibeKit")
                                    yield data
                                except json.JSONDecodeError as e:
                                    ui.warning(f"Failed to parse VibeKit data: {e}", "VibeKit")
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
                if data.get("success"):
                    ui.success("Command executed successfully", "VibeKit")
                else:
                    ui.warning(f"Command failed: {data.get('error', 'Unknown error')}", "VibeKit")
                return data
            else:
                error_msg = f"Command execution failed: {response.text}"
                ui.error(error_msg, "VibeKit")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            ui.error(f"Error executing command: {e}", "VibeKit")
            return {"success": False, "error": str(e)}
    
    async def get_host(self, port: int) -> str:
        """Get host URL for a port"""
        try:
            ui.info(f"Getting host URL for port: {port}", "VibeKit")
            
            response = await self.client.get(
                f"{self.bridge_url}/api/sandbox/host/{self.project_id}/{port}"
            )
            
            if response.status_code == 200:
                data = response.json()
                host_url = data.get("hostUrl")
                ui.success(f"Host URL: {host_url}", "VibeKit")
                return host_url
            else:
                raise Exception(f"Failed to get host URL: {response.text}")
                
        except Exception as e:
            ui.error(f"Error getting host URL: {e}", "VibeKit")
            raise
    
    async def get_session(self) -> Optional[str]:
        """Get current session ID"""
        try:
            response = await self.client.get(
                f"{self.bridge_url}/api/sandbox/session/{self.project_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("sessionId")
            else:
                return None
                
        except Exception as e:
            ui.warning(f"Error getting session: {e}", "VibeKit")
            return None
    
    async def set_session(self, session_id: str) -> None:
        """Set session ID"""
        try:
            await self.client.post(
                f"{self.bridge_url}/api/sandbox/session/{self.project_id}",
                json={"sessionId": session_id}
            )
        except Exception as e:
            ui.warning(f"Error setting session: {e}", "VibeKit")
    
    async def cleanup(self) -> None:
        """Cleanup sandbox"""
        try:
            ui.info(f"Cleaning up sandbox for project: {self.project_id}", "VibeKit")
            
            response = await self.client.delete(
                f"{self.bridge_url}/api/sandbox/{self.project_id}"
            )
            
            if response.status_code == 200:
                ui.success("Sandbox cleaned up successfully", "VibeKit")
            else:
                ui.warning(f"Cleanup warning: {response.text}", "VibeKit")
                
        except Exception as e:
            ui.error(f"Error cleaning up sandbox: {e}", "VibeKit")
        finally:
            await self.client.aclose()


# Global service instances
_vibekit_services: Dict[str, VibeKitService] = {}


def get_vibekit_service(project_id: str) -> VibeKitService:
    """Get or create VibeKit service for project"""
    if project_id not in _vibekit_services:
        _vibekit_services[project_id] = VibeKitService(project_id)
    return _vibekit_services[project_id]


async def cleanup_all_services():
    """Cleanup all VibeKit services"""
    for service in _vibekit_services.values():
        await service.cleanup()
    _vibekit_services.clear()