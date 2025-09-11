import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { VibeKit } from '@vibe-kit/sdk';
import { createE2BProvider } from '@vibe-kit/e2b';

dotenv.config();

const app = express();
const PORT = process.env.VIBEKIT_BRIDGE_PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// VibeKit configuration
const e2bProvider = createE2BProvider({
  apiKey: process.env.E2B_API_KEY,
  templateId: "vibekit-claude" // Use pre-built template
});

const vibeKit = new VibeKit()
  .withAgent({
    type: "claude",
    provider: "anthropic",
    apiKey: process.env.ANTHROPIC_API_KEY,
    model: "claude-sonnet-4-20250514",
  })
  .withSandbox(e2bProvider);

// Store active sandboxes
const activeSandboxes = new Map();

// Initialize sandbox
app.post('/api/sandbox/initialize', async (req, res) => {
  try {
    const { projectId } = req.body;
    
    if (!projectId) {
      return res.status(400).json({ error: 'Project ID is required' });
    }

    // Initialize sandbox
    const sandboxId = `sandbox_${projectId}_${Date.now()}`;
    activeSandboxes.set(projectId, {
      sandboxId,
      status: 'initializing',
      createdAt: new Date()
    });

    // Create /vibe0 directory and navigate to it (like your test script)
    try {
      await vibeKit.executeCommand("cd /vibe0 && pwd");
      console.log(`[VibeKit] Navigated to /vibe0 directory`);
    } catch (error) {
      console.log(`[VibeKit] /vibe0 directory doesn't exist, creating it...`);
      await vibeKit.executeCommand("mkdir -p /vibe0 && cd /vibe0 && pwd");
      console.log(`[VibeKit] Created and navigated to /vibe0 directory`);
    }

    // Using npm for package management (Bun requires unzip which is not available in E2B sandbox)
    console.log(`[VibeKit] Using npm for package management`);

    // Configure Claude Code API settings in sandbox (like you do locally)
    console.log(`[VibeKit] Configuring Claude Code API settings in sandbox...`);
    
    // Set environment variables for current session
    await vibeKit.executeCommand("unset ANTHROPIC_API_KEY"); // Remove old API key
    await vibeKit.executeCommand(`export ANTHROPIC_AUTH_TOKEN='${process.env.ANTHROPIC_API_KEY}'`);
    await vibeKit.executeCommand(`export ANTHROPIC_BASE_URL='${process.env.ANTHROPIC_BASE_URL}'`);
    await vibeKit.executeCommand(`export ANTHROPIC_API_KEY='${process.env.ANTHROPIC_API_KEY}'`); // Set both for compatibility
    
    // Add to all shell profiles for persistence using echo -e with proper quoting
    await vibeKit.executeCommand("echo -e '\\n# Claude Code API Configuration' >> ~/.bash_profile");
    await vibeKit.executeCommand(`echo -e '\\nexport ANTHROPIC_AUTH_TOKEN=\"${process.env.ANTHROPIC_API_KEY}\"' >> ~/.bash_profile`);
    await vibeKit.executeCommand(`echo -e '\\nexport ANTHROPIC_API_KEY=\"${process.env.ANTHROPIC_API_KEY}\"' >> ~/.bash_profile`);
    await vibeKit.executeCommand(`echo -e '\\nexport ANTHROPIC_BASE_URL=\"${process.env.ANTHROPIC_BASE_URL}\"' >> ~/.bash_profile`);
    
    await vibeKit.executeCommand("echo -e '\\n# Claude Code API Configuration' >> ~/.bashrc");
    await vibeKit.executeCommand(`echo -e '\\nexport ANTHROPIC_AUTH_TOKEN=\"${process.env.ANTHROPIC_API_KEY}\"' >> ~/.bashrc`);
    await vibeKit.executeCommand(`echo -e '\\nexport ANTHROPIC_API_KEY=\"${process.env.ANTHROPIC_API_KEY}\"' >> ~/.bashrc`);
    await vibeKit.executeCommand(`echo -e '\\nexport ANTHROPIC_BASE_URL=\"${process.env.ANTHROPIC_BASE_URL}\"' >> ~/.bashrc`);
    
    await vibeKit.executeCommand("echo -e '\\n# Claude Code API Configuration' >> ~/.zshrc");
    await vibeKit.executeCommand(`echo -e '\\nexport ANTHROPIC_AUTH_TOKEN=\"${process.env.ANTHROPIC_API_KEY}\"' >> ~/.zshrc`);
    await vibeKit.executeCommand(`echo -e '\\nexport ANTHROPIC_API_KEY=\"${process.env.ANTHROPIC_API_KEY}\"' >> ~/.zshrc`);
    await vibeKit.executeCommand(`echo -e '\\nexport ANTHROPIC_BASE_URL=\"${process.env.ANTHROPIC_BASE_URL}\"' >> ~/.zshrc`);
    
    // Verify configuration with detailed debugging
    console.log(`[VibeKit] Verifying API configuration...`);
    const envCheck = await vibeKit.executeCommand("echo '=== ANTHROPIC Environment Variables ===' && env | grep ANTHROPIC && echo '=== Current Directory ===' && pwd && echo '=== Shell Profile Contents ===' && echo 'Bash Profile:' && cat ~/.bash_profile | grep ANTHROPIC && echo 'Bash RC:' && cat ~/.bashrc | grep ANTHROPIC");
    console.log(`[VibeKit] Environment check result:`, envCheck);
    console.log(`[VibeKit] Claude Code API settings configured successfully`);

    res.json({
      success: true,
      sandboxId,
      status: 'initializing'
    });
  } catch (error) {
    console.error('Error initializing sandbox:', error);
    res.status(500).json({ error: error.message });
  }
});

