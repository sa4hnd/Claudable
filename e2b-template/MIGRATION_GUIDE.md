# Migration Guide: Updating to Custom E2B Sandbox Template

This guide helps you migrate from the default E2B template to your custom template with Claude Code and Bun.

## Step 1: Build the Custom Template

1. **Navigate to the template directory**:
   ```bash
   cd e2b-template
   ```

2. **Build the template**:
   ```bash
   ./build-template.sh
   ```

3. **Copy the new template ID** from the build output.

## Step 2: Update VibeKit Bridge Configuration

### Update `apps/api/vibekit-bridge/index.js`

Replace the template ID in the E2B provider configuration:

```javascript
// Before
const e2bProvider = createE2BProvider({
  apiKey: process.env.E2B_API_KEY,
  templateId: "vibekit-claude" // Old template
});

// After
const e2bProvider = createE2BProvider({
  apiKey: process.env.E2B_API_KEY,
  templateId: "your-new-template-id" // New custom template
});
```

### Update `apps/api/vibekit-bridge/package.json`

Add the new template ID as an environment variable:

```json
{
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js"
  },
  "env": {
    "E2B_TEMPLATE_ID": "your-new-template-id"
  }
}
```

## Step 3: Update VibeKit Service

### Update `apps/api/app/services/vibekit_service.py`

Modify the VibeKit service to use the new template:

```python
# Update the template ID in the service initialization
class VibeKitService:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.template_id = "your-new-template-id"  # New template ID
        # ... rest of the implementation
```

## Step 4: Update Environment Variables

### Update `.env` files

Add the new template ID to your environment configuration:

```bash
# Add to your .env files
E2B_TEMPLATE_ID=your-new-template-id
E2B_CUSTOM_TEMPLATE=true
```

## Step 5: Test the Migration

### 1. Test VibeKit Bridge

```bash
cd apps/api/vibekit-bridge
npm start
```

Check the health endpoint:
```bash
curl http://localhost:3001/api/health
```

### 2. Test Sandbox Initialization

```bash
curl -X POST http://localhost:3001/api/sandbox/initialize \
  -H "Content-Type: application/json" \
  -d '{"projectId": "test-project"}'
```

### 3. Test Claude Code Integration

```bash
curl -X POST http://localhost:3001/api/sandbox/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "test-project",
    "prompt": "Create a simple React component",
    "streaming": true
  }'
```

## Step 6: Update Documentation

### Update README files

1. **Main README**: Update the E2B template information
2. **API README**: Update the VibeKit bridge documentation
3. **Deployment docs**: Update any deployment configurations

## Step 7: Monitor and Optimize

### Performance Monitoring

1. **Resource Usage**: Monitor CPU and memory usage with the new 4GB/2CPU allocation
2. **Startup Time**: Check if the pre-installed tools improve initialization speed
3. **Tool Availability**: Verify that Claude Code and Bun are working correctly

### Optimization Opportunities

1. **Package Management**: Use Bun for faster package installation
2. **Development Workflow**: Leverage pre-installed tools for faster development
3. **Resource Allocation**: Adjust CPU/memory based on actual usage patterns

## Rollback Plan

If you need to rollback to the previous template:

1. **Revert template ID**: Change back to `"vibekit-claude"`
2. **Update environment variables**: Remove custom template references
3. **Test functionality**: Ensure all features work with the old template

## Troubleshooting

### Common Issues

1. **Template not found**: Ensure the template ID is correct and the template is built
2. **Resource limits**: Check that your E2B plan supports 4GB RAM and 2 CPU cores
3. **Tool not found**: Verify that Claude Code and Bun are properly installed in the template

### Debug Steps

1. **Check template status**: Use E2B CLI to verify template exists
2. **Test sandbox creation**: Create a test sandbox to verify functionality
3. **Check logs**: Review VibeKit bridge logs for any errors
4. **Verify environment**: Ensure all environment variables are set correctly

## Benefits of the New Template

### Performance Improvements
- **Faster startup**: Pre-installed tools reduce initialization time
- **Better resource allocation**: 4GB RAM and 2 CPU cores for better performance
- **Optimized environment**: Tailored for Claudable's specific needs

### Development Experience
- **Claude Code ready**: No need to install Claude Code in each sandbox
- **Bun integration**: Faster package management and execution
- **Comprehensive tooling**: All necessary development tools pre-installed

### Maintenance
- **Consistent environment**: Same tools and versions across all sandboxes
- **Reduced complexity**: Fewer installation steps and dependencies
- **Better debugging**: Pre-configured environment for easier troubleshooting

## Next Steps

After successful migration:

1. **Monitor performance**: Track resource usage and performance metrics
2. **Optimize further**: Fine-tune the template based on usage patterns
3. **Document changes**: Update team documentation with new procedures
4. **Plan updates**: Schedule regular template updates to keep tools current
