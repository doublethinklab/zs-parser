#!/bin/bash

set -e

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Print section header
section() {
    echo -e "\n${YELLOW}==>${NC} ${GREEN}$1${NC}"
}

# Print status message
status() {
    echo -e "${YELLOW}[*]${NC} $1"
}

# Print success message
success() {
    echo -e "${GREEN}[+]${NC} $1"
}

# Print error message and exit
error() {
    echo -e "${RED}[!] ERROR:${NC} $1"
    exit 1
}

# Check if running on macOS
is_macos() {
    [[ "$OSTYPE" == "darwin"* ]]
}

# Main installation function
install() {
    section "Starting ZS Parser Installation"
    
    # 1. Check system requirements
    section "Checking System Requirements"
    status "Checking Python 3.10+..."
    if ! command_exists python3; then
        error "Python 3.10 or higher is required. Please install it first."
    fi
    
    # Verify Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ "$(printf '%s\n' "3.10" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.10" ]]; then
        error "Python 3.10 or higher is required. Found Python $PYTHON_VERSION"
    fi
    success "Python $PYTHON_VERSION is installed"
    
    # 2. Install uv if not exists
    section "Setting up uv"
    if ! command_exists uv; then
        status "uv not found, installing..."
        if is_macos; then
            if ! command_exists brew; then
                error "Homebrew is required to install uv on macOS. Please install it first."
            fi
            brew install uv
        else
            curl -LsSf https://astral.sh/uv/install.sh | sh
            # Add uv to PATH if not already there
            if ! echo "$PATH" | grep -q "$HOME/.cargo/bin"; then
                echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
                export PATH="$HOME/.cargo/bin:$PATH"
            fi
        fi
        success "uv installed successfully"
    else
        success "uv is already installed"
    fi
    
    # 3. Set up Python virtual environment
    section "Setting up Python Environment"
    if [ ! -d ".venv" ]; then
        status "Creating virtual environment..."
        uv venv
    fi
    
    # Activate virtual environment
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        success "Virtual environment activated"
    else
        error "Failed to create/activate virtual environment"
    fi
    
    # 4. Install Python dependencies
    section "Installing Python Dependencies"
    if [ -f "pyproject.toml" ]; then
        status "Installing dependencies using uv..."
        uv pip install -e .
        success "Python dependencies installed successfully"
    else
        error "pyproject.toml not found. Are you in the project root?"
    fi
    
    # 5. Install Node.js dependencies
    section "Installing JavaScript Dependencies"
    if ! command_exists node; then
        error "Node.js is required but not installed. Please install Node.js 16+ first."
    fi
    
    if [ -f "package.json" ]; then
        status "Installing Node.js dependencies..."
        npm install
        success "Node.js dependencies installed successfully"
    else
        error "package.json not found. Are you in the project root?"
    fi
    
    # 6. Build the application
    section "Building Application"
    status "Building the application..."
    npm run build
    
    # 7. Create desktop entry (Linux) or application shortcut (macOS/Windows)
    if ! is_macos; then
        # Linux: Create desktop entry
        if [ -d "/usr/share/applications" ]; then
            status "Creating desktop entry..."
            cat > /tmp/zs-parser.desktop <<EOL
[Desktop Entry]
Name=ZS Parser
Comment=Parse data from Zeeshuimer
Exec=$(pwd)/node_modules/.bin/electron .
Icon=$(pwd)/zs-parser.png
Terminal=false
Type=Application
Categories=Utility;
StartupWMClass=zs-parser
EOL
            sudo mv /tmp/zs-parser.desktop /usr/share/applications/
            success "Desktop entry created"
        fi
    else
        # macOS: Create application bundle
        status "Creating application bundle..."
        mkdir -p "ZS Parser.app/Contents/MacOS"
        mkdir -p "ZS Parser.app/Contents/Resources"
        
        # Create Info.plist
        cat > "ZS Parser.app/Contents/Info.plist" <<EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>zs-parser</string>
    <key>CFBundleIconFile</key>
    <string>zs-parser.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.doublethinklab.zs-parser</string>
    <key>CFBundleName</key>
    <string>ZS Parser</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
</dict>
</plist>
EOL
        
        # Create launcher script
        cat > "ZS Parser.app/Contents/MacOS/zs-parser" <<EOL
#!/bin/bash
cd "$(dirname "$0")/../../"
npm start
EOL
        chmod +x "ZS Parser.app/Contents/MacOS/zs-parser"
        
        # Copy icon if exists
        if [ -f "zs-parser.icns" ]; then
            cp zs-parser.icns "ZS Parser.app/Contents/Resources/"
        fi
        
        success "Application bundle created at '$(pwd)/ZS Parser.app'"
    fi
    
    # 8. Final message
    section "Installation Complete!"
    if is_macos; then
        echo -e "${GREEN}✓ Installation completed successfully!${NC}"
        echo -e "You can now run the application by double-clicking 'ZS Parser.app' in the current directory."
    else
        echo -e "${GREEN}✓ Installation completed successfully!${NC}"
        echo -e "You can now run the application by executing: ${YELLOW}npm start${NC} in this directory."
    fi
}

# Run the installation
install
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
npm start

echo -e "${GREEN}Project setup complete and application started!${NC}"