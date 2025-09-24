import pytest
import sys
import os

# Add the project root to the path for testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_import_config():
    """Test that core config can be imported."""
    from src.game.core import config
    assert hasattr(config, 'WINDOW_SIZE')
    assert hasattr(config, 'WINDOW_TITLE')


def test_import_definitions():
    """Test that core definitions can be imported."""
    from src.game.core import definitions
    assert hasattr(definitions, 'CRAFTING_RECIPES')


def test_import_ui_components():
    """Test that UI components can be imported."""
    from src.game.ui import menu_utils
    assert hasattr(menu_utils, 'Button')