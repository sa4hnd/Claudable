"""
Sandbox-based Project CRUD Operations
Handles create, read, update, delete operations for sandbox projects
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
import re
import uuid
import asyncio

from app.api.deps import get_db
from app.models.projects import Project as ProjectModel
from app.models.sandbox_sessions import SandboxSession
from app.models.messages import Message
from app.models.project_services import ProjectServiceConnection
from app.models.sessions import Session as SessionModel
from app.services.project.sandbox_initializer import (
    initialize_project_sandbox,
    cleanup_project_sandbox,
    start_preview_sandbox,
    stop_preview_sandbox
)
from app.core.websocket.manager import manager as websocket_manager
from app.core.terminal_ui import ui

# Project ID validation regex
PROJECT_ID_REGEX = re.compile(r"^[a-z0-9-]{3,}$")

# Pydantic models
class SandboxProjectCreate(BaseModel):
    project_id: str = Field(..., pattern=PROJECT_ID_REGEX.pattern)
    name: str
    initial_prompt: Optional[str] = None
    preferred_cli: Optional[str] = "claude"
    selected_model: Optional[str] = None
    fallback_enabled: Optional[bool] = True
    cli_settings: Optional[dict] = None

class SandboxProjectUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    settings: Optional[dict] = None

class SandboxProject(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    sandbox_id: Optional[str] = None
    sandbox_status: Optional[str] = None
    host_url: Optional[str] = None
    preview_url: Optional[str] = None
    initial_prompt: Optional[str] = None
    template_type: Optional[str] = None
    preferred_cli: str
    selected_model: Optional[str] = None
    fallback_enabled: bool
    settings: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    last_active_at: Optional[datetime] = None
    last_sandbox_activity: Optional[datetime] = None
    services: dict = {}

    class Config:
        from_attributes = True

router = APIRouter()


async def initialize_sandbox_project_background(project_id: str, project_name: str, body: SandboxProjectCreate):
    """Initialize sandbox project in background with WebSocket progress updates"""
    try:
        # Send initial status update
        await websocket_manager.broadcast_to_project(project_id, {
            "type": "project_status",
            "data": {
                "status": "initializing",
                "message": "Initializing sandbox environment..."
            }
        })
        
        # Initialize the project using sandbox initializer
        from app.api.deps import get_db
        
        # Create new database session for background task
        db_session = next(get_db())
        
        try:
            # Initialize project in sandbox
            result = await initialize_project_sandbox(project_id, project_name)
            
            # Update project with sandbox information
            project = db_session.query(ProjectModel).filter(ProjectModel.id == project_id).first()
            if project:
                project.sandbox_id = result["sandbox_id"]
                project.sandbox_status = "active"
                project.host_url = result["host_url"]
                project.preview_url = result["host_url"]  # Use sandbox URL as preview
                project.last_sandbox_activity = datetime.utcnow()
                project.status = "active"
                db_session.commit()
            
            # Send completion status
            await websocket_manager.broadcast_to_project(project_id, {
                "type": "project_status",
                "data": {
                    "status": "active",
                    "message": "Sandbox project ready!",
                    "host_url": result["host_url"]
                }
            })
            
            ui.success(f"Sandbox project {project_id} initialized successfully")
            
        finally:
            db_session.close()
            
    except Exception as e:
        ui.error(f"Failed to initialize sandbox project {project_id}: {e}")
        
        # Send error status
        await websocket_manager.broadcast_to_project(project_id, {
            "type": "project_status",
            "data": {
                "status": "error",
                "message": f"Failed to initialize sandbox: {str(e)}"
            }
        })


@router.post("/sandbox", response_model=SandboxProject)
async def create_sandbox_project(
    body: SandboxProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new sandbox project"""
    
    # Check if project already exists
    existing_project = db.query(ProjectModel).filter(ProjectModel.id == body.project_id).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="Project with this ID already exists")
    
    # Create project record
    project = ProjectModel(
        id=body.project_id,
        name=body.name,
        description=None,
        status="initializing",
        initial_prompt=body.initial_prompt,
        template_type="nextjs",
        preferred_cli=body.preferred_cli or "claude",
        selected_model=body.selected_model,
        fallback_enabled=body.fallback_enabled,
        settings=body.cli_settings or {}
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Start background initialization
    background_tasks.add_task(
        initialize_sandbox_project_background,
        body.project_id,
        body.name,
        body
    )
    
    return SandboxProject(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        sandbox_id=project.sandbox_id,
        sandbox_status=project.sandbox_status,
        host_url=project.host_url,
        preview_url=project.preview_url,
        initial_prompt=project.initial_prompt,
        template_type=project.template_type,
        preferred_cli=project.preferred_cli,
        selected_model=project.selected_model,
        fallback_enabled=project.fallback_enabled,
        settings=project.settings,
        created_at=project.created_at,
        updated_at=project.updated_at,
        last_active_at=project.last_active_at,
        last_sandbox_activity=project.last_sandbox_activity,
        services={}
    )


@router.get("/sandbox", response_model=List[SandboxProject])
async def list_sandbox_projects(db: Session = Depends(get_db)) -> List[SandboxProject]:
    """List all sandbox projects with their status and last activity"""
    
    # Get projects with their last message time using subquery
    last_message_subquery = (
        db.query(
            Message.project_id,
            func.max(Message.created_at).label('last_message_at')
        )
        .group_by(Message.project_id)
        .subquery()
    )
    
    # Query projects with last message time
    projects_with_last_message = (
        db.query(ProjectModel, last_message_subquery.c.last_message_at)
        .outerjoin(
            last_message_subquery,
            ProjectModel.id == last_message_subquery.c.project_id
        )
        .filter(ProjectModel.sandbox_id.isnot(None))  # Only sandbox projects
        .order_by(desc(ProjectModel.created_at))
        .all()
    )
    
    result: List[SandboxProject] = []
    for project, last_message_at in projects_with_last_message:
        # Get service connections for this project
        services = {}
        service_connections = db.query(ProjectServiceConnection).filter(
            ProjectServiceConnection.project_id == project.id
        ).all()
        
        for conn in service_connections:
            services[conn.provider] = {
                "connected": True,
                "status": conn.status
            }
        
        # Ensure all service types are represented
        for provider in ["github", "supabase", "vercel"]:
            if provider not in services:
                services[provider] = {
                    "connected": False,
                    "status": "disconnected"
                }
        
        result.append(SandboxProject(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            sandbox_id=project.sandbox_id,
            sandbox_status=project.sandbox_status,
            host_url=project.host_url,
            preview_url=project.preview_url,
            initial_prompt=project.initial_prompt,
            template_type=project.template_type,
            preferred_cli=project.preferred_cli,
            selected_model=project.selected_model,
            fallback_enabled=project.fallback_enabled,
            settings=project.settings,
            created_at=project.created_at,
            updated_at=project.updated_at,
            last_active_at=project.last_active_at,
            last_sandbox_activity=project.last_sandbox_activity,
            services=services
        ))
    
    return result


@router.get("/sandbox/{project_id}", response_model=SandboxProject)
async def get_sandbox_project(project_id: str, db: Session = Depends(get_db)):
    """Get a specific sandbox project"""
    
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.sandbox_id.isnot(None)
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Sandbox project not found")
    
    # Get service connections
    services = {}
    service_connections = db.query(ProjectServiceConnection).filter(
        ProjectServiceConnection.project_id == project.id
    ).all()
    
    for conn in service_connections:
        services[conn.provider] = {
            "connected": True,
            "status": conn.status
        }
    
    return SandboxProject(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        sandbox_id=project.sandbox_id,
        sandbox_status=project.sandbox_status,
        host_url=project.host_url,
        preview_url=project.preview_url,
        initial_prompt=project.initial_prompt,
        template_type=project.template_type,
        preferred_cli=project.preferred_cli,
        selected_model=project.selected_model,
        fallback_enabled=project.fallback_enabled,
        settings=project.settings,
        created_at=project.created_at,
        updated_at=project.updated_at,
        last_active_at=project.last_active_at,
        last_sandbox_activity=project.last_sandbox_activity,
        services=services
    )


@router.post("/sandbox/{project_id}/preview/start")
async def start_sandbox_preview(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start preview server for a sandbox project"""
    
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.sandbox_id.isnot(None)
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Sandbox project not found")
    
    # Start preview in background
    background_tasks.add_task(start_preview_sandbox, project_id)
    
    return {"message": "Preview server starting in background", "project_id": project_id}


@router.post("/sandbox/{project_id}/preview/stop")
async def stop_sandbox_preview(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Stop preview server for a sandbox project"""
    
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.sandbox_id.isnot(None)
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Sandbox project not found")
    
    # Stop preview
    success = await stop_preview_sandbox(project_id)
    
    if success:
        return {"message": "Preview server stopped", "project_id": project_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to stop preview server")


@router.delete("/sandbox/{project_id}")
async def delete_sandbox_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Delete a sandbox project"""
    
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.sandbox_id.isnot(None)
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Sandbox project not found")
    
    # Cleanup sandbox in background
    background_tasks.add_task(cleanup_project_sandbox, project_id)
    
    # Delete project from database
    db.delete(project)
    db.commit()
    
    return {"message": "Sandbox project deleted", "project_id": project_id}


@router.get("/sandbox/health")
async def sandbox_health():
    """Health check for sandbox projects router"""
    return {"status": "ok", "router": "sandbox_projects"}

