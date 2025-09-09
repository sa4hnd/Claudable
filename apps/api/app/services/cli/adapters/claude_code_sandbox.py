"""
Claude Code Sandbox provider implementation.
Uses VibeKit sandbox for Claude Code execution
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from app.core.terminal_ui import ui
from app.models.messages import Message
from app.services.vibekit_service import get_vibekit_service

from ..base import BaseCLI, CLIType


class ClaudeCodeSandboxCLI(BaseCLI):
    """Claude Code VibeKit Sandbox implementation"""

    def __init__(self):
        super().__init__(CLIType.CLAUDE)
        self.session_mapping: Dict[str, str] = {}

    async def check_availability(self) -> Dict[str, Any]:
        """Check if VibeKit sandbox is available"""
        try:
            # Test VibeKit bridge health
            from app.services.vibekit_service import VibeKitService
            test_service = VibeKitService("test")
            health = await test_service.health_check()
            
            if health.get("status") == "ok":
                return {
                    "available": True,
                    "configured": True,
                    "message": "VibeKit sandbox is ready"
                }
            else:
                return {
                    "available": False,
                    "configured": False,
                    "error": f"VibeKit sandbox not available: {health.get('message', 'Unknown error')}"
                }
                
        except Exception as e:
            return {
                "available": False,
                "configured": False,
                "error": f"VibeKit sandbox check failed: {str(e)}"
            }

    async def execute_with_streaming(
        self,
        instruction: str,
        project_path: str,
        session_id: Optional[str] = None,
        log_callback: Optional[Callable[[str], Any]] = None,
        images: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        is_initial_prompt: bool = False,
    ) -> AsyncGenerator[Message, None]:
        """Execute instruction using VibeKit sandbox"""

        ui.info("Starting Claude Sandbox execution", "Claude Sandbox")
        ui.debug(f"Instruction: {instruction[:100]}...", "Claude Sandbox")
        ui.debug(f"Project path: {project_path}", "Claude Sandbox")
        ui.debug(f"Session ID: {session_id}", "Claude Sandbox")

        if log_callback:
            await log_callback("Starting sandbox execution...")

        # Extract project ID from project path
        project_id = self._extract_project_id(project_path)
        if not project_id:
            ui.error("Could not extract project ID from path", "Claude Sandbox")
            yield Message(
                role="assistant",
                content="Error: Could not determine project ID",
                message_type="error"
            )
            return

        try:
            # Get VibeKit service for this project
            vibekit = get_vibekit_service(project_id)
            
            # Initialize sandbox if not already done
            if not vibekit.sandbox_id:
                await vibekit.initialize_sandbox()

            # Resume session if provided
            if session_id:
                await vibekit.set_session(session_id)

            # Load system prompt
            try:
                from app.services.claude_act import get_system_prompt
                system_prompt = get_system_prompt()
                ui.debug(f"System prompt loaded: {len(system_prompt)} chars", "Claude Sandbox")
            except Exception as e:
                ui.error(f"Failed to load system prompt: {e}", "Claude Sandbox")
                system_prompt = (
                    "You are Claude Code, an AI coding assistant specialized in building modern web applications."
                )

            # Get CLI-specific model name
            cli_model = self._get_cli_model_name(model) or "claude-sonnet-4-20250514"

            # Add project directory structure for initial prompts
            if is_initial_prompt:
                project_structure_info = """
<initial_context>
## Project Directory Structure (node_modules are already installed)
.eslintrc.json
.gitignore
next.config.mjs
next-env.d.ts
package.json
postcss.config.mjs
README.md
tailwind.config.ts
tsconfig.json
.env
src/app/favicon.ico
src/app/globals.css
src/app/layout.tsx
src/app/page.tsx
public/
node_modules/
</initial_context>"""
                instruction = instruction + project_structure_info
                ui.info("Added project structure info to initial prompt", "Claude Sandbox")

            # Build the full prompt with system context
            full_prompt = f"{system_prompt}\n\nUser Request: {instruction}"

            # Stream code generation
            async for chunk in vibekit.generate_code(full_prompt, streaming=True):
                if log_callback:
                    await log_callback(f"Received chunk: {chunk.get('type', 'unknown')}")

                if chunk.get("type") == "code_generation":
                    yield Message(
                        role="assistant",
                        content=chunk.get("content", ""),
                        message_type="code_generation",
                        metadata_json={
                            "sandbox_id": vibekit.sandbox_id,
                            "model": cli_model,
                            "session_id": session_id
                        }
                    )
                elif chunk.get("type") == "error":
                    yield Message(
                        role="assistant",
                        content=f"Error: {chunk.get('error', 'Unknown error')}",
                        message_type="error",
                        metadata_json={
                            "sandbox_id": vibekit.sandbox_id,
                            "error": chunk.get("error")
                        }
                    )
                elif chunk.get("type") == "complete":
                    # Get current session ID for resumption
                    current_session = await vibekit.get_session()
                    if current_session:
                        self.session_mapping[project_id] = current_session
                    
                    yield Message(
                        role="assistant",
                        content="Code generation completed",
                        message_type="completion",
                        metadata_json={
                            "sandbox_id": vibekit.sandbox_id,
                            "session_id": current_session
                        }
                    )

        except Exception as e:
            ui.error(f"Error in sandbox execution: {e}", "Claude Sandbox")
            yield Message(
                role="assistant",
                content=f"Error: {str(e)}",
                message_type="error",
                metadata_json={
                    "sandbox_id": getattr(vibekit, 'sandbox_id', None),
                    "error": str(e)
                }
            )

    def _extract_project_id(self, project_path: str) -> Optional[str]:
        """Extract project ID from project path"""
        try:
            # Project path format: /path/to/projects/{project_id}/repo
            parts = project_path.split(os.sep)
            if "projects" in parts:
                projects_index = parts.index("projects")
                if projects_index + 1 < len(parts):
                    return parts[projects_index + 1]
            return None
        except Exception:
            return None

    async def get_session_id(self, project_id: str) -> Optional[str]:
        """Get session ID for project"""
        return self.session_mapping.get(project_id)

    async def cleanup_session(self, project_id: str) -> None:
        """Cleanup session for project"""
        if project_id in self.session_mapping:
            del self.session_mapping[project_id]
        
        # Cleanup sandbox
        try:
            vibekit = get_vibekit_service(project_id)
            await vibekit.cleanup()
        except Exception as e:
            ui.error(f"Error cleaning up sandbox for project {project_id}: {e}", "Claude Sandbox")

