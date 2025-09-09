# 🚀 Claudable + VibeKit Migration Plan

## 📋 **Executive Summary**

This document outlines the complete migration of Claudable from local CLI execution to cloud-based sandbox execution using VibeKit SDK and E2B sandboxes. This migration will eliminate the need for users to install Claude Code CLI or other dependencies locally, providing a seamless cloud-based development experience.

## 🎯 **Migration Goals**

1. **Eliminate Local Dependencies**: Remove need for Claude Code CLI, Git, Node.js on user machines
2. **Cloud-First Architecture**: Move all development operations to E2B sandboxes
3. **Real-time Collaboration**: Enable multiple users to work on projects simultaneously
4. **Scalable Infrastructure**: Support unlimited concurrent projects
5. **Enhanced Security**: Isolated execution environments with automatic cleanup

## 🏗️ **Current vs. Target Architecture**

### **Current Architecture (Local)**
```
User → Web UI → FastAPI → Local CLI (claude command) → Local File System
                ↓
            WebSocket → Real-time Updates
```

### **Target Architecture (Cloud Sandbox)**
```
User → Web UI → FastAPI → VibeKit SDK → E2B Sandbox → Claude Code
                ↓                    ↓
            WebSocket ← Real-time Streaming ← Sandbox Operations
```

## 📊 **Current System Analysis**

### **Components Requiring Migration**

#### **1. CLI Execution Layer**
- **File**: `apps/api/app/services/cli/adapters/claude_code.py`
- **Current**: Uses `claude_code_sdk` with local file system and session management
- **Migration**: Replace with VibeKit SDK calls using `vibekit-claude` template

#### **2. Project Management**
- **File**: `apps/api/app/services/project/initializer.py`
- **Current**: Creates local directories using `create-next-app` and scaffolds Next.js projects
- **Migration**: Use VibeKit `executeCommand()` for project scaffolding in sandbox

#### **3. File System Operations**
- **File**: `apps/api/app/services/filesystem.py`
- **Current**: Direct file system operations (create, read, write) with `scaffold_nextjs_minimal()`
- **Migration**: Use VibeKit `generateCode()` and `executeCommand()` for file operations

#### **4. Development Server**
- **File**: `apps/api/app/services/local_runtime.py`
- **Current**: Local Next.js dev server with port management and process monitoring
- **Migration**: Use VibeKit `getHost()` for sandbox-hosted preview with `npm run dev`

#### **5. Environment Management**
- **File**: `apps/api/app/services/env_manager.py`
- **Current**: Local .env file management with encryption/decryption
- **Migration**: Use VibeKit secrets management for environment variables

#### **6. WebSocket Communication**
- **File**: `apps/api/app/core/websocket/manager.py`
- **Current**: Real-time updates from local processes with message streaming
- **Migration**: Stream VibeKit operations to WebSocket clients

#### **7. Session Management**
- **File**: `apps/api/app/services/cli_session_manager.py`
- **Current**: Local session tracking and resumption
- **Migration**: Use VibeKit session management with `getSession()` and `setSession()`

## 🔧 **Implementation Plan**

### **Phase 1: VibeKit Service Foundation**

