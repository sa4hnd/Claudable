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
        self.session_id: Optional[str] = None

    def set_session_id(self, session_id: str) -> None:
        """Set session ID for the CLI"""
        self.session_id = session_id

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

        # Extract project ID from project path or get from database
        project_id = self._extract_project_id(project_path)
        if not project_id:
            # Try to get project ID from database using session_id
            try:
                from app.models.projects import Project
                from app.db.session import get_db
                db_session = next(get_db())
                # Look for project with this session_id in any of the session fields
                project = db_session.query(Project).filter(
                    (Project.active_claude_session_id == session_id) |
                    (Project.active_cursor_session_id == session_id)
                ).first()
                if project:
                    project_id = project.id
                    ui.info(f"Found project ID from database: {project_id}", "Claude Sandbox")
                else:
                    # Fallback to using session_id as project_id
                    project_id = session_id.split('-')[0] if '-' in session_id else session_id
                    ui.warning(f"Using session_id as project_id: {project_id}", "Claude Sandbox")
            except Exception as e:
                ui.warning(f"Could not get project from database: {e}", "Claude Sandbox")
                project_id = session_id.split('-')[0] if '-' in session_id else session_id
                ui.warning(f"Using session_id as project_id: {project_id}", "Claude Sandbox")
        
        if not project_id:
            ui.error("Could not extract project ID from path or session", "Claude Sandbox")
            yield Message(
                id=str(uuid.uuid4()),
                project_id="unknown",
                role="assistant",
                content="Error: Could not determine project ID",
                message_type="error",
                metadata_json={"cli_type": "claude"},
                session_id=session_id,
                created_at=datetime.utcnow()
            )
            return

        # Get CLI-specific model name first
        cli_model = self._get_cli_model_name(model) or "claude-sonnet-4-20250514"

        try:
            # Get VibeKit service for this project
            vibekit = get_vibekit_service(project_id)
            
            # Initialize sandbox if not already done
            if not vibekit.sandbox_id:
                # Show sandbox initialization status
                yield Message(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    role="assistant",
                    content="🌐 **Initializing sandbox environment...**",
                    message_type="info",
                    metadata_json={
                        "sandbox_id": None,  # Not yet initialized
                        "model": cli_model,
                        "session_id": session_id,
                        "cli_type": "claude",
                        "event_type": "sandbox_initialization"
                    },
                    session_id=session_id,
                    created_at=datetime.utcnow()
                )
                
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

        except Exception as e:
            ui.error(f"Error in sandbox setup: {e}", "Claude Sandbox")
            yield Message(
                id=str(uuid.uuid4()),
                project_id=project_id,
                role="assistant",
                content=f"Error: {str(e)}",
                message_type="error",
                metadata_json={
                    "sandbox_id": None,
                    "error": str(e),
                    "cli_type": "claude"
                },
                session_id=session_id,
                created_at=datetime.utcnow()
            )
            return

        # For initial prompts, we need to create the Next.js project first (like your test script)
        if is_initial_prompt:
            ui.info("Initial prompt detected - creating Next.js project first", "Claude Sandbox")
            
            # Show sandbox initialization status
            yield Message(
                id=str(uuid.uuid4()),
                project_id=project_id,
                role="assistant",
                content="🚀 **Opening sandbox environment...**",
                message_type="info",
                metadata_json={
                    "sandbox_id": vibekit.sandbox_id,
                    "model": cli_model,
                    "session_id": session_id,
                    "cli_type": "claude",
                    "event_type": "sandbox_init"
                },
                session_id=session_id,
                created_at=datetime.utcnow()
            )
            
            # Create Next.js project in /vibe0 (like your test script)
            app_name = f"my-app-{project_id}"
            ui.info(f"Creating Next.js project '{app_name}' in /vibe0", "Claude Sandbox")
            
            # Show project creation status
            yield Message(
                id=str(uuid.uuid4()),
                project_id=project_id,
                role="assistant",
                content="📦 **Creating Next.js project...**",
                message_type="info",
                metadata_json={
                    "sandbox_id": vibekit.sandbox_id,
                    "model": cli_model,
                    "session_id": session_id,
                    "cli_type": "claude",
                    "event_type": "project_creation"
                },
                session_id=session_id,
                created_at=datetime.utcnow()
            )
            
            # Clean up any existing directories
            await vibekit.execute_command("cd /vibe0 && rm -rf my-app*")
            
            # Create Next.js project
            create_cmd = [
                "npx", "create-next-app@latest", app_name,
                "--typescript", "--tailwind", "--eslint", "--app",
                "--import-alias", "@/*", "--use-npm", "--yes"
            ]
            
            result = await vibekit.execute_command(f"cd /vibe0 && {' '.join(create_cmd)}")
            if not result.get("success"):
                raise Exception(f"Failed to create Next.js project: {result}")
            
            # Navigate to project directory
            project_dir = f"/vibe0/{app_name}"
            await vibekit.execute_command(f"cd {project_dir} && pwd")
            
            # Show git setup status
            yield Message(
                id=str(uuid.uuid4()),
                project_id=project_id,
                role="assistant",
                content="🔧 **Setting up git repository...**",
                message_type="info",
                metadata_json={
                    "sandbox_id": vibekit.sandbox_id,
                    "model": cli_model,
                    "session_id": session_id,
                    "cli_type": "claude",
                    "event_type": "git_setup"
                },
                session_id=session_id,
                created_at=datetime.utcnow()
            )
            
            # Create .env file
            env_content = f"NEXT_PUBLIC_PROJECT_ID={project_id}\nNEXT_PUBLIC_PROJECT_NAME=Claudable Project"
            await vibekit.execute_command(f"cd {project_dir} && echo '{env_content}' > .env")
            
            # Initialize git repository
            await vibekit.execute_command(f"cd {project_dir} && git config --global user.email 'shexhtc@gmail.com' && git config --global user.name 'sa4hnd'")
            await vibekit.execute_command(f"cd {project_dir} && git init")
            await vibekit.execute_command(f"cd {project_dir} && git add .")
            await vibekit.execute_command(f"cd {project_dir} && git commit -m 'Initial commit'")
            
            # Show dev server startup status
            yield Message(
                id=str(uuid.uuid4()),
                project_id=project_id,
                role="assistant",
                content="⚡ **Starting development server...**",
                message_type="info",
                metadata_json={
                    "sandbox_id": vibekit.sandbox_id,
                    "model": cli_model,
                    "session_id": session_id,
                    "cli_type": "claude",
                    "event_type": "dev_server_start"
                },
                session_id=session_id,
                created_at=datetime.utcnow()
            )
            
            # Start development server in background (like your test script)
            ui.info("Starting development server in background", "Claude Sandbox")
            dev_result = await vibekit.execute_command(f"cd {project_dir} && npm run dev -- --port 3000", {"background": True})
            if not dev_result.get("success"):
                ui.warning(f"Dev server failed to start: {dev_result}", "Claude Sandbox")
            else:
                ui.info("Development server started in background", "Claude Sandbox")
            
            # Get preview URL (like your test script)
            host_url = await vibekit.get_host(3000)
            ui.info(f"Preview URL: {host_url}", "Claude Sandbox")
            
            # Show completion status
            yield Message(
                id=str(uuid.uuid4()),
                project_id=project_id,
                role="assistant",
                content=f"✅ **Project ready!** Preview: {host_url}",
                message_type="info",
                metadata_json={
                    "sandbox_id": vibekit.sandbox_id,
                    "model": cli_model,
                    "session_id": session_id,
                    "cli_type": "claude",
                    "event_type": "project_ready",
                    "preview_url": host_url
                },
                session_id=session_id,
                created_at=datetime.utcnow()
            )
            
            # Update the instruction to work in the project directory
            instruction = f"Working in directory: {project_dir}\n\n{instruction}"
            ui.info(f"Next.js project created and ready at {project_dir}", "Claude Sandbox")

            # Build the full prompt with system context
            full_prompt = f"{system_prompt}\n\nUser Request: {instruction}"

            # Stream code generation
            async for chunk in vibekit.generate_code(full_prompt, streaming=True):
                ui.debug(f"Claude Sandbox received chunk: {chunk}", "Claude Sandbox")
                if log_callback:
                    await log_callback(f"Received chunk: {chunk.get('type', 'unknown')}")

                if chunk.get("type") == "update":
                    # Handle streaming updates from Claude - use "chat" message type like other CLIs
                    content = chunk.get("content", "")
                    ui.debug(f"Claude Sandbox update content: '{content}'", "Claude Sandbox")
                    if content:
                        yield Message(
                            id=str(uuid.uuid4()),
                            project_id=project_id,
                            role="assistant",
                            content=content,
                            message_type="chat",
                            metadata_json={
                                "sandbox_id": vibekit.sandbox_id,
                                "model": cli_model,
                                "session_id": session_id,
                                "cli_type": "claude",
                                "event_type": "streaming_update"
                            },
                            session_id=session_id,
                            created_at=datetime.utcnow()
                        )
                elif chunk.get("type") == "tool_use":
                    # Handle tool usage messages - show what Claude is doing
                    content = chunk.get("content", "")
                    tool_name = chunk.get("tool_name", "Unknown Tool")
                    tool_input = chunk.get("tool_input", {})
                    tool_id = chunk.get("tool_id", "")
                    
                    ui.debug(f"Claude Sandbox tool usage: {tool_name} - {content}", "Claude Sandbox")
                    if content:
                        yield Message(
                            id=str(uuid.uuid4()),
                            project_id=project_id,
                            role="assistant",
                            content=content,
                            message_type="tool_use",
                            metadata_json={
                                "sandbox_id": vibekit.sandbox_id,
                                "model": cli_model,
                                "session_id": session_id,
                                "cli_type": "claude",
                                "event_type": "tool_usage",
                                "tool_name": tool_name,
                                "tool_input": tool_input,
                                "tool_id": tool_id
                            },
                            session_id=session_id,
                            created_at=datetime.utcnow()
                        )
                elif chunk.get("type") == "todo_list":
                    # Handle todo list messages - display structured todo list
                    content = chunk.get("content", "")
                    tool_name = chunk.get("tool_name", "TodoWrite")
                    tool_input = chunk.get("tool_input", {})
                    tool_id = chunk.get("tool_id", "")
                    
                    # Determine if this is an update based on tool input or existing todos
                    is_update = tool_input.get("isUpdate", False) or "update" in str(tool_input).lower()
                    
                    ui.info(f"Todo list {'updated' if is_update else 'generated'}: {tool_name}", "Claude Sandbox")
                    yield Message(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        role="assistant",
                        content=content,
                        message_type="todo_list",
                        metadata_json={
                            "sandbox_id": vibekit.sandbox_id,
                            "model": cli_model,
                            "session_id": session_id,
                            "cli_type": "claude",
                            "event_type": "todo_update" if is_update else "todo_list",
                            "isUpdate": is_update,
                            "tool_name": tool_name,
                            "tool_input": tool_input,
                            "tool_id": tool_id
                        },
                        session_id=session_id,
                        created_at=datetime.utcnow()
                    )
                elif chunk.get("type") == "code_generation":
                    yield Message(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        role="assistant",
                        content=chunk.get("content", ""),
                        message_type="chat",
                        metadata_json={
                            "sandbox_id": vibekit.sandbox_id,
                            "model": cli_model,
                            "session_id": session_id,
                            "cli_type": "claude",
                            "event_type": "code_generation"
                        },
                        session_id=session_id,
                        created_at=datetime.utcnow()
                    )
                elif chunk.get("type") == "error":
                    yield Message(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        role="assistant",
                        content=f"Error: {chunk.get('error', 'Unknown error')}",
                        message_type="error",
                        metadata_json={
                            "sandbox_id": vibekit.sandbox_id,
                            "error": chunk.get("error"),
                            "cli_type": "claude"
                        },
                        session_id=session_id,
                        created_at=datetime.utcnow()
                    )
                elif chunk.get("type") == "complete":
                    # Get current session ID for resumption
                    current_session = await vibekit.get_session()
                    if current_session:
                        self.session_mapping[project_id] = current_session
                    
                    yield Message(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        role="assistant",
                        content="Code generation completed",
                        message_type="info",
                        metadata_json={
                            "sandbox_id": vibekit.sandbox_id,
                            "session_id": current_session,
                            "cli_type": "claude",
                            "event_type": "completion"
                        },
                        session_id=session_id,
                        created_at=datetime.utcnow()
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

