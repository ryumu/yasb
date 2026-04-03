# AGENTS.md - YASB Reborn Development Guide

## Project Overview
YASB Reborn is a highly configurable Windows status bar / taskbar replacement written in **Python 3.14** using **PyQt6**. It features 40+ widgets, YAML configuration, CSS styling, and integrations with tiling window managers (Komorebi, GlazeWM).

## Essential Commands

### Development Setup
```bash
pip install -e .[dev]    # Install with dev dependencies
pre-commit install       # Install git hooks (ruff-check + ruff-format)
```

### Running the Application
```bash
python src/main.py       # Run the application
```

### Linting & Formatting (Ruff)
```bash
ruff format .            # Format all code
ruff check .             # Run lint checks
ruff check --fix .       # Auto-fix lint issues
```

### Building
```bash
cd src && python build.py build        # Build executables (cx-Freeze)
cd src && python build.py bdist_msi    # Build MSI installer
```

### Testing
- **No automated test framework currently exists.** Manual testing is required.
- Test on Windows with PyQt6 installed.
- Validate config changes against `schema.json`.

## Code Style Guidelines

### Linter & Formatter: Ruff
- **Line length:** 120 characters
- **Quote style:** Double quotes
- **Indent style:** Spaces (4 spaces)
- **Target version:** Python 3.14
- **Lint rules:** `I` (isort/import ordering) + `F` (pyflakes) only
- **Ignored rules:** `F405`, `F403` (star imports), `E741` (ambiguous names)

### Imports
- Imports are auto-sorted by Ruff's `I` rule (standard library → third-party → local)
- Use absolute imports from `core.` prefix: `from core.widgets.base import BaseWidget`
- Group imports logically with blank lines between groups

### Naming Conventions
- **Classes:** PascalCase (`BaseWidget`, `BarManager`, `EventService`)
- **Functions/Methods:** snake_case (`get_screen_geometry`, `load_config`)
- **Constants:** UPPER_SNAKE_CASE (`BUILD_VERSION`, `APP_NAME`)
- **Private members:** Leading underscore (`_init_ui`, `_event_handler`)

### Type Hints
- Use Python 3.14 type hints consistently
- Prefer `typing` module imports for complex types
- Add return type annotations to all functions
- Use `Optional[T]` for nullable types

### Error Handling
- Use specific exception types, not bare `except:`
- Log errors using the app's logger from `core.log`
- Show user-facing errors via `alert_dialog` utilities
- Validate config with Pydantic schemas in `core.validation`

### Async Patterns
- Uses `qasync` to integrate PyQt6 event loop with `asyncio`
- Use `async def` for I/O-bound operations
- Prefer `QTimer` for periodic UI updates over async loops

## Architecture Overview

### Key Directories
```
src/
├── main.py              # Application entry point
├── cli.py               # CLI tool (yasbc)
├── core/
│   ├── application.py   # YASBApplication (Qt app wrapper)
│   ├── bar.py           # Bar widget class
│   ├── bar_manager.py   # Manages multiple bars
│   ├── config.py        # Configuration loading
│   ├── event_service.py # Pub/sub event system
│   ├── widgets/
│   │   ├── base.py      # BaseWidget (all widgets inherit)
│   │   ├── registry.py  # Widget class registry
│   │   ├── yasb/        # Built-in widgets
│   │   ├── komorebi/    # Komorebi WM widgets
│   │   └── glazewm/     # GlazeWM widgets
│   ├── utils/           # Utilities (controller, shell, win32)
│   ├── ui/              # Style management, windows
│   └── validation/      # Pydantic validation schemas
```

### Widget Development
- All widgets inherit from `BaseWidget` (`src/core/widgets/base.py`)
- Auto-registration via `__init_subclass__` into `WIDGET_REGISTRY`
- Widgets use YAML config + CSS styling
- Use `EventService` for inter-widget communication

### Configuration
- YAML-based (`config.yaml`) with Pydantic validation
- JSON schema (`schema.json`) for IDE autocomplete
- Styles defined in CSS (`styles.css`)

## Important Patterns
- **Single instance:** Enforced via Windows mutex (`CreateMutexW`)
- **File watching:** Config/style changes trigger hot-reload via `watchdog`
- **CLI communication:** Named pipes between `yasbc` and main app
- **Windows-only:** Uses pywin32, WinRT, and Windows-specific APIs
