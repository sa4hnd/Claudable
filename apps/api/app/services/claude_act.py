import os
from typing import Tuple, Optional, Callable
import json
from datetime import datetime
from pathlib import Path

# Note: claude_code_sdk imports removed - now using VibeKit sandbox integration


DEFAULT_MODEL = os.getenv("CLAUDE_CODE_MODEL", "claude-sonnet-4-20250514")


def find_prompt_file() -> Path:
    """
    Find the system-prompt.md file in app/prompt/ directory.
    """
    current_path = Path(__file__).resolve()
    
    # Get the app directory (current file is in app/services/)
    app_dir = current_path.parent.parent  # app/
    prompt_file = app_dir / 'prompt' / 'system-prompt.md'
    
    if prompt_file.exists():
        return prompt_file
    
    # Fallback: look for system-prompt.md in various locations
    fallback_locations = [
        current_path.parent.parent / 'prompt' / 'system-prompt.md',  # app/prompt/
        current_path.parent.parent.parent.parent / 'docs' / 'system-prompt.md',  # project-root/docs/
        current_path.parent.parent.parent.parent / 'system-prompt.md',  # project-root/
    ]
    
    for location in fallback_locations:
        if location.exists():
            return location
    
    # Return expected location even if it doesn't exist
    return prompt_file


def load_system_prompt(force_reload: bool = False) -> str:
    """
    Load system prompt from app/prompt/system-prompt.md file.
    Falls back to basic prompt if file not found.
    
    Args:
        force_reload: If True, ignores cache and reloads from file
    """
    # Simple caching mechanism
    if not force_reload and hasattr(load_system_prompt, '_cached_prompt'):
        return load_system_prompt._cached_prompt
    
    try:
        prompt_file = find_prompt_file()
        
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                print(f"✅ Loaded system prompt from: {prompt_file} ({len(content)} chars)")
                
                # Cache the loaded prompt
                load_system_prompt._cached_prompt = content
                return content
        else:
            print(f"⚠️  System prompt file not found at: {prompt_file}")
            
    except Exception as e:
        print(f"❌ Error loading system prompt: {e}")
        import traceback
        traceback.print_exc()
    
    # Fallback to basic prompt
    fallback_prompt = (
        "You are Claude Code, an advanced AI coding assistant specialized in building modern fullstack web applications.\n"
        "You assist users by chatting with them and making changes to their code in real-time.\n\n"
        "Constraints:\n"
        "- Do not delete files entirely; prefer edits.\n"
        "- Keep changes minimal and focused.\n"
        "- Use UTF-8 encoding.\n"
        "- Follow modern development best practices.\n"
    )
    
    print(f"🔄 Using fallback system prompt ({len(fallback_prompt)} chars)")
    load_system_prompt._cached_prompt = fallback_prompt
    return fallback_prompt


def get_system_prompt() -> str:
    """Get the current system prompt (uses cached version)"""
    return load_system_prompt(force_reload=False)


def get_initial_system_prompt() -> str:
    """Get the initial system prompt for project creation (uses cached version)"""
    return load_system_prompt(force_reload=False)


# System prompt is now loaded dynamically via get_system_prompt() and get_initial_system_prompt()


# Legacy functions removed - now only generate_diff_with_logging is used


def extract_tool_summary(tool_name: str, tool_input: dict) -> str:
    """Extract concise summary for tool usage"""
    if tool_name == "Read":
        return f"📖 Reading: {tool_input.get('file_path', 'unknown')}"
    elif tool_name == "Write":
        return f"✏️ Writing: {tool_input.get('file_path', 'unknown')}"
    elif tool_name == "Edit":
        return f"🔧 Editing: {tool_input.get('file_path', 'unknown')}"
    elif tool_name == "MultiEdit":
        return f"🔧 Multi-editing: {tool_input.get('file_path', 'unknown')}"
    elif tool_name == "Bash":
        cmd = tool_input.get('command', '')
        return f"💻 Running: {cmd[:50]}{'...' if len(cmd) > 50 else ''}"
    elif tool_name == "Glob":
        return f"🔍 Searching: {tool_input.get('pattern', 'unknown')}"
    elif tool_name == "Grep":
        return f"🔎 Grep: {tool_input.get('pattern', 'unknown')}"
    elif tool_name == "LS":
        return f"📁 Listing: {tool_input.get('path', 'current dir')}"
    elif tool_name == "WebFetch":
        return f"🌐 Fetching: {tool_input.get('url', 'unknown')}"
    elif tool_name == "TodoWrite":
        return f"📝 Managing todos"
    else:
        return f"🔧 {tool_name}: {list(tool_input.keys())[:3]}"