// Generate code
app.post('/api/sandbox/generate-code', async (req, res) => {
  try {
    const { projectId, prompt, streaming = false } = req.body;
    
    if (!projectId || !prompt) {
      return res.status(400).json({ error: 'Project ID and prompt are required' });
    }

    const sandbox = activeSandboxes.get(projectId);
    if (!sandbox) {
      return res.status(404).json({ error: 'Sandbox not found' });
    }

    if (streaming) {
      // For streaming, we'll need to implement Server-Sent Events
      res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Cache-Control'
      });

      try {
        // Project is already in /vibe0, just navigate to it
        let projectDir;
        if (projectId.startsWith('project-')) {
          // Extract the actual project ID from the full project ID
          const actualProjectId = projectId.replace('project-', '').split('-')[0];
          projectDir = `/vibe0/my-app${actualProjectId}`;
        } else {
          projectDir = `/vibe0/my-app${projectId}`;
        }
        console.log(`[VibeKit] Navigating to project directory: ${projectDir}`);
        
        // Change to the project directory in /vibe0
        const cdResult = await vibeKit.executeCommand(`cd ${projectDir} && pwd`);
        console.log(`[VibeKit] Directory change result:`, cdResult);
        
        // Check environment variables before code generation
        const envCheckBefore = await vibeKit.executeCommand(`cd ${projectDir} && echo '=== Environment Variables Before Code Generation ===' && env | grep ANTHROPIC`);
        console.log(`[VibeKit] Environment before code generation:`, envCheckBefore);
        
        // Update the prompt to include the full path
        const fullPrompt = `Working in directory: ${projectDir}\n\n${prompt}`;
        
        console.log(`[VibeKit] Generating code in directory: ${projectDir}`);
        
        // Set up streaming event listeners
        vibeKit.on("update", (message) => {
          console.log(`[VibeKit] Streaming update: ${message}`);
        
        // Parse message if it's a string
        let parsedMessage = message;
        if (typeof message === 'string') {
          try {
            parsedMessage = JSON.parse(message);
            console.log(`[VibeKit] Parsed message:`, parsedMessage);
          } catch (e) {
            console.log(`[VibeKit] Failed to parse message as JSON:`, e);
            parsedMessage = message;
          }
        }
        
        // Extract text content from VibeKit message
        let content = "";
        console.log(`[VibeKit] Processing message type: ${parsedMessage?.type}`);
        console.log(`[VibeKit] Message structure:`, JSON.stringify(parsedMessage, null, 2));
        
        if (parsedMessage && typeof parsedMessage === 'object') {
          if (parsedMessage.type === "assistant" && parsedMessage.message && parsedMessage.message.content) {
            console.log(`[VibeKit] Assistant message content:`, parsedMessage.message.content);
            // Extract text from assistant message content array
            if (Array.isArray(parsedMessage.message.content)) {
              const textParts = parsedMessage.message.content.filter(part => part.type === "text");
              const toolUseParts = parsedMessage.message.content.filter(part => part.type === "tool_use");
              
              console.log(`[VibeKit] Text parts found:`, textParts);
              console.log(`[VibeKit] Tool use parts found:`, toolUseParts);
              
              // Send text content
              if (textParts.length > 0) {
                content = textParts.map(part => part.text).join("");
                console.log(`[VibeKit] Extracted content:`, content);
              }
              
              // Send tool usage
              if (toolUseParts.length > 0) {
                for (const toolPart of toolUseParts) {
                  const toolName = toolPart.name || "Unknown Tool";
                  const toolInput = toolPart.input || {};
                  const toolId = toolPart.id || "";
                  
                  // Special handling for TodoWrite - check if it contains actual todo data
                  if (toolName === "TodoWrite") {
                    // Check if toolInput contains todos array
                    if (toolInput.todos && Array.isArray(toolInput.todos)) {
                      console.log(`[VibeKit] TodoWrite with todos data:`, toolInput.todos);
                      // Send as todo_list message
                      res.write(`data: ${JSON.stringify({ 
                        type: 'todo_list', 
                        content: JSON.stringify(toolInput.todos),
                        tool_name: toolName,
                        tool_input: toolInput,
                        tool_id: toolId
                      })}\n\n`);
                    } else {
                      // Regular tool usage message
                      res.write(`data: ${JSON.stringify({ 
                        type: 'tool_use', 
                        content: `\`Planning for next moves...\``,
                        tool_name: toolName,
                        tool_input: toolInput,
                        tool_id: toolId
                      })}\n\n`);
                    }
                  } else {
                    // Create tool summary with proper styling like other CLIs
                    let toolSummary = "";
                    if (toolName === "MultiEdit") {
                      const filePath = toolInput.file_path || "file";
                      const displayPath = filePath.length > 40 ? "…/" + filePath.split("/").slice(-2).join("/") : filePath;
                      toolSummary = `**Edit** \`${displayPath}\``;
                    } else if (toolName === "Read") {
                      const filePath = toolInput.file_path || "file";
                      const displayPath = filePath.length > 40 ? "…/" + filePath.split("/").slice(-2).join("/") : filePath;
                      toolSummary = `**Read** \`${displayPath}\``;
                    } else if (toolName === "Bash") {
                      const command = toolInput.command || "command";
                      const displayCmd = command.length > 40 ? command.substring(0, 40) + "..." : command;
                      toolSummary = `**Bash** \`${displayCmd}\``;
                    } else if (toolName === "LS") {
                      toolSummary = `**List** \`directory\``;
                    } else if (toolName === "WebSearch") {
                      const query = toolInput.query || "";
                      const displayQuery = query.length > 50 ? query.substring(0, 50) + "..." : query;
                      toolSummary = `**Search** \`${displayQuery}\``;
                    } else if (toolName === "WebFetch") {
                      const url = toolInput.url || "";
                      const domain = url.split("//")[1]?.split("/")[0] || url;
                      toolSummary = `**Fetch** \`${domain}\``;
                    } else {
                      toolSummary = `**${toolName}** \`tool\``;
                    }
                    
                    console.log(`[VibeKit] Sending tool usage: ${toolSummary}`);
                    res.write(`data: ${JSON.stringify({ 
                      type: 'tool_use', 
                      content: toolSummary,
                      tool_name: toolName,
                      tool_input: toolInput,
                      tool_id: toolId
                    })}\n\n`);
                  }
                }
              }
            } else if (typeof parsedMessage.message.content === "string") {
              content = parsedMessage.message.content;
            }
          } else if (parsedMessage.type === "user" && parsedMessage.message && parsedMessage.message.content) {
            console.log(`[VibeKit] User message content:`, parsedMessage.message.content);
            // Extract text from user message content array
            if (Array.isArray(parsedMessage.message.content)) {
              const textParts = parsedMessage.message.content.filter(part => part.type === "text");
              console.log(`[VibeKit] User text parts found:`, textParts);
              content = textParts.map(part => part.text).join("");
              console.log(`[VibeKit] Extracted user content:`, content);
            } else if (typeof parsedMessage.message.content === "string") {
              content = parsedMessage.message.content;
            }
          } else if (parsedMessage.text) {
            // Direct text content
            content = parsedMessage.text;
          } else if (typeof parsedMessage === "string") {
            content = parsedMessage;
          }
        }
        
        if (content) {
          console.log(`[VibeKit] Sending streaming content: ${content.substring(0, 100)}...`);
          res.write(`data: ${JSON.stringify({ type: 'update', content: content })}\n\n`);
        } else {
          console.log(`[VibeKit] No content extracted from message:`, message);
          // Fallback: try to extract any text content from the raw message
          if (typeof message === 'string' && message.includes('"text":"')) {
            const textMatch = message.match(/"text":"([^"]+)"/);
            if (textMatch) {
              content = textMatch[1];
              console.log(`[VibeKit] Fallback extracted content:`, content);
              res.write(`data: ${JSON.stringify({ type: 'update', content: content })}\n\n`);
            }
          }
        }
        });
        
        vibeKit.on("error", (error) => {
          console.error(`[VibeKit] Streaming error: ${error}`);
          res.write(`data: ${JSON.stringify({ type: 'error', error: error })}\n\n`);
        });
        
      // Generate code with streaming
        const result = await vibeKit.generateCode({ 
          prompt: fullPrompt, 
          mode: "ask" 
        });

        // Stream the final result
      if (result && result.code) {
        res.write(`data: ${JSON.stringify({ type: 'code_generation', content: result.code })}\n\n`);
      }
        res.write(`data: ${JSON.stringify({ type: 'complete' })}\n\n`);
        res.end();
      } catch (error) {
        console.error(`[VibeKit] Error in streaming: ${error.message}`);
        res.write(`data: ${JSON.stringify({ type: 'error', error: error.message })}\n\n`);
        res.end();
      }
    } else {
      // Project is already in /vibe0, just navigate to it
      let projectDir;
      if (projectId.startsWith('project-')) {
        // Extract the actual project ID from the full project ID
        const actualProjectId = projectId.replace('project-', '').split('-')[0];
        projectDir = `/vibe0/my-app${actualProjectId}`;
      } else {
        projectDir = `/vibe0/my-app${projectId}`;
      }
      console.log(`[VibeKit] Navigating to project directory: ${projectDir}`);
      
      // Change to the project directory in /vibe0
      const cdResult = await vibeKit.executeCommand(`cd ${projectDir} && pwd`);
      console.log(`[VibeKit] Directory change result:`, cdResult);
      
      // Update the prompt to include the full path
      const fullPrompt = `Working in directory: ${projectDir}\n\n${prompt}`;
      
      console.log(`[VibeKit] Generating code in directory: ${projectDir}`);
      
      // Set up streaming event listeners for non-streaming mode too
      vibeKit.on("update", (message) => {
        console.log(`[VibeKit] Streaming update: ${message}`);
      });
      
      vibeKit.on("error", (error) => {
        console.error(`[VibeKit] Streaming error: ${error}`);
      });
      
      const result = await vibeKit.generateCode({ 
        prompt: fullPrompt, 
        mode: "ask" 
      });

      res.json({
        success: true,
        code: result.code || result,
        sandboxId: sandbox.sandboxId
      });
    }
  } catch (error) {
    console.error('Error generating code:', error);
    res.status(500).json({ error: error.message });
  }
});

