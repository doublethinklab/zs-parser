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

# Build function
build() {
    section "Building ZS Parser Package"
    
    # 1. Check prerequisites
    status "Checking prerequisites..."
    if ! command_exists node || ! command_exists npm; then
        error "Node.js and npm are required for building the package."
    fi
    
    if ! command_exists python3; then
        error "Python 3 is required for building the package."
    fi
    
    # 2. Clean previous builds
    status "Cleaning previous builds..."
    rm -rf dist/ build/ *.dmg *.AppImage *.exe
    
    # 3. Install dependencies
    status "Installing dependencies..."
    npm install
    
    # 4. Build the Electron app
    section "Building Electron Application"
    if is_macos; then
        # Build for macOS
        status "Building macOS application..."
        npm run dist -- -m
        
        # Create DMG if on macOS
        if command_exists create-dmg; then
            status "Creating DMG package..."
            mkdir -p "ZS Parser"
            cp -R "dist/mac/ZS Parser.app" "ZS Parser/"
            create-dmg \
                --volname "ZS Parser" \
                --volicon "zs-parser.icns" \
                --window-pos 200 120 \
                --window-size 800 400 \
                --icon-size 100 \
                --icon "ZS Parser.app" 200 190 \
                --hide-extension "ZS Parser.app" \
                --app-drop-link 600 185 \
                "ZS-Parser.dmg" \
                "ZS Parser/"
            rm -rf "ZS Parser"
            success "DMG package created: ZS-Parser.dmg"
        fi
    else
        # Build for Linux and Windows
        status "Building for Linux..."
        npm run dist -- -l
        
        if command_exists docker; then
            status "Building for Windows (using Docker)..."
            docker run --rm -v "${PWD}":/project -w /project electronuserland/builder:wine /bin/bash -c "npm run dist -- -w"
        else
            status "Skipping Windows build (Docker not found)"
        fi
    fi
    
    # 5. Create Python package
    section "Creating Python Package"
    if [ -f "pyproject.toml" ]; then
        status "Building Python package..."
        python -m build --wheel --outdir dist/
        success "Python wheel package created in dist/ directory"
    fi
    
    # 6. Create final package
    section "Creating Final Package"
    PACKAGE_DIR="zs-parser-$(date +%Y%m%d)"
    mkdir -p "$PACKAGE_DIR"
    
    # Copy relevant files
    if is_macos; then
        cp -R "dist/mac/ZS Parser.app" "$PACKAGE_DIR/" || true
        [ -f "ZS-Parser.dmg" ] && cp "ZS-Parser.dmg" "$PACKAGE_DIR/"
    else
        cp -R dist/linux* "$PACKAGE_DIR/" 2>/dev/null || true
        cp -R dist/win* "$PACKAGE_DIR/" 2>/dev/null || true
    fi
    
    # Copy Python package
    cp dist/*.whl "$PACKAGE_DIR/" 2>/dev/null || true
    
    # Copy documentation and license
    [ -f "README.md" ] && cp README.md "$PACKAGE_DIR/"
    [ -f "LICENSE" ] && cp LICENSE "$PACKAGE_DIR/"
    
    # Create install script
    cat > "$PACKAGE_DIR/INSTALL" << 'EOL'
#!/bin/bash
# Installation instructions for ZS Parser

echo "ZS Parser Installation"
echo "====================="

echo "1. Python Package (required for CLI usage)"
if command -v pip3 &> /dev/null; then
    echo "Installing Python package..."
    pip3 install --user zs_parser-*.whl
else
    echo "Python package installation requires pip3"
fi

echo -e "\n2. Desktop Application"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "On macOS, please drag the 'ZS Parser.app' to your Applications folder."
else
    echo "For Linux, you can run the AppImage directly."
    echo "For Windows, run the installer in the win-unpacked directory."
fi

# Add more installation instructions as needed
EOL

    chmod +x "$PACKAGE_DIR/INSTALL"
    
    # Create archive
    status "Creating final archive..."
    if is_macos; then
        zip -r "${PACKAGE_DIR}.zip" "$PACKAGE_DIR"
    else
        tar -czf "${PACKAGE_DIR}.tar.gz" "$PACKAGE_DIR"
    fi
    
    # Cleanup
    rm -rf "$PACKAGE_DIR"
    
    section "Build Complete!"
    if is_macos; then
        success "Build completed successfully! Final package: ${PACKAGE_DIR}.zip"
        echo "To install on macOS:"
        echo "  1. Double-click 'ZS-Parser.dmg' and drag the app to your Applications folder"
    else
        success "Build completed successfully! Final package: ${PACKAGE_DIR}.tar.gz"
        echo "To install on Linux:"
        echo "  1. Extract the archive: tar -xzf ${PACKAGE_DIR}.tar.gz"
        echo "  2. Run the AppImage or install the .deb/.rpm package"
    fi
    echo -e "\nFor command-line usage, install the Python package using pip3."
}

# Run the build
build
