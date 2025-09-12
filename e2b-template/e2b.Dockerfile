# Custom E2B sandbox template with Claude Code and Bun
# Based on E2B code-interpreter with additional tools
FROM e2bdev/code-interpreter:latest

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1

# Update system and install essential dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    build-essential \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Create user and install Bun for them
RUN useradd -m -s /bin/bash user && \
    usermod -aG sudo user

# Switch to user for Bun installation
USER user
WORKDIR /home/user

# Install Bun (latest version) for the user
RUN curl -fsSL https://bun.com/install | bash
ENV PATH="/home/user/.bun/bin:$PATH"

# Switch back to root for other installations
USER root

# Install Node.js (LTS version for compatibility)
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel

# Install Claude Code globally via npm (as per your specification)
RUN npm install -g @anthropic-ai/claude-code

# Install additional Python packages commonly used in development
RUN pip install \
    requests \
    beautifulsoup4 \
    pandas \
    numpy \
    matplotlib \
    seaborn \
    jupyter \
    ipykernel \
    black \
    flake8 \
    pytest \
    fastapi \
    uvicorn \
    sqlalchemy \
    alembic \
    psycopg2-binary \
    redis \
    celery \
    pydantic \
    python-dotenv

# Install global npm packages
RUN npm install -g \
    @expo/cli \
    @expo/ngrok \
    typescript \
    ts-node \
    nodemon \
    pm2 \
    yarn \
    pnpm

# Create working directories
RUN mkdir -p /vibe0 /home/user/projects /home/user/.vscode

# Set up Claude Code configuration directory
RUN mkdir -p /home/user/.claude-code

# Create startup script
RUN cat > /home/user/startup.sh << 'EOF'
#!/bin/bash

# Set up environment
export PATH="/root/.bun/bin:$PATH"
export PYTHONPATH="/usr/local/lib/python3.11/site-packages:$PYTHONPATH"

# Create /vibe0 directory if it doesn't exist
mkdir -p /vibe0

# Set up git configuration (using your GitHub credentials)
git config --global user.email "shexhtc@gmail.com"
git config --global user.name "sa4hnd"

# Set up shell environment
echo 'export PYTHONPATH="/usr/local/lib/python3.11/site-packages:$PYTHONPATH"' >> ~/.bashrc

# Add Bun to PATH
echo 'export BUN_INSTALL="$HOME/.bun"' >> ~/.bashrc
echo 'export PATH="$BUN_INSTALL/bin:$PATH"' >> ~/.bashrc


# Start Jupyter server in background
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password='' &

# Keep the container running
tail -f /dev/null
EOF

RUN chmod +x /home/user/startup.sh

# Set working directory
WORKDIR /vibe0

# Expose common ports
EXPOSE 3000 3001 8080 8888 5000

# Set the default command
CMD ["/home/user/startup.sh"]
