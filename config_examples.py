#!/usr/bin/env python3
"""
F1 Live Timing System - Configuration Examples
Demonstrates different ways to configure the system
"""

def example_development_setup():
    """Example: Development environment setup"""
    print("=== Development Environment Setup ===")
    
    from config import config
    
    # Development-friendly settings
    config.Server.DEBUG = True
    config.Server.PORT = 5003  # Different port to avoid conflicts
    config.Server.USE_RELOADER = True
    
    # Faster updates for development
    config.Performance.UPDATE_INTERVAL = 0.5
    config.Performance.BROADCAST_INTERVAL = 1
    config.Performance.MAX_CLIENTS = 3  # Lower for testing
    
    # Verbose logging
    config.Logging.ENABLE_DEBUG_LOGGING = True
    config.Logging.VERBOSE_CONSOLE_OUTPUT = True
    
    # Fast simulation for testing
    config.Simulation.DEFAULT_SPEED = 2.0
    
    print("✅ Development configuration applied")
    config.print_config_summary()

def example_production_setup():
    """Example: Production environment setup"""
    print("=== Production Environment Setup ===")
    
    from config import config
    
    # Production settings
    config.Server.DEBUG = False
    config.Server.PORT = 80  # Standard HTTP port
    config.Server.HOST = '0.0.0.0'  # Accept connections from anywhere
    
    # Optimized performance
    config.Performance.UPDATE_INTERVAL = 1.0
    config.Performance.BROADCAST_INTERVAL = 2
    config.Performance.MAX_CLIENTS = 50
    
    # Production logging
    config.Logging.ENABLE_DEBUG_LOGGING = False
    config.Logging.LOG_TO_FILE = True
    config.Logging.LOG_FILE_PATH = '/var/log/f1_timing.log'
    
    # Standard simulation speed
    config.Simulation.DEFAULT_SPEED = 1.0
    
    print("✅ Production configuration applied")
    config.print_config_summary()

def example_demo_setup():
    """Example: Demo/presentation setup"""
    print("=== Demo/Presentation Setup ===")
    
    from config import config
    
    # Demo settings for engaging presentations
    config.Simulation.DEFAULT_SPEED = 3.0  # 3x speed for demos
    config.Simulation.MIN_SPEED = 0.5
    config.Simulation.MAX_SPEED = 10.0
    
    # Responsive updates
    config.Performance.UPDATE_INTERVAL = 0.5
    config.Performance.BROADCAST_INTERVAL = 1
    
    # Aggressive status detection for quick changes
    config.StatusDetection.STATUS_WINDOW_SECONDS = 10
    config.StatusDetection.DATA_TIMEOUT_SECONDS = 20
    
    # Enhanced forecasting for demos
    config.Forecasting.EXCELLENT_FORECAST_THRESHOLD = 15  # Show more "excellent" forecasts
    config.Forecasting.FORECAST_TIME_WINDOW = 300
    
    print("✅ Demo configuration applied")
    config.print_config_summary()

def example_custom_data_setup():
    """Example: Custom data directory setup"""
    print("=== Custom Data Directory Setup ===")
    
    from config import config
    import os
    
    # Get the current script directory and project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = current_dir  # Assuming this script is in the project root
    
    # Different data directories for different scenarios (portable paths)
    data_dirs = {
        'race_2023': os.path.join(project_root, 'data', '2023_races'),
        'race_2024': os.path.join(project_root, 'data', '2024_races'),
        'test_data': os.path.join(project_root, 'Truck_Cal', 'cropped_data'),
        'backup_data': os.path.join(project_root, 'backup_data'),
        'user_data': os.path.expanduser('~/F1_Racing_Data'),  # User's home directory
        'temp_data': os.path.join(os.getcwd(), 'temp_racing_data'),  # Current working directory
        'env_data': os.getenv('F1_DATA_PATH', os.path.join(project_root, 'Truck_Cal', 'cropped_data'))  # From environment variable
    }
    
    # Choose data set
    chosen_data = 'test_data'  # Change this to switch data sets
    
    # Print available data directories
    print("Available data directories:")
    for key, path in data_dirs.items():
        exists = "✅" if os.path.exists(path) else "❌"
        print(f"  {key:12} -> {path} {exists}")
    
    if chosen_data in data_dirs:
        new_dir = data_dirs[chosen_data]
        if os.path.exists(new_dir):
            config.Data.BASE_DIR = new_dir
            print(f"\n✅ Data directory set to: {new_dir}")
        else:
            print(f"\n❌ Directory not found: {new_dir}")
            print(f"Using default: {config.Data.BASE_DIR}")
            
            # Try to create the directory if it's within the project
            if not os.path.isabs(new_dir) or project_root in new_dir:
                try:
                    os.makedirs(new_dir, exist_ok=True)
                    print(f"📁 Created directory: {new_dir}")
                except Exception as e:
                    print(f"❌ Could not create directory: {e}")
    else:
        print(f"\n❌ Unknown data set: {chosen_data}")
        print(f"Available options: {list(data_dirs.keys())}")
    
    print(f"\nCurrent data directory: {config.Data.BASE_DIR}")


