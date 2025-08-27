# Migration Guide: Moving to Configuration System

## Overview
The F1 Live Timing System has been updated to use a centralized configuration system. This guide helps you migrate from the old hardcoded values to the new flexible configuration.

## What Changed

### Before (Old System)
Settings were hardcoded throughout `f1_live_ui.py`:
```python
# Hardcoded values scattered throughout the file
max_clients = 10
update_interval = 1.0
simulation_speed = 1.0
data_dir = "/path/to/hardcoded/directory"
```

### After (New System)
All settings are centralized in `config.py`:
```python
# Import configuration
from config import config

# Use configuration values
max_clients = config.Performance.MAX_CLIENTS
update_interval = config.Performance.UPDATE_INTERVAL
simulation_speed = config.Simulation.DEFAULT_SPEED
data_dir = config.get_data_directory()
```

## Migration Steps

### 1. Update Your Data Directory
If you were using a custom data directory, update it in `config.py`:

**Old way:**
```python
# In f1_live_ui.py (no longer needed)
data_dir = "/your/custom/path"
```

**New way:**
```python
# In config.py or your startup script
from config import config
config.Data.BASE_DIR = "/your/custom/path"
```

### 2. Update Server Settings
**Old way:**
```python
# Hardcoded in main()
socketio.run(app, host='0.0.0.0', port=5002, debug=False)
```

**New way:**
```python
# Configured in config.py
config.Server.HOST = '0.0.0.0'
config.Server.PORT = 5002
config.Server.DEBUG = False
```

### 3. Update Performance Settings
**Old way:**
```python
# Scattered throughout the code
max_clients = 10
update_interval = 1.0
distance_cache_size = 1000
```

**New way:**
```python
# Centralized in config.py
config.Performance.MAX_CLIENTS = 10
config.Performance.UPDATE_INTERVAL = 1.0
config.Performance.DISTANCE_CACHE_SIZE = 1000
```

## Quick Migration Script

Create a file called `migrate_config.py` with your old settings:

```python
#!/usr/bin/env python3
"""
Migration script to convert old hardcoded settings to new config system
"""

from config import config

# Apply your old custom settings here
def apply_old_settings():
    """Apply your previous custom settings"""
    
    # If you had a custom data directory
    config.Data.BASE_DIR = "/Users/socaresabol/POC/test/F1/Truck_Cal/cropped_data"
    
    # If you had custom server settings
    config.Server.PORT = 5002
    config.Server.HOST = '0.0.0.0'
    config.Server.DEBUG = False
    
    # If you had custom performance settings
    config.Performance.MAX_CLIENTS = 10
    config.Performance.UPDATE_INTERVAL = 1.0
    
    # If you had custom simulation settings
    config.Simulation.DEFAULT_SPEED = 1.0
    config.Simulation.MIN_SPEED = 0.1
    config.Simulation.MAX_SPEED = 5.0
    
    # If you had custom status detection settings
    config.StatusDetection.STOPPED_SPEED_THRESHOLD = 5
    config.StatusDetection.PIT_SPEED_THRESHOLD = 60
    config.StatusDetection.DATA_TIMEOUT_SECONDS = 60
    
    print("✅ Old settings applied to new configuration system")
    
    # Validate the configuration
    issues = config.validate_config()
    if issues:
        print("❌ Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Configuration is valid!")
    
    # Show summary
    config.print_config_summary()

if __name__ == "__main__":
    apply_old_settings()
```

## Environment-Specific Configurations

### Development Environment
```python
from config_helper import setup_for_development
setup_for_development()
```

### Production Environment
```python
from config_helper import setup_for_production
setup_for_production()
```

### Custom Environment
```python
from config import config

# Apply your specific settings
config.Server.PORT = 8080
config.Data.BASE_DIR = "/production/data"
config.Performance.MAX_CLIENTS = 50
config.Logging.LOG_TO_FILE = True
```

## Common Migration Issues and Solutions

### Issue 1: Data Directory Not Found
**Problem:** Your old data directory path doesn't work
**Solution:**
```python
import os
from config import config

# Check if directory exists
if not os.path.exists(config.Data.BASE_DIR):
    print(f"Directory not found: {config.Data.BASE_DIR}")
    # Update to correct path
    config.Data.BASE_DIR = "/correct/path/to/data"
```

### Issue 2: Port Already in Use
**Problem:** Another service is using port 5002
**Solution:**
```python
config.Server.PORT = 5003  # Use different port
```

### Issue 3: Performance Issues
**Problem:** System running slowly with new defaults
**Solution:**
```python
# Reduce update frequency
config.Performance.UPDATE_INTERVAL = 2.0
config.Performance.BROADCAST_INTERVAL = 4

# Reduce cache sizes
config.Performance.DISTANCE_CACHE_SIZE = 500
config.Performance.MAX_CLIENTS = 5
```

## Verification Steps

After migration, verify everything works:

1. **Test Configuration Loading:**
   ```bash
   python config.py
   ```

2. **Test Main Application:**
   ```bash
   python f1_live_ui.py
   ```

3. **Check Configuration Helper:**
   ```bash
   python config_helper.py
   ```

4. **Validate Settings:**
   ```python
   from config import config
   issues = config.validate_config()
   if not issues:
       print("✅ Migration successful!")
   ```

## Benefits of New System

✅ **Centralized Configuration** - All settings in one place
✅ **Environment Support** - Easy dev/staging/production setups  
✅ **Validation** - Built-in configuration validation
✅ **Interactive Setup** - GUI-like configuration helper
✅ **Documentation** - Self-documenting configuration options
✅ **Backwards Compatible** - Old functionality preserved
✅ **Extensible** - Easy to add new configuration options

## Getting Help

If you encounter issues during migration:

1. **Check the configuration validation:**
   ```python
   from config import config
   print(config.validate_config())
   ```

2. **Use the interactive helper:**
   ```bash
   python config_helper.py
   ```

3. **Review the examples:**
   ```bash
   python config_examples.py
   ```

4. **Check the full documentation:**
   ```bash
   cat README_config.md
   ```