#### **1.1 Create VibeKit Service**
```python
# apps/api/app/services/vibekit_service.py
import asyncio
import os
from typing import Optional, Dict, Any, AsyncGenerator
from app.core.terminal_ui import ui

class VibeKitService:
    def __init__(self):
        self.e2b_provider = {
            "apiKey": os.getenv("E2B_API_KEY"),
            "templateId": "vibekit-claude"  # Use pre-built template
        }
        
        self.agent_config = {
            "type": "claude",
            "provider": "anthropic",
            "apiKey": os.getenv("ANTHROPIC_API_KEY"),
            "model": "claude-sonnet-4-20250514"
        }
        
        self.sandbox_id = None
        self.session_id = None

    async def initialize_sandbox(self) -> str:
        """Initialize E2B sandbox and return sandbox ID"""
        # This will be implemented using VibeKit SDK
        # For now, return a placeholder
        self.sandbox_id = f"sandbox_{os.urandom(8).hex()}"
        return self.sandbox_id

    async def generate_code(self, prompt: str, streaming: bool = True) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate code using VibeKit Claude Code agent"""
        # This will be implemented using VibeKit SDK
        # For now, return a placeholder
        yield {"type": "code_generation", "content": "Generated code placeholder"}

    async def execute_command(self, command: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute command in sandbox"""
        # This will be implemented using VibeKit SDK
        return {"success": True, "output": "Command executed"}

    async def get_host(self, port: int) -> str:
        """Get host URL for sandbox port"""
        # This will be implemented using VibeKit SDK
        return f"https://{port}-{self.sandbox_id}.e2b.dev"

    async def cleanup(self):
        """Cleanup sandbox resources"""
        # This will be implemented using VibeKit SDK
        pass
```

#### **1.2 Use Pre-built VibeKit Template**
✅ **No Custom Dockerfile Needed** - Use VibeKit's pre-built `"vibekit-claude"` template which includes:
- Claude Code CLI pre-installed
- Node.js and npm
- Git and development tools
- File system operations
- Port forwarding capabilities

### **Phase 2: Core Service Migration**

#### **2.1 Project Initialization Migration**
```python
# Replace: apps/api/app/services/project/initializer.py
async def initialize_project_sandbox(project_id: str, name: str) -> Dict[str, Any]:
    """Initialize project using VibeKit sandbox"""
    
    # Create VibeKit instance
    vibekit = VibeKitService()
    
    # Initialize sandbox
    sandbox_id = await vibekit.initialize_sandbox()
    
    # Execute project creation commands (replaces scaffold_nextjs_minimal)
    await vibekit.executeCommand("npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias '@/*' --yes", {
        "background": False
    })
    
    # Initialize git repository (replaces init_git_repo)
    await vibekit.executeCommand("git init && git add . && git commit -m 'Initial commit'")
    
    # Create .env file (replaces write_env_file)
    env_content = f"NEXT_PUBLIC_PROJECT_ID={project_id}\nNEXT_PUBLIC_PROJECT_NAME={name}\n"
    await vibekit.executeCommand(f"echo '{env_content}' > .env")
    
    # Get host URL for preview
    host_url = await vibekit.getHost(3000)
    
    return {
        "project_id": project_id,
        "sandbox_id": sandbox_id,
        "host_url": host_url,
        "status": "active"
    }
```

#### **2.2 Claude Code Execution Migration**
```python
# Replace: apps/api/app/services/cli/adapters/claude_code.py
async def execute_with_streaming_sandbox(
    self,
    instruction: str,
    project_id: str,
    session_id: Optional[str] = None,
    log_callback: Optional[Callable] = None,
) -> AsyncGenerator[Message, None]:
    """Execute Claude Code using VibeKit sandbox"""
    
    vibekit = VibeKitService()
    
    # Initialize sandbox for project
    sandbox_id = await vibekit.initialize_sandbox()
    
    # Resume session if provided (replaces session management)
    if session_id:
        await vibekit.setSession(session_id)
    
    # Stream code generation (replaces Claude Code SDK streaming)
    async for chunk in vibekit.generate_code(instruction, streaming=True):
        
        if log_callback:
            await log_callback(chunk)
        
        yield Message(
            role="assistant",
            content=chunk.get("content", ""),
            message_type="code_generation",
            metadata_json={"sandbox_id": sandbox_id}
        )
```

