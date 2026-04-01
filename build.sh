#!/bin/bash

# ZS Parser Unified Build Script
# Builds both Python backend and Electron frontend

set -e  # Exit on any error

echo "🚀 ZS Parser Build Script"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect the operating system
detect_os() {
    case "$OSTYPE" in
        darwin*)  echo "macos" ;;
        linux*)   echo "linux" ;;
        msys*)    echo "windows" ;;
        cygwin*)  echo "windows" ;;
        *)        echo "unknown" ;;
    esac
}

OS=$(detect_os)
print_status "Detected OS: $OS"

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3 not found. Please install Python >= 3.10"
        exit 1
    fi
    
    # Check Node.js
    if command_exists node; then
        NODE_VERSION=$(node --version)
        print_success "Node.js $NODE_VERSION found"
    else
        print_error "Node.js not found. Please install Node.js >= 18"
        exit 1
    fi
    
    # Check npm
    if command_exists npm; then
        NPM_VERSION=$(npm --version)
        print_success "npm $NPM_VERSION found"
    else
        print_error "npm not found"
        exit 1
    fi
    
    # Check uv (preferred) or pip
    if command_exists uv; then
        UV_VERSION=$(uv --version 2>/dev/null | cut -d' ' -f2 || echo "unknown")
        print_success "uv $UV_VERSION found (preferred)"
        USE_UV=true
    elif command_exists pip; then
        PIP_VERSION=$(pip --version | cut -d' ' -f2)
        print_success "pip $PIP_VERSION found"
        USE_UV=false
    else
        print_error "Neither uv nor pip found. Please install one of them"
        exit 1
    fi
}

# Setup Python environment
setup_python() {
    print_status "Setting up Python environment..."
    
    if [ "$USE_UV" = true ]; then
        print_status "Using uv for Python package management"
        
        # Create virtual environment if it doesn't exist
        if [ ! -d ".venv" ]; then
            print_status "Creating virtual environment with uv..."
            uv venv
        fi
        
        # Activate virtual environment
        if [ "$OS" = "windows" ]; then
            source .venv/Scripts/activate
        else
            source .venv/bin/activate
        fi
        
        # Install dependencies
        print_status "Installing Python dependencies with uv..."
        uv pip install -e .
    else
        print_status "Using pip for Python package management"
        
        # Create virtual environment if it doesn't exist
        if [ ! -d ".venv" ]; then
            print_status "Creating virtual environment..."
            python3 -m venv .venv
        fi
        
        # Activate virtual environment
        if [ "$OS" = "windows" ]; then
            source .venv/Scripts/activate
        else
            source .venv/bin/activate
        fi
        
        # Upgrade pip
        pip install --upgrade pip
        
        # Install dependencies
        print_status "Installing Python dependencies..."
        pip install -e .
        pip install build
    fi
    
    print_success "Python environment setup complete"
}

# Setup Node.js environment
setup_nodejs() {
    print_status "Setting up Node.js environment..."
    
    # Install dependencies
    if [ -f "package-lock.json" ]; then
        print_status "Installing Node.js dependencies (using npm ci)..."
        npm ci
    else
        print_status "Installing Node.js dependencies (using npm install)..."
        npm install
    fi
    
    print_success "Node.js environment setup complete"
}

# Run tests
run_tests() {
    print_status "Running tests..."
    
    # Test Python CLI
    print_status "Testing Python CLI..."
    if [ -f "test_format_consistency.py" ]; then
        python test_format_consistency.py
        print_success "Python tests passed"
    else
        print_warning "No Python tests found"
    fi
    
    # Basic CLI test
    if [ -f "data/tik1.json" ]; then
        print_status "Testing basic CLI functionality..."
        python src/zs_parser/main.py data/tik1.json --format csv -o build_test.csv
        if [ -f "build_test.csv" ]; then
            rm build_test.csv
            print_success "Basic CLI test passed"
        else
            print_error "Basic CLI test failed"
            exit 1
        fi
    else
        print_warning "No test data found, skipping CLI test"
    fi
}

# Build Python package
build_python() {
    print_status "Building Python package..."
    
    # Clean previous builds
    rm -rf dist/ build/ *.egg-info/ src/*.egg-info/
    
    if [ "$USE_UV" = true ]; then
        uv build
    else
        python -m build
    fi
    
    # Check if build succeeded
    if [ -d "dist" ] && [ "$(ls -A dist)" ]; then
        print_success "Python package built successfully"
        print_status "Built packages:"
        ls -la dist/
    else
        print_error "Python package build failed"
        exit 1
    fi
}

# Build Electron app
build_electron() {
    print_status "Building Electron application..."
    
    # Build for current platform
    npm run dist
    
    # Check if build succeeded
    if [ -d "dist" ] && find dist -name "*.dmg" -o -name "*.exe" -o -name "*.AppImage" -o -name "*.deb" -o -name "*.rpm" | grep -q .; then
        print_success "Electron application built successfully"
        print_status "Built applications:"
        find dist -name "*.dmg" -o -name "*.exe" -o -name "*.AppImage" -o -name "*.deb" -o -name "*.rpm" -exec ls -la {} \;
    else
        print_error "Electron application build failed"
        exit 1
    fi
}

# Clean build artifacts
clean() {
    print_status "Cleaning build artifacts..."
    rm -rf dist/ build/ *.egg-info/ src/*.egg-info/
    rm -rf node_modules/
    print_success "Clean complete"
}

# Main build function
build_all() {
    print_status "Starting unified build process..."
    
    check_prerequisites
    setup_python
    setup_nodejs
    run_tests
    build_python
    build_electron
    
    print_success "🎉 Build completed successfully!"
    print_status "Build artifacts:"
    echo "  Python: $(ls dist/*.whl 2>/dev/null | head -1 || echo 'No wheel found')"
    echo "  Electron: $(find dist -name '*.dmg' -o -name '*.exe' -o -name '*.AppImage' 2>/dev/null | head -1 || echo 'No app found')"
}

# Parse command line arguments
case "${1:-build}" in
    "clean")
        clean
        ;;
    "setup")
        check_prerequisites
        setup_python
        setup_nodejs
        ;;
    "test")
        check_prerequisites
        setup_python
        run_tests
        ;;
    "python")
        check_prerequisites
        setup_python
        build_python
        ;;
    "electron")
        check_prerequisites
        setup_nodejs
        build_electron
        ;;
    "build"|"")
        build_all
        ;;
    "help"|"-h"|"--help")
        echo "ZS Parser Build Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  build     Build both Python and Electron (default)"
        echo "  setup     Setup development environments only"
        echo "  test      Run tests only"
        echo "  python    Build Python package only"
        echo "  electron  Build Electron app only"
        echo "  clean     Clean build artifacts"
        echo "  help      Show this help message"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac