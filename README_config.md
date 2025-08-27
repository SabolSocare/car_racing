# F1 Live Timing System - Configuration Guide

## Overview

The F1 Live Timing System has been refactored to use a centralized configuration system, making it much easier to configure and customize for different environments and use cases.

## Configuration Files

### `config.py`
The main configuration file containing all system settings organized into logical sections:

- **Server Configuration**: Flask/WebSocket server settings
- **Data Configuration**: Data sources and file handling
- **Performance Configuration**: Optimization and caching settings
- **Simulation Configuration**: Race simulation timing and speed control
- **Status Detection Configuration**: Car status detection parameters
- **Ranking Configuration**: Ranking calculation settings
- **Forecasting Configuration**: Overtaking prediction settings
- **UI Configuration**: User interface settings
- **Logging Configuration**: Logging and debugging settings
- **Safety Configuration**: Resource limits and error handling

### `config_helper.py`
Interactive configuration helper with preset configurations for:
- Development environment
- Production environment
- Demo/presentation mode

## Quick Start

### 1. Basic Setup
```python
from config import config

# Change data directory
config.Data.BASE_DIR = "/path/to/your/data"

# Change server port
config.Server.PORT = 8080

# Set simulation speed
config.Simulation.DEFAULT_SPEED = 2.0  # 2x speed
```

### 2. Environment-Specific Setup
```python
from config_helper import setup_for_development, setup_for_production

# For development
setup_for_development()

# For production
setup_for_production()
```

### 3. Interactive Configuration
```bash
python config_helper.py
```

## Common Configuration Tasks

### Change Data Directory
```python
# Method 1: Direct assignment
config.Data.BASE_DIR = "/Users/username/race_data"

# Method 2: Using helper
from config_helper import set_data_directory
set_data_directory("/Users/username/race_data")
```

### Adjust Performance Settings
```python
# For better performance on slower machines
config.Performance.UPDATE_INTERVAL = 2.0      # Update every 2 seconds
config.Performance.BROADCAST_INTERVAL = 3     # Broadcast every 3rd update
config.Performance.MAX_CLIENTS = 5            # Limit concurrent clients

# For high-performance machines
config.Performance.UPDATE_INTERVAL = 0.5      # Update every 500ms
config.Performance.BROADCAST_INTERVAL = 1     # Broadcast every update
config.Performance.MAX_CLIENTS = 50           # Allow more clients
```

### Customize Simulation Speed
```python
# Set default speed
config.Simulation.DEFAULT_SPEED = 1.5  # 1.5x speed

# Change speed limits
config.Simulation.MIN_SPEED = 0.1       # Minimum 0.1x speed
config.Simulation.MAX_SPEED = 20.0      # Maximum 20x speed

# Use presets
config.Simulation.DEFAULT_SPEED = config.Simulation.SPEED_PRESETS['fast']  # 2x speed
```

### Configure Status Detection
```python
# Adjust speed thresholds
config.StatusDetection.STOPPED_SPEED_THRESHOLD = 3   # Below 3 km/h = stopped
config.StatusDetection.PIT_SPEED_THRESHOLD = 50      # Below 50 km/h = in pits

# Adjust time windows
config.StatusDetection.STATUS_WINDOW_SECONDS = 45    # 45-second analysis window
config.StatusDetection.DATA_TIMEOUT_SECONDS = 120    # 2-minute timeout = OUT
```

### Enable Debug Mode
```python
# Server debug mode
config.Server.DEBUG = True
config.Server.USE_RELOADER = True

# Logging debug mode
config.Logging.ENABLE_DEBUG_LOGGING = True
config.Logging.VERBOSE_CONSOLE_OUTPUT = True
config.Logging.LOG_TO_FILE = True
```

## Configuration Validation

The system includes built-in validation:

```python
# Check configuration
issues = config.validate_config()
if issues:
    for issue in issues:
        print(f"Configuration issue: {issue}")
else:
    print("Configuration is valid!")
```

## Environment Presets

### Development Environment
- Debug mode enabled
- Verbose logging
- Fast updates (0.5s intervals)
- Limited clients (5)
- Auto-reloader enabled

### Production Environment
- Debug mode disabled
- Optimized logging
- Standard updates (1s intervals)
- More clients (20)
- File logging enabled

### Demo Environment
- 2x simulation speed
- Fast updates for responsiveness
- Aggressive status detection
- Optimized for presentations

## File Structure

```
F1/
├── config.py              # Main configuration file
├── config_helper.py       # Interactive configuration helper
├── f1_live_ui.py          # Main application (now uses config)
└── README_config.md       # This documentation
```

## Migration from Old System

The old hardcoded values have been replaced with configuration references:

| Old Code | New Code |
|----------|----------|
| `max_clients = 10` | `config.Performance.MAX_CLIENTS` |
| `update_interval = 1.0` | `config.Performance.UPDATE_INTERVAL` |
| `simulation_speed = 1.0` | `config.Simulation.DEFAULT_SPEED` |
| `data_dir = "/path/..."` | `config.get_data_directory()` |

## Best Practices

1. **Always validate configuration** after making changes
2. **Use environment presets** for consistent setups
3. **Document custom configurations** in your deployment scripts
4. **Test configuration changes** in development first
5. **Keep backups** of working configurations

## Troubleshooting

### Common Issues

1. **Data directory not found**
   ```python
   # Check if directory exists
   import os
   if not os.path.exists(config.Data.BASE_DIR):
       print(f"Directory not found: {config.Data.BASE_DIR}")
   ```

2. **Port already in use**
   ```python
   # Change to different port
   config.Server.PORT = 5003
   ```

3. **Performance issues**
   ```python
   # Reduce update frequency
   config.Performance.UPDATE_INTERVAL = 2.0
   config.Performance.BROADCAST_INTERVAL = 4
   ```

4. **Memory issues**
   ```python
   # Reduce cache sizes
   config.Performance.DISTANCE_CACHE_SIZE = 500
   config.Performance.POSITION_CACHE_SIZE = 250
   ```

## Support

For additional help with configuration:
1. Run `python config_helper.py` for interactive setup
2. Use `config.print_config_summary()` to see current settings
3. Use `config.validate_config()` to check for issues

## Example: Complete Custom Setup

```python
from config import config

# Custom configuration for large-scale deployment
config.Server.HOST = '0.0.0.0'
config.Server.PORT = 80
config.Server.DEBUG = False

config.Data.BASE_DIR = '/opt/f1_data/race_data'

config.Performance.MAX_CLIENTS = 100
config.Performance.UPDATE_INTERVAL = 1.5
config.Performance.DISTANCE_CACHE_SIZE = 2000

config.Simulation.DEFAULT_SPEED = 1.0
config.Simulation.MAX_SPEED = 5.0

config.Logging.LOG_TO_FILE = True
config.Logging.LOG_FILE_PATH = '/var/log/f1_timing.log'

# Validate before starting
issues = config.validate_config()
if not issues:
    print("✅ Configuration ready for production!")
else:
    print("❌ Please fix configuration issues first")
```
