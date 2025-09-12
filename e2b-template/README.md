# Custom E2B Sandbox Template for Claudable

This is a custom E2B sandbox template optimized for the Claudable application, featuring Claude Code, Bun, and development tools with enhanced CPU and memory specifications.

## Features

### Pre-installed Tools
- **Claude Code**: Globally installed for AI-powered coding
- **Bun**: Latest version for fast JavaScript/TypeScript runtime and package management
- **Node.js**: LTS version for compatibility
- **Python**: With comprehensive development packages
- **Expo CLI**: For React Native development
- **Development Tools**: Git, curl, wget, build-essential, etc.

### Resource Specifications
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Base Image**: E2B code-interpreter (Debian-based)

### Pre-installed Python Packages
- `claude-code` (globally)
- `requests`, `beautifulsoup4`
- `pandas`, `numpy`, `matplotlib`, `seaborn`
- `jupyter`, `ipykernel`
- `black`, `flake8`, `pytest`
- `fastapi`, `uvicorn`
- `sqlalchemy`, `alembic`, `psycopg2-binary`
- `redis`, `celery`, `pydantic`, `python-dotenv`

### Pre-installed NPM Packages
- `@expo/cli`, `@expo/ngrok`
- `typescript`, `ts-node`, `nodemon`
- `pm2`, `yarn`, `pnpm`

## Usage

### Building the Template

1. **Install E2B CLI**:
   ```bash
   npm i -g @e2b/cli
   # or
   brew install e2b
   ```

2. **Build the template**:
   ```bash
   cd e2b-template
   ./build-template.sh
   ```

3. **Update configuration**:
   - Copy the new template ID from the build output
   - Update `e2b.toml` with the new template ID
   - Update your VibeKit service configuration

### Using the Template

#### Python SDK
```python
from e2b import Sandbox, AsyncSandbox

# Sync sandbox
sandbox = Sandbox("your-new-template-id")

# Async sandbox
sandbox = await AsyncSandbox.create("your-new-template-id")
```

#### JavaScript SDK
```javascript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('your-new-template-id')
```

## Integration with Claudable

This template is designed to work seamlessly with your existing Claudable architecture:

### VibeKit Bridge Integration
- The template maintains the same `/vibe0` working directory structure
- Compatible with existing VibeKit bridge endpoints
- Supports the same project initialization flow

### Claude Code Sandbox Adapter
- Works with your existing `claude_code_sandbox.py` adapter
- Maintains the same session management and streaming capabilities
- Supports the same tool usage patterns

### Key Differences from Default Template
1. **Enhanced Resources**: 4GB RAM and 2 CPU cores vs default specifications
2. **Pre-installed Tools**: Claude Code and Bun are globally available
3. **Development Environment**: Comprehensive Python and Node.js packages
4. **Optimized Startup**: Faster initialization with pre-configured tools

## Directory Structure

```
/vibe0/                    # Main working directory
/home/user/projects/       # Project storage
/home/user/.claude-code/   # Claude Code configuration
/home/user/.vscode/        # VS Code settings
```

## Environment Variables

The sandbox automatically sets up:
- `PATH` includes Bun and Python packages
- `PYTHONPATH` includes all installed packages
- Git configuration for development
- Claude Code API configuration structure

## Ports

Exposed ports:
- `3000`: Default development server
- `3001`: VibeKit bridge
- `8080`: API server
- `8888`: Jupyter Lab
- `5000`: Additional services

## Troubleshooting

### Common Issues

1. **Template build fails**: Ensure Docker is running and E2B CLI is installed
2. **Memory issues**: The template is configured for 4GB RAM - ensure your E2B plan supports this
3. **Claude Code not found**: Check that the template built successfully and includes the Python packages

### Debugging

1. **Check template build logs**: Look for any errors during the build process
2. **Verify tool installation**: Connect to the sandbox and run `claude-code --version` and `bun --version`
3. **Check resource allocation**: Ensure your E2B plan supports the specified CPU and memory requirements

## Customization

To modify the template:

1. **Edit `e2b.Dockerfile`**: Add or remove packages as needed
2. **Update `e2b.toml`**: Modify resource specifications or metadata
3. **Rebuild**: Run `./build-template.sh` to create a new version

## Support

For issues related to:
- **E2B**: Check the [E2B documentation](https://e2b.dev/docs)
- **Claude Code**: Check the [Claude Code documentation](https://claude.ai)
- **Bun**: Check the [Bun documentation](https://bun.sh/docs)
- **Claudable**: Check your project documentation
