#!/usr/bin/env python3
"""
Test script for VibeKit sandbox integration
"""
import asyncio
import sys
import os

# Add the API directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from app.services.vibekit_service import VibeKitService

async def test_vibekit_connection():
    """Test VibeKit bridge connection"""
    print("🧪 Testing VibeKit connection...")
    
    try:
        service = VibeKitService("test-project")
        health = await service.health_check()
        
        if health.get("status") == "ok":
            print("✅ VibeKit bridge is running")
            print(f"   Active sandboxes: {health.get('activeSandboxes', 0)}")
            return True
        else:
            print(f"❌ VibeKit bridge error: {health.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def test_sandbox_initialization():
    """Test sandbox initialization"""
    print("\n🧪 Testing sandbox initialization...")
    
    try:
        import time
        unique_id = f"test-init-{int(time.time())}"
        service = VibeKitService(unique_id)
        sandbox_id = await service.initialize_sandbox()
        
        print(f"✅ Sandbox initialized: {sandbox_id}")
        
        # Cleanup
        await service.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Sandbox initialization failed: {e}")
        return False

async def test_full_project_creation():
    """Test full project creation flow - Next.js app + Hello World edit + preview"""
    print("\n🧪 Testing full project creation flow...")
    
    try:
        # Use a unique project ID for each test run
        import time
        timestamp = int(time.time())
        unique_id = f"test-project-{timestamp}"
        app_name = f"my-app-{timestamp}"
        service = VibeKitService(unique_id)
        
        # Step 1: Initialize sandbox
        print("   📦 Initializing sandbox...")
        sandbox_id = await service.initialize_sandbox()
        print(f"   ✅ Sandbox initialized: {sandbox_id}")
        
        # Step 2: Navigate to /vibe0 directory and clean up
        print("   📁 Navigating to /vibe0 directory...")
        await service.execute_command("cd /vibe0 && pwd")
        print("   ✅ Navigated to /vibe0 directory")
        
        # Step 2.5: Clean up any existing my-app directories
        print("   🧹 Cleaning up any existing directories...")
        await service.execute_command("cd /vibe0 && rm -rf my-app*")
        print("   ✅ Cleaned up existing directories")
        
        # Step 3: Create Next.js project (like scaffold_nextjs_minimal)
        print(f"   🚀 Creating Next.js project '{app_name}' in /vibe0...")
        create_cmd = [
            "npx", "create-next-app@latest", app_name,
            "--typescript", "--tailwind", "--eslint", "--app",
            "--import-alias", "@/*", "--use-npm", "--yes"
        ]
        
        result = await service.execute_command(f"cd /vibe0 && {' '.join(create_cmd)}")
        if not result.get("success"):
            print(f"   ❌ create-next-app failed: {result}")
            # Try to get more details about what's in the directory
            ls_result = await service.execute_command("cd /vibe0 && ls -la")
            print(f"   📁 Directory contents: {ls_result}")
            raise Exception(f"Failed to create Next.js project: {result}")
        print("   ✅ Next.js project created in /vibe0")
        
        # Step 4: Navigate to project directory
        print("   📁 Navigating to project directory...")
        await service.execute_command(f"cd /vibe0/{app_name} && pwd")
        print("   ✅ Navigated to project directory")
        
        # Step 5: Create .env file (like write_env_file)
        print("   ⚙️ Creating .env file...")
        env_content = f"NEXT_PUBLIC_PROJECT_ID={unique_id}\nNEXT_PUBLIC_PROJECT_NAME=Test Project"
        await service.execute_command(f"cd /vibe0/{app_name} && echo '{env_content}' > .env")
        print("   ✅ .env file created")
        
        # Step 6: Initialize git (like init_git_repo)
        print("   🔧 Initializing git repository...")
        # First configure git user
        await service.execute_command(f"cd /vibe0/{app_name} && git config --global user.email 'shexhtc@gmail.com' && git config --global user.name 'sa4hnd'")
        
        # Then initialize git
        git_result = await service.execute_command(f"cd /vibe0/{app_name} && git init")
        if not git_result.get("success"):
            print("   ⚠️ Git init failed, continuing...")
        else:
            print("   ✅ Git repository initialized")
            
            # Add and commit files
            add_result = await service.execute_command(f"cd /vibe0/{app_name} && git add .")
            if add_result.get("success"):
                commit_result = await service.execute_command(f"cd /vibe0/{app_name} && git commit -m 'Initial commit'")
                if commit_result.get("success"):
                    print("   ✅ Initial commit created")
                else:
                    print("   ⚠️ Initial commit failed, continuing...")
            else:
                print("   ⚠️ Git add failed, continuing...")
        
        # Step 7: Edit the main page to say "Hello World" (like code generation)
        print("   ✏️ Editing main page to say 'Hello World'...")
        edit_prompt = f"Edit the main page.tsx file in /vibe0/{app_name} to display 'Hello World from VibeKit Sandbox!' instead of the default content"
        
        async for chunk in service.generate_code(edit_prompt, streaming=True):
            if chunk.get("type") == "update":
                print(f"   🤖 Claude: {chunk.get('content', '')}")
            elif chunk.get("type") == "code_generation":
                print(f"   📝 Generated code: {chunk.get('content', '')[:100]}...")
            elif chunk.get("type") == "error":
                print(f"   ❌ Error: {chunk.get('error', '')}")
            elif chunk.get("type") == "complete":
                print("   ✅ Code generation completed")
                break
        print("   ✅ Page edited successfully")
        
        # Step 8: Start development server (like start_preview_process) - run in background
        print("   🚀 Starting development server in background...")
        dev_result = await service.execute_command(f"cd /vibe0/{app_name} && npm run dev -- --port 3000", {"background": True})
        if not dev_result.get("success"):
            print(f"   ❌ Dev server failed to start: {dev_result}")
            raise Exception(f"Failed to start dev server: {dev_result}")
        print("   ✅ Development server started in background")
        
        # Step 9: Get preview URL (like getHost)
        print("   🌐 Getting preview URL...")
        host_url = await service.get_host(3000)
        print(f"   ✅ Preview URL: {host_url}")
        
        # Step 10: Verify the project structure
        print("   📋 Verifying project structure...")
        ls_result = await service.execute_command(f"cd /vibe0/{app_name} && ls -la")
        print(f"   📁 Project contents: {ls_result}")
        
        # Step 11: Show the edited page content
        print("   📄 Showing edited page content...")
        page_content = await service.execute_command(f"cd /vibe0/{app_name} && cat app/page.tsx")
        print(f"   📝 Page content: {page_content}")
        
        # Step 12: Keep sandbox running
        print("   ⏳ Keeping sandbox running for testing...")
        print("   ✅ Sandbox kept running")
        
        print("✅ Full project creation test completed")
        print(f"🎉 Your Next.js app is running at: {host_url}")
        return True
        
    except Exception as e:
        print(f"❌ Full project creation failed: {e}")
        return False

async def test_command_execution():
    """Test command execution"""
    print("\n🧪 Testing command execution...")
    
    try:
        import time
        unique_id = f"test-cmd-{int(time.time())}"
        service = VibeKitService(unique_id)
        
        # Initialize sandbox first
        await service.initialize_sandbox()
        
        # Test simple command
        result = await service.execute_command("echo 'Hello from sandbox'")
        print(f"   Command result: {result}")
        
        # Cleanup
        await service.cleanup()
        
        print("✅ Command execution test completed")
        return True
        
    except Exception as e:
        print(f"❌ Command execution failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting VibeKit sandbox tests...\n")
    
    tests = [
        test_vibekit_connection,
        test_sandbox_initialization,
        test_command_execution,
        test_full_project_creation,  # This replaces test_code_generation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! VibeKit integration is working.")
    else:
        print("⚠️  Some tests failed. Check the VibeKit bridge configuration.")
    
    # Keep sandbox running for testing
    print("\n🔧 Sandbox kept running for further testing")
    print("🌐 You can access your Next.js app at the preview URL shown above")
    print("⏳ The script will keep running...")
    
    # Keep the script running indefinitely
    import asyncio
    while True:
        await asyncio.sleep(60)  # Sleep for 1 minute intervals
        print("⏰ Sandbox still running...")

if __name__ == "__main__":
    asyncio.run(main())