#### **2.3 Development Server Migration**
```python
# Replace: apps/api/app/services/local_runtime.py
async def start_preview_sandbox(project_id: str) -> dict:
    """Start development server in sandbox"""
    
    vibekit = VibeKitService()
    
    # Initialize sandbox for project
    sandbox_id = await vibekit.initialize_sandbox()
    
    # Install dependencies (replaces npm install logic)
    await vibekit.executeCommand("npm install", {
        "background": False
    })
    
    # Start Next.js dev server (replaces subprocess.Popen)
    await vibekit.executeCommand("npm run dev", {
        "background": True,
        "port": 3000
    })
    
    # Get host URL (replaces localhost port management)
    host_url = await vibekit.getHost(3000)
    
    return {
        "url": host_url,
        "status": "running",
        "project_id": project_id,
        "sandbox_id": sandbox_id
    }
```

### **Phase 3: WebSocket Integration**

#### **3.1 Real-time Streaming**
```python
# Update: apps/api/app/core/websocket/manager.py
async def stream_vibekit_operations(project_id: str, operation: str, params: dict):
    """Stream VibeKit operations to WebSocket clients"""
    
    vibekit = VibeKitService()
    
    try:
        if operation == "generate_code":
            async for chunk in vibekit.generateCode(params, streaming=True):
                await manager.send_message(project_id, {
                    "type": "code_chunk",
                    "data": chunk
                })
        
        elif operation == "execute_command":
            result = await vibekit.executeCommand(params["command"], params.get("options", {}))
            await manager.send_message(project_id, {
                "type": "command_result",
                "data": result
            })
        
        elif operation == "get_host":
            host_url = await vibekit.getHost(params["port"])
            await manager.send_message(project_id, {
                "type": "host_url",
                "data": {"url": host_url}
            })
    
    except Exception as e:
        await manager.send_message(project_id, {
            "type": "error",
            "data": {"error": str(e)}
        })
```

### **Phase 4: Environment & Secrets Management**

#### **4.1 Secrets Integration**
```python
# Update: apps/api/app/services/env_manager.py
async def sync_env_to_sandbox(project_id: str, env_vars: dict):
    """Sync environment variables to VibeKit sandbox"""
    
    vibekit = VibeKitService()
    
    # Set secrets in sandbox
    for key, value in env_vars.items():
        await vibekit.setSecret(key, value)
    
    # Update .env file in sandbox
    env_content = "\n".join([f"{k}={v}" for k, v in env_vars.items()])
    await vibekit.executeCommand(f"echo '{env_content}' > .env")
```

### **Phase 5: Database Schema Updates**

#### **5.1 Project Model Updates**
```python
# Update: apps/api/app/models/projects.py
class Project(Base):
    # ... existing fields ...
    
    # New fields for sandbox integration
    sandbox_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    sandbox_status: Mapped[str] = mapped_column(String(32), default="inactive")
    host_url: Mapped[str] = mapped_column(String(512), nullable=True)
    last_sandbox_activity: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Update existing fields
    preview_url: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Now points to sandbox URL
    repo_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)  # Now points to sandbox path
```

#### **5.2 Session Management Updates**
```python
# Update: apps/api/app/models/sessions.py
class Session(Base):
    # ... existing fields ...
    
    # New fields for sandbox integration
    sandbox_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    vibekit_session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    
    # Update existing fields
    claude_session_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)  # Now VibeKit session
```

#### **5.3 New Sandbox Management Model**
```python
# New: apps/api/app/models/sandbox_sessions.py
class SandboxSession(Base):
    __tablename__ = "sandbox_sessions"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    sandbox_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active")  # active, paused, stopped, error
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="sandbox_sessions")
```

## 🔄 **Migration Strategy**

### **Phase 1: Parallel Implementation (Weeks 1-2)**
- Implement VibeKit service alongside existing local CLI
- Create feature flag system to switch between local/sandbox
- Test sandbox functionality with sample projects

### **Phase 2: Gradual Migration (Weeks 3-4)**
- Migrate project creation to sandbox
- Update WebSocket handlers for sandbox streaming
- Implement sandbox session management

