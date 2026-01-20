#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "Starting project environment setup..."

# 1. Install uv
echo "Checking and installing uv..."
if ! command_exists uv; then
    echo "uv not found, installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install uv
    else
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
else
    echo -e "${GREEN}uv is already installed${NC}"
fi

# 2. Check if Python is installed
echo "Checking Python..."
if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is required, please install Python 3${NC}"
    exit 1
else
    echo -e "${GREEN}Python is installed $(python3 --version)${NC}"
fi

# 3. Create and activate virtual environment
echo "Creating and activating virtual environment..."
if [ ! -d ".venv" ]; then
    uv venv
fi
source .venv/bin/activate
echo -e "${GREEN}Virtual environment activated${NC}"

# 4. Install Python dependencies
echo "Installing Python dependencies..."
if [ -f "pyproject.toml" ]; then
    uv sync
    echo -e "${GREEN}Python dependencies installed${NC}"
else
    echo -e "${RED}Error: pyproject.toml file not found${NC}"
    exit 1
fi

# 5. Install Node.js and npm
echo "Checking and installing Node.js and npm..."
if ! command_exists node; then
    echo "Node.js not found, installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install node
    else
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
else
    echo -e "${GREEN}Node.js is installed $(node --version)${NC}"
fi

if ! command_exists npm; then
    echo -e "${RED}Error: npm not found, please check Node.js installation${NC}"
    exit 1
else
    echo -e "${GREEN}npm is installed $(npm --version)${NC}"
fi

# 6. Install npm dependencies and build Electron app
echo "Installing npm dependencies..."
if [ -f "package.json" ]; then
    npm install
    echo -e "${GREEN}npm dependencies installed${NC}"
else
    echo -e "${RED}Error: package.json file not found${NC}"
    exit 1
fi

#echo "Building Electron application..."
#npm run build
#echo -e "${GREEN}Electron application built${NC}"

# 7. Start Electron application
echo "Starting Electron application..."
source .venv/bin/activate
npm start

echo -e "${GREEN}Project setup complete and application started!${NC}"
