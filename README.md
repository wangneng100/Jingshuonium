# Jingshuonium

A 2D Minecraft-like game built with Pygame.

## Features

- 2D block-based world generation
- Mining and crafting system
- Player inventory management
- Day/night cycle
- Multiple enemy types
- Various tools and weapons
- UI interfaces for crafting, chests, and furnaces

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Install from source

1. Clone the repository:
   ```bash
   git clone https://github.com/wangneng100/Jingshuonium.git
   cd Jingshuonium
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the game:
   ```bash
   python run_game.py
   ```
   
   Or using the legacy entry point:
   ```bash
   python main.py
   ```

### Development Installation

For development, install additional dependencies:

```bash
pip install -r requirements-dev.txt
```

## Project Structure

```
Jingshuonium/
├── src/
│   └── game/
│       ├── core/           # Core game modules (config, definitions, assets)
│       ├── entities/       # Game entities (player, enemies)
│       ├── ui/            # User interface components
│       ├── world/         # World generation and management
│       └── systems/       # Game systems (physics, rendering, etc.)
├── assets/
│   ├── textures/          # Game textures
│   ├── sounds/            # Sound effects and music
│   └── fonts/             # Game fonts
├── saves/                 # Save game files
├── tests/                 # Test files
├── docs/                  # Documentation
├── main.py               # Main entry point
└── requirements.txt      # Python dependencies
```

## Controls

- **WASD** - Move player
- **Mouse** - Aim and interact
- **Left Click** - Mine blocks / Attack
- **Right Click** - Place blocks
- **E** - Open inventory
- **ESC** - Pause menu
- **1-9** - Select hotbar items

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
```

### Linting

```bash
flake8 src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Pygame
- Uses Perlin noise for world generation
- Inspired by Minecraft and similar block-based games