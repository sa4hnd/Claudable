#!/bin/bash

# Build script for custom E2B sandbox template with Claude Code and Bun
# This script builds the template and provides instructions for deployment

set -e

echo "🚀 Building custom E2B sandbox template with Claude Code and Bun..."

# Check if E2B CLI is installed
if ! command -v e2b &> /dev/null; then
    echo "❌ E2B CLI is not installed. Please install it first:"
    echo "   npm i -g @e2b/cli"
    echo "   or"
    echo "   brew install e2b"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Prerequisites checked"

# Build the template with custom CPU and memory specifications
echo "🔨 Building sandbox template with 4GB RAM and 2 CPU cores..."
e2b template build -c "/home/user/startup.sh" --cpu-count 2 --memory-mb 4096

echo ""
echo "✅ Template built successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Copy the template ID from the output above"
echo "2. Update your VibeKit service to use the new template ID"
echo "3. Test the sandbox with your application"
echo ""
echo "🔧 To use the new template in your code:"
echo "   Python: sandbox = Sandbox('your-new-template-id')"
echo "   JavaScript: const sandbox = await Sandbox.create('your-new-template-id')"
echo ""
echo "📊 Resource specifications:"
echo "   - CPU: 2 cores"
echo "   - Memory: 4GB"
echo "   - Includes: Claude Code, Bun, Node.js, Python packages, Expo CLI"
echo ""
echo "🎉 Your custom sandbox template is ready!"