def get_portable_data_dir(data_type='test_data'):
    """
    Helper function to get a portable data directory path
    
    Args:
        data_type (str): Type of data directory ('test_data', 'race_2023', etc.)
    
    Returns:
        str: Absolute path to the data directory
    
    Example:
        from config_examples import get_portable_data_dir
        data_path = get_portable_data_dir('test_data')
    """
    import os
    
    # Get the current script directory and project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = current_dir
    
    # Portable data directories
    data_dirs = {
        'race_2023': os.path.join(project_root, 'data', '2023_races'),
        'race_2024': os.path.join(project_root, 'data', '2024_races'),
        'test_data': os.path.join(project_root, 'Truck_Cal', 'cropped_data'),
        'backup_data': os.path.join(project_root, 'backup_data'),
        'user_data': os.path.expanduser('~/F1_Racing_Data'),
        'temp_data': os.path.join(os.getcwd(), 'temp_racing_data'),
        'env_data': os.getenv('F1_DATA_PATH', os.path.join(project_root, 'Truck_Cal', 'cropped_data'))
    }
    
    if data_type in data_dirs:
        return data_dirs[data_type]
    else:
        # Return test_data as default
        return data_dirs['test_data']


def setup_data_directory(data_type='test_data', create_if_missing=True):
    """
    Setup and configure a data directory for the F1 timing system
    
    Args:
        data_type (str): Type of data directory
        create_if_missing (bool): Create directory if it doesn't exist
    
    Returns:
        tuple: (success, path, message)
    
    Example:
        from config_examples import setup_data_directory
        success, path, msg = setup_data_directory('test_data')
        if success:
            print(f"Data directory ready: {path}")
        else:
            print(f"Error: {msg}")
    """
    import os
    from config import config
    
    try:
        data_path = get_portable_data_dir(data_type)
        
        if os.path.exists(data_path):
            config.Data.BASE_DIR = data_path
            return True, data_path, f"Data directory set successfully"
        
        elif create_if_missing:
            os.makedirs(data_path, exist_ok=True)
            config.Data.BASE_DIR = data_path
            return True, data_path, f"Data directory created and set successfully"
        
        else:
            return False, data_path, f"Directory does not exist: {data_path}"
            
    except Exception as e:
        return False, "", f"Error setting up data directory: {str(e)}"

def example_performance_tuning():
    """Example: Performance tuning for different hardware"""
    print("=== Performance Tuning Examples ===")
    
    from config import config
    import psutil
    
    # Get system specs
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    print(f"System: {cpu_count} CPUs, {memory_gb:.1f}GB RAM")
    
    if cpu_count >= 8 and memory_gb >= 16:
        # High-performance setup
        print("Applying HIGH-PERFORMANCE configuration...")
        config.Performance.UPDATE_INTERVAL = 0.25  # 250ms updates
        config.Performance.BROADCAST_INTERVAL = 1
        config.Performance.MAX_CLIENTS = 100
        config.Performance.DISTANCE_CACHE_SIZE = 2000
        config.Performance.POSITION_CACHE_SIZE = 1000
        
    elif cpu_count >= 4 and memory_gb >= 8:
        # Standard setup
        print("Applying STANDARD configuration...")
        config.Performance.UPDATE_INTERVAL = 0.5   # 500ms updates
        config.Performance.BROADCAST_INTERVAL = 2
        config.Performance.MAX_CLIENTS = 25
        config.Performance.DISTANCE_CACHE_SIZE = 1000
        config.Performance.POSITION_CACHE_SIZE = 500
        
    else:
        # Low-resource setup
        print("Applying LOW-RESOURCE configuration...")
        config.Performance.UPDATE_INTERVAL = 2.0   # 2-second updates
        config.Performance.BROADCAST_INTERVAL = 4
        config.Performance.MAX_CLIENTS = 5
        config.Performance.DISTANCE_CACHE_SIZE = 200
        config.Performance.POSITION_CACHE_SIZE = 100
    
    print("✅ Performance configuration applied")