### **Phase 3: Full Migration (Weeks 5-6)**
- Migrate all CLI operations to sandbox
- Update frontend to use sandbox-hosted previews
- Remove local CLI dependencies

### **Phase 4: Optimization (Weeks 7-8)**
- Implement sandbox pooling and reuse
- Add advanced features (collaboration, sharing)
- Performance optimization and monitoring

## 📋 **Required Environment Variables**

```bash
# VibeKit Configuration
E2B_API_KEY=your_e2b_api_key
E2B_TEMPLATE_ID=vibekit-claude  # Use pre-built template

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional: VibeKit API Key (if using VibeKit API directly)
VIBEKIT_API_KEY=your_vibekit_api_key
```

## 🧪 **Testing Strategy**

### **Unit Tests**
- VibeKit service integration tests
- Sandbox session management tests
- WebSocket streaming tests

### **Integration Tests**
- End-to-end project creation flow
- Real-time collaboration scenarios
- Error handling and recovery

### **Performance Tests**
- Concurrent sandbox creation
- Memory usage monitoring
- Response time benchmarks

## 📊 **Monitoring & Observability**

### **Metrics to Track**
- Sandbox creation time
- Code generation latency
- WebSocket connection stability
- Resource usage per sandbox
- Error rates and types

### **Logging Strategy**
- Structured logging for all VibeKit operations
- Real-time error tracking
- Performance metrics collection

## 🚨 **Risk Mitigation**

### **Technical Risks**
- **Sandbox Latency**: Implement caching and connection pooling
- **API Rate Limits**: Implement exponential backoff and retry logic
- **Session Management**: Implement automatic cleanup and renewal

### **Business Risks**
- **Cost Management**: Monitor E2B usage and implement cost controls
- **Reliability**: Implement fallback mechanisms and error recovery
- **Security**: Ensure proper sandbox isolation and data protection

## 📈 **Success Metrics**

### **Performance Metrics**
- Project creation time < 30 seconds
- Code generation latency < 5 seconds
- 99.9% uptime for sandbox operations

### **User Experience Metrics**
- Zero local dependency installation required
- Real-time collaboration support
- Seamless preview functionality

### **Business Metrics**
- Increased user adoption
- Reduced support tickets
- Improved scalability

## 🔧 **Implementation Checklist**

### **Backend Tasks**
- [ ] Create VibeKit service wrapper
- [ ] Migrate project initialization to sandbox
- [ ] Update Claude Code execution with VibeKit
- [ ] Implement sandbox session management
- [ ] Update WebSocket handlers for streaming
- [ ] Migrate environment variable management
- [ ] Update database models for sandbox integration
- [ ] Implement error handling and recovery
- [ ] Add monitoring and logging
- [ ] Update preview server to use sandbox URLs

### **Frontend Tasks**
- [ ] Update preview iframe to use sandbox URLs
- [ ] Implement real-time sandbox status updates
- [ ] Update project creation flow
- [ ] Add sandbox management UI
- [ ] Implement collaboration features
- [ ] Update error handling and user feedback

### **DevOps Tasks**
- [ ] Set up E2B account and API keys
- [ ] Configure VibeKit integration
- [ ] Implement sandbox cleanup automation
- [ ] Set up monitoring and alerting
- [ ] Configure cost management
- [ ] Implement backup and recovery procedures

## 🎯 **Next Steps**

1. **Immediate**: Set up E2B account and configure VibeKit integration
2. **Week 1**: Implement VibeKit service foundation
3. **Week 2**: Migrate project creation to sandbox
4. **Week 3**: Update WebSocket handlers for real-time streaming
5. **Week 4**: Migrate all CLI operations to sandbox
6. **Week 5**: Frontend integration and testing
7. **Week 6**: Performance optimization and monitoring
8. **Week 7**: User testing and feedback
9. **Week 8**: Production deployment and monitoring

---

**This migration will transform Claudable into a truly cloud-native platform, eliminating local dependencies while providing enhanced collaboration and scalability features.**
