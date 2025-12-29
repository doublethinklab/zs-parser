#!/usr/bin/env python3
"""
ZS Parser GUI Setup Script
Installs required dependencies for the CustomTkinter version
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages for the GUI application"""
    requirements = [
        "customtkinter>=5.2.0",
        "tkinterdnd2>=0.3.0",  # For drag and drop functionality
    ]
    
    print("Installing GUI dependencies...")
    for requirement in requirements:
        print(f"Installing {requirement}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", requirement])
    
    print("GUI dependencies installed successfully!")

def create_desktop_entry():
    """Create desktop entry for Linux systems"""
    if sys.platform.startswith('linux'):
        desktop_entry = f"""[Desktop Entry]
Name=ZS Parser GUI
Comment=Parse data from Zeeschuimer with GUI
Exec=python3 {os.path.abspath('zs_parser_gui.py')}
Icon={os.path.abspath('zs-parser.png')}
Terminal=false
Type=Application
Categories=Utility;
"""
        desktop_path = os.path.expanduser("~/.local/share/applications/zs-parser-gui.desktop")
        os.makedirs(os.path.dirname(desktop_path), exist_ok=True)
        
        with open(desktop_path, 'w') as f:
            f.write(desktop_entry)
        
        os.chmod(desktop_path, 0o755)
        print(f"Desktop entry created at: {desktop_path}")

if __name__ == "__main__":
    try:
        install_requirements()
        create_desktop_entry()
        print("\n✓ Setup completed successfully!")
        print("You can now run: python3 zs_parser_gui.py")
    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)