def example_multi_environment():
    """Example: Multi-environment configuration"""
    print("=== Multi-Environment Configuration ===")
    
    import os
    from config import config
    
    # Check environment variable
    env = os.getenv('F1_ENV', 'development').lower()
    
    print(f"Environment: {env}")
    
    if env == 'production':
        # Production settings
        config.Server.DEBUG = False
        config.Server.PORT = int(os.getenv('F1_PORT', 5002))
        config.Performance.MAX_CLIENTS = int(os.getenv('F1_MAX_CLIENTS', 50))
        config.Logging.LOG_TO_FILE = True
        
    elif env == 'staging':
        # Staging settings
        config.Server.DEBUG = False
        config.Server.PORT = int(os.getenv('F1_PORT', 5004))
        config.Performance.MAX_CLIENTS = int(os.getenv('F1_MAX_CLIENTS', 10))
        config.Logging.ENABLE_DEBUG_LOGGING = True
        
    else:  # development
        # Development settings
        config.Server.DEBUG = True
        config.Server.PORT = int(os.getenv('F1_PORT', 5003))
        config.Performance.MAX_CLIENTS = int(os.getenv('F1_MAX_CLIENTS', 3))
        config.Logging.VERBOSE_CONSOLE_OUTPUT = True
    
    # Data directory from environment
    data_dir = os.getenv('F1_DATA_DIR')
    if data_dir and os.path.exists(data_dir):
        config.Data.BASE_DIR = data_dir
    
    print(f"✅ {env.title()} environment configured")
    config.print_config_summary()

def run_examples():
    """Run all configuration examples"""
    examples = [
        ("Development Setup", example_development_setup),
        ("Production Setup", example_production_setup),
        ("Demo Setup", example_demo_setup),
        ("Custom Data Setup", example_custom_data_setup),
        ("Performance Tuning", example_performance_tuning),
        ("Multi-Environment", example_multi_environment)
    ]
    
    print("F1 Live Timing - Configuration Examples")
    print("=" * 45)
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{i}. {name}")
        print("-" * 30)
        
        try:
            func()
        except Exception as e:
            print(f"❌ Error in {name}: {e}")
        
        input("\nPress Enter to continue to next example...")
        print("\n" + "="*50)

if __name__ == "__main__":
    import os
    
    print("F1 Live Timing System - Configuration Examples")
    print("=" * 50)
    print("This script demonstrates various configuration setups.")
    print("Each example shows how to configure the system for different scenarios.")
    
    # Quick setup demo
    print("\n🚀 Quick Setup Demo:")
    print("-" * 20)
    
    # Show portable data directory usage
    print("1. Getting portable data directories:")
    for data_type in ['test_data', 'race_2023', 'user_data', 'env_data']:
        path = get_portable_data_dir(data_type)
        exists = "✅" if os.path.exists(path) else "❌"
        print(f"   {data_type:12} -> {path} {exists}")
    
    print("\n2. Setting up data directory:")
    success, path, msg = setup_data_directory('test_data', create_if_missing=True)
    print(f"   Result: {msg}")
    print(f"   Path: {path}")
    
    print("\n" + "="*50)
    
    response = input("\nRun all configuration examples? (y/n): ").strip().lower()
    
    if response in ['y', 'yes', '1']:
        run_examples()
    else:
        print("\nAvailable examples:")
        print("1. example_development_setup()")
        print("2. example_production_setup()")
        print("3. example_demo_setup()")
        print("4. example_custom_data_setup()")
        print("5. example_performance_tuning()")
        print("6. example_multi_environment()")
        print("\nPortable helper functions:")
        print("7. get_portable_data_dir(data_type)")
        print("8. setup_data_directory(data_type, create_if_missing=True)")
        print("\nRun individual examples in Python:")
        print("  from config_examples import example_development_setup")
        print("  example_development_setup()")
        print("\nOr use the portable helpers:")
        print("  from config_examples import setup_data_directory")
        print("  success, path, msg = setup_data_directory('test_data')")