async def generate_diff_with_logging(
    instruction: str, 
    allow_globs: list[str], 
    repo_path: str,
    log_callback: Optional[Callable] = None,
    resume_session_id: Optional[str] = None,
    system_prompt: str = None
) -> Tuple[str, str, Optional[str]]:
    """
    Generate diff with real-time logging via VibeKit sandbox.
    
    Args:
        instruction: Task description
        allow_globs: List of allowed file patterns
        repo_path: Repository path (project ID for sandbox)
        log_callback: Async function to call with log data
        resume_session_id: Optional session ID to resume
        system_prompt: Custom system prompt (defaults to get_system_prompt())
    
    Returns:
        Tuple of (commit_message, changes_summary, session_id)
    """
    from app.services.vibekit_service import VibeKitService
    
    # Use provided system prompt or default (dynamically loaded)
    effective_system_prompt = system_prompt if system_prompt is not None else get_system_prompt()
    
    # Build a comprehensive prompt for VibeKit
    user_prompt = (
        f"Task: {instruction}\n\n"
        "Please implement the requested changes to this Next.js project. "
        "After making changes, provide a summary in this format:\n"
        "<COMMIT_MSG>One-line imperative commit message</COMMIT_MSG>\n"
        "<SUMMARY>Brief description of changes made</SUMMARY>"
    )
    
    # Initialize VibeKit service
    vibekit_service = VibeKitService()
    
    # Extract project ID from repo_path (assuming it's the project ID)
    project_id = os.path.basename(repo_path)
    
    response_text = ""
    current_session_id = resume_session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    start_time = datetime.now()
    
    try:
        print(f"Starting VibeKit sandbox query with prompt: {user_prompt[:100]}...")
        
        # Add immediate debug message to test real-time transmission
        if log_callback:
            await log_callback("text", {"content": "🚀 Starting VibeKit sandbox execution..."})
        
        # Initialize sandbox if needed
        sandbox_id = await vibekit_service.initialize_sandbox(project_id)
        if log_callback:
            await log_callback("text", {"content": f"📦 Sandbox initialized: {sandbox_id}"})
        
        # Generate code using VibeKit
        result = await vibekit_service.generate_code(
            project_id=project_id,
            prompt=user_prompt,
            mode="ask"
        )
        
        if result and result.get("success"):
            response_text = result.get("content", "")
            
            # Stream the response text
            if log_callback and response_text:
                await log_callback("text", {"content": response_text})
            
            # Simulate tool usage for compatibility
            if log_callback:
                await log_callback("tool_start", {
                    "tool_id": "vibekit_generation",
                    "tool_name": "VibeKit Code Generation",
                    "summary": "Generating code using VibeKit sandbox",
                    "input": {"prompt": user_prompt}
                })
                
                await log_callback("tool_result", {
                    "tool_id": "vibekit_generation",
                    "tool_name": "VibeKit Code Generation",
                    "summary": "Code generation completed",
                    "is_error": False,
                    "content": response_text[:500] if response_text else None
                })
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        if log_callback:
            await log_callback("result", {
                "duration_ms": int(duration_ms),
                "api_duration_ms": int(duration_ms),
                "turns": 1,
                "total_cost_usd": 0.0,  # VibeKit handles cost internally
                "is_error": not (result and result.get("success")),
                "session_id": current_session_id
            })
                    
    except Exception as exc:
        print(f"VibeKit sandbox exception: {type(exc).__name__}: {exc}")
        if log_callback:
            await log_callback("error", {"message": str(exc)})
        raise RuntimeError(f"VibeKit sandbox execution failed: {exc}") from exc
    
    print(f"VibeKit sandbox completed.")
    
    # If no response was received, provide fallback
    if not response_text:
        print("No response received from VibeKit sandbox - falling back to simple response")
        response_text = f"I understand you want to: {instruction}\n\nHowever, VibeKit sandbox is not fully configured. Please check your E2B_API_KEY and ANTHROPIC_API_KEY."
    
    # Extract commit message and summary
    commit_msg = ""
    if "<COMMIT_MSG>" in response_text and "</COMMIT_MSG>" in response_text:
        commit_msg = response_text.split("<COMMIT_MSG>", 1)[1].split("</COMMIT_MSG>", 1)[0].strip()
    
    if not commit_msg:
        commit_msg = instruction.strip()[:72]
    
    diff_summary = "Changes applied via VibeKit sandbox"
    if "<SUMMARY>" in response_text and "</SUMMARY>" in response_text:
        diff_summary = response_text.split("<SUMMARY>", 1)[1].split("</SUMMARY>", 1)[0].strip()
    
    # Return session ID for conversation continuity
    return commit_msg, diff_summary, current_session_id
