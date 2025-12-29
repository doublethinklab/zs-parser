#!/bin/bash
# ZS Parser GUI Launcher

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run the GUI application
python3 zs_parser_gui.py
