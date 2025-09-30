# ZS Parser Build Instructions

This document provides comprehensive build instructions for the ZS Parser project, which consists of:
- **Python CLI Backend** - Command-line parser for NDJSON data
- **Electron GUI** - Desktop application interface

## Project Structure

```
FB-ndjson-parser/
├── src/zs_parser/          # Python CLI backend
│   ├── main.py             # CLI entry point
│   ├── tools.py            # Parsing logic
│   └── __init__.py
├── main.js                 # Electron main process
├── renderer.js             # Electron renderer process
├── index.html              # Electron UI
├── styles.css              # UI styling
├── preload.js              # Electron preload script
├── package.json            # Node.js dependencies
├── pyproject.toml          # Python dependencies
└── uv.lock                 # UV lock file
```

## Prerequisites

### System Requirements
- **Node.js** >= 18.0.0
- **Python** >= 3.10
- **UV** (recommended) or **pip** for Python package management

### Install UV (Recommended)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Python Backend Build

### 1. Development Setup
```bash
# Clone the repository
cd FB-ndjson-parser

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Test the CLI
```bash
# Test basic functionality
python src/zs_parser/main.py data/tik1.json --format csv -o test.csv
python src/zs_parser/main.py data/tik1.json --format json -o test.json

# Test format consistency
python test_format_consistency.py
```

### 3. Build Distribution
```bash
# Build wheel package
uv build

# Or using pip
pip install build
python -m build
```

### 4. Install from Distribution
```bash
# Install the built package
uv pip install dist/zs_parser-0.2.0-py3-none-any.whl

# Test installed CLI
zs-parser --help
zs-parser data/tik1.json -o output.csv
```

## Electron App Build

### 1. Development Setup
```bash
# Install Node.js dependencies
npm install

# Start development server
npm start
```

### 2. Build for Distribution
```bash
# Build for current platform
npm run build

# Build without publishing
npm run dist
```

### 3. Platform-Specific Builds
```bash
# Build for specific platforms
npx electron-builder --mac
npx electron-builder --win
npx electron-builder --linux
```

### 4. Build Configuration
The Electron build configuration is in `package.json`:
```json
{
  "build": {
    "appId": "com.example.zs-parser",
    "productName": "ZS Parser",
    "directories": {
      "output": "dist"
    },
    "files": [
      "main.js",
      "renderer.js", 
      "index.html",
      "styles.css",
      "src/",
      "node_modules/"
    ]
  }
}
```

## Unified Build Process

### Quick Start
```bash
# 1. Setup Python environment
uv venv && source .venv/bin/activate
uv pip install -e .

# 2. Setup Node.js environment
npm install

# 3. Test everything works
python test_format_consistency.py
npm start  # Test Electron app

# 4. Build both components
uv build                    # Python package
npm run dist               # Electron app
```

## Available Commands

### Python CLI Commands
```bash
# Basic parsing
zs-parser input.ndjson                          # Interactive mode → JSON
zs-parser input.ndjson > output.csv             # Redirect → CSV
zs-parser input.ndjson -o output.csv            # File output → CSV (inferred)
zs-parser input.ndjson -o output.json           # File output → JSON (inferred)
zs-parser input.ndjson --format csv -o out.csv  # Explicit format

# Environment variable format detection
ZS_PARSER_OUTPUT_FILE=output.csv zs-parser input.ndjson > output.csv
ZS_PARSER_OUTPUT_FILE=output.json zs-parser input.ndjson > output.json
```

### Electron App Commands
```bash
npm start          # Start development mode
npm run build      # Build for production
npm run dist       # Build distributables
```

## Testing

### Python Tests
```bash
# Run format consistency tests
python test_format_consistency.py

# Test with sample data
python src/zs_parser/main.py data/tik1.json -o test.csv
python src/zs_parser/main.py data/zeeschuimer-export-facebook.com-2025-07-28T041835.ndjson -o test.json
```

### Electron Tests
```bash
# Start the app to test functionality
npm start

# Test with sample files by dragging and dropping into the app
```

## Deployment

### Python CLI Distribution
```bash
# Build and upload to PyPI (if desired)
uv build
twine upload dist/*
```

### Electron App Distribution
```bash
# Build for all platforms
npx electron-builder --mac --win --linux

# Distributables will be in dist/ directory
ls dist/
```

### Output Files
- **Python**: `dist/zs_parser-0.2.0-py3-none-any.whl`
- **Electron macOS**: `dist/ZS Parser-1.0.0.dmg`
- **Electron Windows**: `dist/ZS Parser Setup 1.0.0.exe`
- **Electron Linux**: `dist/ZS Parser-1.0.0.AppImage`

## Troubleshooting

### Common Issues

1. **Python module not found**
   ```bash
   # Make sure you're in the virtual environment
   source .venv/bin/activate
   uv pip install -e .
   ```

2. **Electron build fails**
   ```bash
   # Clear node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **UV not found**
   ```bash
   # Install UV or use pip instead
   pip install -e .
   pip install build
   ```

4. **Permission errors on macOS/Linux**
   ```bash
   chmod +x scripts/build.sh
   ```

### Dependencies Issues
- **Python dependencies**: Defined in `pyproject.toml`
- **Node.js dependencies**: Defined in `package.json`
- **Version conflicts**: Use `uv` for Python and `npm ci` for Node.js

## Development Workflow

1. **Make changes** to Python code in `src/zs_parser/`
2. **Test changes** with `python src/zs_parser/main.py`
3. **Test Electron integration** with `npm start`
4. **Run tests** with `python test_format_consistency.py`
5. **Build for distribution** when ready

## Support

For build issues:
1. Check this documentation
2. Verify all prerequisites are installed
3. Check the project's issue tracker
4. Ensure you're using the correct Python (>=3.10) and Node.js (>=18) versions