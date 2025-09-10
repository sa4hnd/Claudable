"""
Sandbox-based Project Initializer Service
Handles project initialization using VibeKit sandboxes
"""
import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.core.terminal_ui import ui
from app.services.vibekit_service import get_vibekit_service


async def initialize_project_sandbox(project_id: str, name: str) -> Dict[str, Any]:
    """
    Initialize a new project using VibeKit sandbox
    
    Args:
        project_id: Unique project identifier
        name: Human-readable project name
    
    Returns:
        Dict containing project initialization results
    """
    
    ui.info(f"Initializing project {project_id} in sandbox", "SandboxInit")
    
    try:
        # Get VibeKit service for this project
        vibekit = get_vibekit_service(project_id)
        
        # Initialize sandbox
        sandbox_id = await vibekit.initialize_sandbox()
        
        # Navigate to /vibe0 directory (like your test script)
        ui.info("Navigating to /vibe0 directory", "SandboxInit")
        await vibekit.execute_command("cd /vibe0 && pwd")
        
        # Note: Next.js project creation will be handled by Claude Code execution
        # This sandbox initializer just sets up the sandbox environment
        ui.info("Sandbox environment ready for Claude Code execution", "SandboxInit")
        
        # Get host URL for preview
        ui.info("Getting preview host URL", "SandboxInit")
        host_url = await vibekit.get_host(3000)
        
        # Create local metadata directory for tracking
        create_local_metadata(project_id, name, sandbox_id, host_url)
        
        ui.success(f"Project {project_id} initialized successfully in sandbox", "SandboxInit")
        
        return {
            "project_id": project_id,
            "sandbox_id": sandbox_id,
            "host_url": host_url,
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        ui.error(f"Failed to initialize project in sandbox: {e}", "SandboxInit")
        # Cleanup sandbox if initialization failed
        try:
            await vibekit.cleanup()
        except:
            pass
        raise Exception(f"Failed to initialize Next.js project in sandbox: {str(e)}")


def create_local_metadata(project_id: str, name: str, sandbox_id: str, host_url: str):
    """
    Create local metadata file for sandbox project tracking
    
    Args:
        project_id: Project identifier
        name: Project name
        sandbox_id: VibeKit sandbox ID
        host_url: Preview host URL
    """
    
    # Create local project directory for metadata
    project_path = os.path.join(settings.projects_root, project_id)
    os.makedirs(project_path, exist_ok=True)
    
    # Create sandbox metadata
    sandbox_metadata = {
        "project_id": project_id,
        "name": name,
        "sandbox_id": sandbox_id,
        "host_url": host_url,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "type": "sandbox"
    }
    
    metadata_path = os.path.join(project_path, "sandbox_metadata.json")
    
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(sandbox_metadata, f, indent=2, ensure_ascii=False)
        ui.success(f"Created sandbox metadata at {metadata_path}", "SandboxInit")
    except Exception as e:
        ui.error(f"Failed to create sandbox metadata: {e}", "SandboxInit")
        raise


async def cleanup_project_sandbox(project_id: str) -> bool:
    """
    Clean up sandbox project resources
    
    Args:
        project_id: Project identifier to clean up
    
    Returns:
        bool: True if cleanup was successful
    """
    
    ui.info(f"Cleaning up sandbox project: {project_id}", "SandboxCleanup")
    
    try:
        # Get VibeKit service for this project
        vibekit = get_vibekit_service(project_id)
        
        # Cleanup sandbox
        await vibekit.cleanup()
        
        # Remove local metadata
        project_path = os.path.join(settings.projects_root, project_id)
        metadata_path = os.path.join(project_path, "sandbox_metadata.json")
        
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
        
        # Remove project directory if empty
        try:
            if os.path.exists(project_path) and not os.listdir(project_path):
                os.rmdir(project_path)
        except OSError:
            pass  # Directory not empty, that's fine
        
        ui.success(f"Sandbox project {project_id} cleaned up successfully", "SandboxCleanup")
        return True
        
    except Exception as e:
        ui.error(f"Error cleaning up sandbox project {project_id}: {e}", "SandboxCleanup")
        return False


async def get_sandbox_metadata(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Get sandbox metadata for a project
    
    Args:
        project_id: Project identifier
    
    Returns:
        Optional[Dict]: Sandbox metadata if exists
    """
    
    metadata_path = os.path.join(settings.projects_root, project_id, "sandbox_metadata.json")
    
    if not os.path.exists(metadata_path):
        return None
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        ui.error(f"Failed to read sandbox metadata for project {project_id}: {e}", "SandboxInit")
        return None


async def sandbox_project_exists(project_id: str) -> bool:
    """
    Check if a sandbox project exists
    
    Args:
        project_id: Project identifier
    
    Returns:
        bool: True if sandbox project exists
    """
    
    metadata = await get_sandbox_metadata(project_id)
    return metadata is not None and metadata.get("status") == "active"


async def start_preview_sandbox(project_id: str) -> Dict[str, Any]:
    """
    Start development server in sandbox
    
    Args:
        project_id: Project identifier
    
    Returns:
        Dict containing preview server information
    """
    
    ui.info(f"Starting preview server for project {project_id}", "SandboxPreview")
    
    try:
        # Get VibeKit service for this project
        vibekit = get_vibekit_service(project_id)
        
        # Install dependencies
        ui.info("Installing dependencies", "SandboxPreview")
        await vibekit.execute_command("npm install", {"background": False})
        
        # Start Next.js dev server
        ui.info("Starting Next.js development server", "SandboxPreview")
        await vibekit.execute_command("npm run dev", {
            "background": True,
            "port": 3000
        })
        
        # Get host URL
        host_url = await vibekit.get_host(3000)
        
        ui.success(f"Preview server started: {host_url}", "SandboxPreview")
        
        return {
            "url": host_url,
            "status": "running",
            "project_id": project_id,
            "sandbox_id": vibekit.sandbox_id
        }
        
    except Exception as e:
        ui.error(f"Failed to start preview server: {e}", "SandboxPreview")
        raise


async def stop_preview_sandbox(project_id: str) -> bool:
    """
    Stop development server in sandbox
    
    Args:
        project_id: Project identifier
    
    Returns:
        bool: True if stopped successfully
    """
    
    ui.info(f"Stopping preview server for project {project_id}", "SandboxPreview")
    
    try:
        # Get VibeKit service for this project
        vibekit = get_vibekit_service(project_id)
        
        # Stop the development server (this will be handled by VibeKit)
        # For now, we'll just cleanup the sandbox
        await vibekit.cleanup()
        
        ui.success(f"Preview server stopped for project {project_id}", "SandboxPreview")
        return True
        
    except Exception as e:
        ui.error(f"Failed to stop preview server: {e}", "SandboxPreview")
        return False

