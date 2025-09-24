# Project Structure Documentation

## Overview

This document describes the restructured Jingshuonium project following Python best practices.

## Directory Structure

```
Jingshuonium/
│
├── README.md                 # Project documentation
├── setup.py                  # Package installation script
├── pyproject.toml           # Modern Python project configuration
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── .gitignore              # Git ignore rules
├── .flake8                 # Flake8 configuration
├── Makefile                # Development automation
├── main.py                 # Legacy entry point (kept for compatibility)
├── run_game.py             # New launcher script
│
├── assets/                 # Game assets
│   ├── textures/          # Game textures and sprites
│   ├── sounds/            # Audio files
│   └── fonts/             # Font files
│
├── saves/                 # Save game files
│
├── src/                   # Source code
│   └── game/
│       ├── __init__.py
│       ├── core/          # Core game modules
│       │   ├── __init__.py
│       │   ├── config.py      # Game configuration
│       │   ├── definitions.py # Game constants and definitions
│       │   └── assets.py      # Asset loading and management
│       │
│       ├── entities/      # Game entities
│       │   ├── __init__.py
│       │   ├── player.py      # Player controller
│       │   └── enemies.py     # Enemy controllers
│       │
│       ├── ui/            # User interface
│       │   ├── __init__.py
│       │   ├── menu_utils.py  # UI utilities
│       │   ├── base_ui.py     # Base UI components
│       │   ├── hud.py         # Heads-up display
│       │   ├── inventory.py   # Inventory system
│       │   ├── crafting_ui.py # Crafting interface
│       │   ├── chest_ui.py    # Chest interface
│       │   ├── furnace_ui.py  # Furnace interface
│       │   ├── pause_menu.py  # Pause menu
│       │   ├── options_menu.py # Options menu
│       │   └── skill_tree_ui.py # Skill tree interface
│       │
│       ├── world/         # World generation and management
│       │   └── __init__.py
│       │
│       └── systems/       # Game systems
│           └── __init__.py
│
├── tests/                 # Test files
│   ├── __init__.py
│   └── test_imports.py    # Import tests
│
└── docs/                  # Documentation
    └── project_structure.md
```

## Module Organization

### Core Modules (`src/game/core/`)
- **config.py**: Game configuration constants (window size, physics, etc.)
- **definitions.py**: Game definitions (recipes, enemy stats, etc.)
- **assets.py**: Asset loading and management system

### Entities (`src/game/entities/`)
- **player.py**: Player controller and related functionality
- **enemies.py**: Enemy AI and behavior systems

### UI System (`src/game/ui/`)
- **menu_utils.py**: Base UI components and utilities
- **base_ui.py**: Core UI classes
- **hud.py**: Game HUD elements (health bar, hotbar, etc.)
- **inventory.py**: Inventory management system
- **[feature]_ui.py**: Specific UI interfaces for game features

### World System (`src/game/world/`)
- Future location for world generation, chunk management, etc.

### Systems (`src/game/systems/`)
- Future location for game systems (physics, rendering, audio, etc.)

## Key Benefits of This Structure

1. **Modularity**: Code is organized into logical modules
2. **Scalability**: Easy to add new features without cluttering
3. **Maintainability**: Clear separation of concerns
4. **Testing**: Structured for easy unit testing
5. **Distribution**: Proper package structure for installation
6. **Standards**: Follows Python packaging best practices

## Development Workflow

### Setting Up Development Environment
```bash
# Install development dependencies
make install-dev

# Or manually:
pip install -r requirements-dev.txt
```

### Running the Game
```bash
# Using the new launcher
python run_game.py

# Or using the legacy entry point
python main.py

# Or using make
make run
```

### Code Quality
```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test
```

### Building Distribution
```bash
make build
```

## Migration Notes

- The main game logic remains in `main.py` for now to maintain compatibility
- All imports in `main.py` have been updated to use the new structure
- Asset paths have been updated to use the new `assets/` directory
- Old directories (`texture/`, `sound/`, `entities/`) have been removed
- Save files are now organized in the `saves/` directory

## Future Improvements

1. **Break down main.py**: The main game loop should be split into smaller modules
2. **Implement systems**: Move game systems into `src/game/systems/`
3. **World management**: Implement proper world generation in `src/game/world/`
4. **Type hints**: Add type annotations throughout the codebase
5. **Tests**: Add comprehensive test coverage
6. **Documentation**: Add docstrings and API documentation