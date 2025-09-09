"""
Sandbox Session Management
Handles VibeKit sandbox session tracking
"""
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from app.db.base import Base


class SandboxSession(Base):
    """VibeKit sandbox session tracking"""
    __tablename__ = "sandbox_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    
    # Sandbox Information
    sandbox_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    vibekit_session_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    
    # Session Status
    status: Mapped[str] = mapped_column(String(32), default="active")  # active, paused, stopped, error
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Resource Information
    host_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="sandbox_sessions")