// Execute command
app.post('/api/sandbox/execute-command', async (req, res) => {
  try {
    const { projectId, command, options = {} } = req.body;
    
    if (!projectId || !command) {
      return res.status(400).json({ error: 'Project ID and command are required' });
    }

    const sandbox = activeSandboxes.get(projectId);
    if (!sandbox) {
      return res.status(404).json({ error: 'Sandbox not found' });
    }

    console.log(`[VibeKit] Executing command: ${command}`);
    
    // Special handling for git clone template-expo: start in background, return after 3 seconds, complete in background
    if (command.includes('git clone') && command.includes('template-expo')) {
      console.log(`[VibeKit] Detected git clone template-expo command - starting in background with npm and Expo dev server`);
      
      // Initialize completion tracking
      sandbox.createExpoAppCompleted = false;
      sandbox.createExpoAppResult = null;
      
      // Extract the project directory name from the command
      const projectDirMatch = command.match(/my-app[a-f0-9]+/);
      const projectDir = projectDirMatch ? projectDirMatch[0] : 'my-app';
      const fullProjectPath = `/vibe0/${projectDir}`;
      
      // Generate custom URLs based on project folder name
      const generateProjectUrls = (projectDir) => {
        return {
          mobile: `exp://${projectDir}.ngrok.io`,
          web: `https://3000-${projectDir}.e2b.dev`
        };
      };
      
      const projectUrls = generateProjectUrls(projectDir);
      console.log(`[VibeKit] Generated URLs:`, projectUrls);
      
      // Check if command already includes npx expo start (chained from Python)
      let chainedCommand;
      if (command.includes('npx expo start')) {
        // Command is already chained from Python, use as-is
        chainedCommand = command;
        console.log(`[VibeKit] Command already chained from Python: ${chainedCommand}`);
      } else {
        // Chain git clone with npm install and npx expo start
        chainedCommand = `${command} && cd ${projectDir} && npm install && npm install @expo/ngrok@4.1.0 --save-dev && export EXPO_TUNNEL_SUBDOMAIN=${projectDir} && npx expo start --tunnel --port 3000`;
        console.log(`[VibeKit] Chained command: ${chainedCommand}`);
      }
      
      // Start the chained command in background
      const startBackgroundProcess = async () => {
        try {
          console.log(`[VibeKit] Starting git clone template-expo + npm install + Expo dev server process...`);
          const result = await vibeKit.executeCommand(chainedCommand, options);
          console.log(`[VibeKit] git clone template-expo + npm install + Expo dev server ACTUALLY completed:`, result);
          sandbox.createExpoAppCompleted = true;
          sandbox.createExpoAppResult = { ...result, urls: projectUrls };
        } catch (error) {
          console.error(`[VibeKit] git clone template-expo + npm install + Expo dev server failed:`, error);
          sandbox.createExpoAppCompleted = true;
          sandbox.createExpoAppResult = { success: false, error: error.message, urls: projectUrls };
        }
      };
      
      // Start the background process (don't await it)
      startBackgroundProcess();
      
      // Wait for 3 seconds to let the project structure be created
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Return success after 3 seconds so Claude Code can start coding
      res.json({
        success: true,
        output: 'Expo template cloning started with npm and dev server. Claude Code can now begin coding while setup completes in background.',
        stderr: '',
        exitCode: 0,
        sandboxId: sandbox.sandboxId,
        background: true,
        message: 'Expo template cloning + npm install + dev server starting - you can start coding now!',
        urls: projectUrls
      });
      
      return;
    }
    
    // Special handling for commands that need the project directory to exist
    if (command.includes('my-app') && (command.includes('cd /vibe0/my-app') || command.includes('&& cd my-app'))) {
      console.log(`[VibeKit] Detected command that needs project directory - checking if it exists`);
      
      // Extract project directory from command
      const projectDirMatch = command.match(/my-app[a-f0-9]+/);
      if (projectDirMatch) {
        const projectDir = projectDirMatch[0];
        const fullProjectPath = `/vibe0/${projectDir}`;
        
        // Check if directory exists, if not wait for it
        const checkDirectory = async () => {
          let attempts = 0;
          const maxAttempts = 30; // 1 minute max wait (30 * 2 seconds)
          
          while (attempts < maxAttempts) {
            try {
              const checkResult = await vibeKit.executeCommand(`ls -la ${fullProjectPath}`, { ...options, background: false });
              if (checkResult.exitCode === 0) {
                console.log(`[VibeKit] Project directory ${fullProjectPath} exists, proceeding with command`);
                return true;
              }
            } catch (error) {
              // Directory doesn't exist yet, continue waiting
            }
            
            await new Promise(resolve => setTimeout(resolve, 2000));
            attempts++;
            console.log(`[VibeKit] Waiting for project directory... attempt ${attempts}/${maxAttempts}`);
          }
          
          console.error(`[VibeKit] Project directory ${fullProjectPath} not found after ${maxAttempts} attempts`);
          return false;
        };
        
        const directoryExists = await checkDirectory();
        if (!directoryExists) {
          return res.status(500).json({
            success: false,
            error: `Project directory ${fullProjectPath} not found`,
            sandboxId: sandbox.sandboxId
          });
        }
      }
    }
    
    // Note: npx expo start is now handled automatically as part of git clone template-expo command
    
    // Special handling for npm install: start in background and return early
    if (command.includes('npm install')) {
      console.log(`[VibeKit] Detected npm install command - starting in background`);
      
      // Start the command in background
      const backgroundPromise = vibeKit.executeCommand(command, { ...options, background: true });
      
      // Return success immediately
        res.json({
        success: true,
        output: 'Dependencies installation started with npm in background. You can continue coding while packages install.',
        stderr: '',
        exitCode: 0,
          sandboxId: sandbox.sandboxId,
        background: true,
        message: 'Dependencies installing with npm in background - you can continue coding!'
      });
      
      // Continue the background process
      backgroundPromise.then(result => {
        console.log(`[VibeKit] Background npm install completed:`, result);
      }).catch(error => {
        console.error(`[VibeKit] Background npm install failed:`, error);
      });
      
      return;
    }
    
    // For other commands, use normal timeout handling
    const timeout = 60000; // 1 minute for other commands
    
    const result = await Promise.race([
      vibeKit.executeCommand(command, options),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error(`Command timed out after ${timeout/1000} seconds`)), timeout)
      )
    ]);
    
    console.log(`[VibeKit] Command result:`, result);

    res.json({
      success: result.exitCode === 0,
      output: result.stdout || result.output || '',
      stderr: result.stderr || '',
      exitCode: result.exitCode,
      sandboxId: sandbox.sandboxId
    });
  } catch (error) {
    console.error('[VibeKit] Error executing command:', error);
    res.status(500).json({ 
      success: false,
      error: error.message,
      details: error.result || error
    });
  }
});

