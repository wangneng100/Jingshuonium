#!/usr/bin/env python3
"""
Jingshuonium Game Launcher

This script serves as the main entry point for the Jingshuonium game.
It ensures proper path setup and handles import errors gracefully.
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """Add the project root to Python path for proper imports."""
    project_root = Path(__file__).parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import pygame
        import perlin_noise
    except ImportError as e:
        print(f"Error: Missing required dependency: {e}")
        print("Please install dependencies using:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

def main():
    """Main entry point for the game."""
    # Setup environment
    setup_python_path()
    check_dependencies()
    
    # Import and run the main game module
    try:
        from src.game.main import main as game_main
        game_main()
    except ImportError:
        # Fallback to the old main.py structure if new one doesn't exist
        import main as old_main
        if hasattr(old_main, 'main_menu'):
            old_main.main_menu()
        else:
            print("Error: Could not find main game entry point")
            sys.exit(1)

if __name__ == "__main__":
    main()