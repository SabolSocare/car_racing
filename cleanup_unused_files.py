#!/usr/bin/env python3
"""
F1 Live Timing System - Cleanup Script
Removes unused files and provides migration guidance
"""

import os
import shutil
from datetime import datetime


def backup_file(file_path, backup_dir="backup"):
    """Create a backup of a file before deletion"""
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    filename = os.path.basename(file_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{timestamp}_{filename}"
    backup_path = os.path.join(backup_dir, backup_name)
    
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backed up {filename} to {backup_path}")


def remove_unused_files():
    """Remove files that are no longer needed after modularization"""
    
    # Files that are now redundant due to modularization
    unused_files = [
        "F1_ranking_system.py",  # Functionality moved to core/timing_engine.py
        "f1_demo.py",           # Simple demo, not needed for main system
        "interval_calculator.py" # Functionality integrated into core modules
    ]
    
    # Test files (unless being actively used)
    test_files = [
        "test_forecast.py",
        "test_overtake_analysis.py", 
        "test_speed_control.py",
        "test_timing_accuracy.py"
    ]
    
    print("🧹 F1 Live Timing System - File Cleanup")
    print("=" * 45)
    
    print("\n📦 Files identified for removal:")
    print("\nUnused/Redundant files:")
    for file in unused_files:
        if os.path.exists(file):
            print(f"  ❌ {file} - Functionality moved to core modules")
        else:
            print(f"  ❓ {file} - File not found")
    
    print("\nTest files:")
    for file in test_files:
        if os.path.exists(file):
            print(f"  🧪 {file} - Test file (consider keeping if actively used)")
        else:
            print(f"  ❓ {file} - File not found")
    
    # Ask for confirmation
    print("\n⚠️  WARNING: This will permanently remove the above files!")
    print("Files will be backed up to 'backup/' directory before removal.")
    response = input("\nProceed with cleanup? (y/N): ").strip().lower()
    
    if response not in ['y', 'yes']:
        print("❌ Cleanup cancelled")
        return
    
    # Remove unused files
    removed_count = 0
    
    print("\n🗑️  Removing unused files...")
    for file in unused_files:
        if os.path.exists(file):
            backup_file(file)
            os.remove(file)
            print(f"✅ Removed {file}")
            removed_count += 1
    
    # Ask about test files separately
    if any(os.path.exists(f) for f in test_files):
        test_response = input("\nRemove test files too? (y/N): ").strip().lower()
        if test_response in ['y', 'yes']:
            for file in test_files:
                if os.path.exists(file):
                    backup_file(file)
                    os.remove(file)
                    print(f"✅ Removed {file}")
                    removed_count += 1
    
    print(f"\n✅ Cleanup complete! Removed {removed_count} files.")
    print("📁 Backup files are available in the 'backup/' directory.")


def show_migration_info():
    """Show information about the new modular structure"""
    print("\n🏗️  NEW MODULAR STRUCTURE")
    print("=" * 30)
    
    print("""
📁 F1 Live Timing System (Modular)
├── f1_live_ui_modular.py    # 🆕 New main entry point
├── f1_live_ui.py            # 📝 Original file (keep as reference)
├── config.py                # ⚙️  Configuration (unchanged)
├── web_routes.py            # 🆕 Flask routes and API endpoints
├── websocket_handlers.py    # 🆕 SocketIO event handlers
├── core/                    # 🆕 Core business logic modules
│   ├── __init__.py          # 🆕 Core module exports
│   ├── timing_engine.py     # 🆕 Main timing engine (from f1_live_ui.py)
│   ├── performance_monitor.py # 🆕 Performance monitoring
│   ├── car_status.py        # 🆕 Car status detection
│   └── forecasting.py       # 🆕 Overtaking predictions
├── static/                  # 🎨 CSS and static files (unchanged)
├── templates/               # 📄 HTML templates (unchanged)
└── Truck_Cal/              # 📊 Data files (unchanged)
""")
    
    print("\n🔄 MIGRATION STEPS")
    print("=" * 20)
    
    print("""
1. ✅ Core modules created in core/ directory
2. ✅ Web routes extracted to web_routes.py
3. ✅ WebSocket handlers extracted to websocket_handlers.py
4. ✅ New modular main file: f1_live_ui_modular.py

To use the new modular system:
  python f1_live_ui_modular.py

To keep using the original:
  python f1_live_ui.py
""")
    
    print("\n📋 WHAT'S DIFFERENT")
    print("=" * 20)
    
    print("""
✨ Improvements:
- Better code organization and maintainability
- Easier to test individual components  
- Cleaner separation of concerns
- Configuration is centralized
- Performance monitoring is modular
- Easier to extend with new features

🔧 Functionality:
- All original features preserved
- Same API endpoints and WebSocket events
- Same configuration options
- Same HTML templates and styling
- Same data processing logic
""")
    
    print("\n⚙️  HELPER FILES KEPT")
    print("=" * 20)
    
    print("""
These files are kept as they provide useful utilities:
- config_helper.py    # Interactive configuration
- config_examples.py  # Configuration examples  
- README_config.md    # Configuration documentation
- MIGRATION_GUIDE.md  # Migration instructions
""")


def create_migration_summary():
    """Create a summary file of the migration"""
    summary = """# F1 Live Timing System - Migration Summary

## Date: {date}

## Changes Made

### ✅ New Modular Structure Created
- `core/` directory with modular components
- `f1_live_ui_modular.py` as new main entry point
- `web_routes.py` for Flask routes
- `websocket_handlers.py` for SocketIO events

### 🗑️  Files Removed
- `F1_ranking_system.py` → Functionality moved to `core/timing_engine.py`
- `f1_demo.py` → Simple demo, functionality available in main system
- `interval_calculator.py` → Functionality integrated into core modules

### 📁 Files Kept
- `f1_live_ui.py` → Original file kept as reference
- `config.py` → Configuration system (unchanged)
- `config_helper.py` → Interactive configuration utility
- `config_examples.py` → Configuration examples
- All template and static files
- All data files in Truck_Cal/

### 🚀 How to Use

#### New Modular System (Recommended)
```bash
python f1_live_ui_modular.py
```

#### Original System (Fallback)
```bash
python f1_live_ui.py
```

## Benefits of Modular Structure

1. **Better Organization**: Code is split into logical modules
2. **Easier Maintenance**: Each module has a specific responsibility
3. **Improved Testability**: Individual components can be tested separately
4. **Cleaner Code**: Reduced file size and better readability
5. **Easier Extension**: New features can be added as separate modules

## Module Responsibilities

- `core/timing_engine.py`: Main timing calculations and race logic
- `core/car_status.py`: Car status detection (RUNNING, STOPPED, etc.)
- `core/forecasting.py`: Overtaking predictions and analysis
- `core/performance_monitor.py`: System performance monitoring
- `web_routes.py`: All Flask HTTP routes and API endpoints
- `websocket_handlers.py`: Real-time WebSocket event handling

## Configuration

Configuration remains the same using `config.py`. Use the helper utilities:
- `python config_helper.py` for interactive setup
- Import examples from `config_examples.py`

## Rollback

If you need to rollback:
1. The original `f1_live_ui.py` file is preserved
2. Backup files are in the `backup/` directory
3. Simply use `python f1_live_ui.py` to use the original system
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    with open("MIGRATION_SUMMARY.md", "w") as f:
        f.write(summary)
    
    print("📝 Created MIGRATION_SUMMARY.md with detailed information")


def main():
    """Main cleanup function"""
    print("🏎️  F1 Live Timing System - Modularization Complete!")
    print("=" * 55)
    
    show_migration_info()
    
    response = input("\nWould you like to clean up unused files? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        remove_unused_files()
    
    create_migration_summary()
    
    print("\n🎉 Modularization and cleanup complete!")
    print("\n📚 Next steps:")
    print("1. Test the new modular system: python f1_live_ui_modular.py")
    print("2. Read MIGRATION_SUMMARY.md for detailed information")
    print("3. Use config_helper.py for configuration changes")
    print("4. The original f1_live_ui.py is preserved as backup")


if __name__ == "__main__":
    main()