// Get host URL
app.get('/api/sandbox/host/:projectId/:port', async (req, res) => {
  try {
    const { projectId, port } = req.params;
    
    const sandbox = activeSandboxes.get(projectId);
    if (!sandbox) {
      return res.status(404).json({ error: 'Sandbox not found' });
    }

    let hostUrl = await vibeKit.getHost(parseInt(port));
    
    // Ensure the URL has the correct protocol
    if (hostUrl && !hostUrl.startsWith('http://') && !hostUrl.startsWith('https://')) {
      hostUrl = `https://${hostUrl}`;
    }

    res.json({
      success: true,
      hostUrl,
      sandboxId: sandbox.sandboxId
    });
  } catch (error) {
    console.error('Error getting host URL:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get session
app.get('/api/sandbox/session/:projectId', async (req, res) => {
  try {
    const { projectId } = req.params;
    
    const sandbox = activeSandboxes.get(projectId);
    if (!sandbox) {
      return res.status(404).json({ error: 'Sandbox not found' });
    }

    const session = await vibeKit.getSession();

    res.json({
      success: true,
      session,
      sandboxId: sandbox.sandboxId
    });
  } catch (error) {
    console.error('Error getting session:', error);
    res.status(500).json({ error: error.message });
  }
});

// Set session
app.post('/api/sandbox/session/:projectId', async (req, res) => {
  try {
    const { projectId } = req.params;
    const { sessionId } = req.body;
    
    const sandbox = activeSandboxes.get(projectId);
    if (!sandbox) {
      return res.status(404).json({ error: 'Sandbox not found' });
    }

    await vibeKit.setSession(sessionId);

    res.json({
      success: true,
      message: 'Session set successfully',
      sandboxId: sandbox.sandboxId
    });
  } catch (error) {
    console.error('Error setting session:', error);
    res.status(500).json({ error: error.message });
  }
});

// Cleanup sandbox
app.delete('/api/sandbox/:projectId', async (req, res) => {
  try {
    const { projectId } = req.params;
    
    const sandbox = activeSandboxes.get(projectId);
    if (!sandbox) {
      return res.status(404).json({ error: 'Sandbox not found' });
    }

    await vibeKit.kill();
    activeSandboxes.delete(projectId);

    res.json({
      success: true,
      message: 'Sandbox cleaned up successfully'
    });
  } catch (error) {
    console.error('Error cleaning up sandbox:', error);
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    activeSandboxes: activeSandboxes.size,
    timestamp: new Date().toISOString()
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 VibeKit Bridge running on port ${PORT}`);
  console.log(`📦 Using E2B template: vibekit-claude`);
  console.log(`🤖 Using Claude model: claude-sonnet-4-20250514`);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🛑 Shutting down VibeKit Bridge...');
  
  // Cleanup all active sandboxes
  for (const [projectId, sandbox] of activeSandboxes) {
    try {
      await vibeKit.kill();
      console.log(`✅ Cleaned up sandbox for project: ${projectId}`);
    } catch (error) {
      console.error(`❌ Error cleaning up sandbox for project ${projectId}:`, error);
    }
  }
  
  process.exit(0);
});