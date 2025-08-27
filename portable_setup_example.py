#!/usr/bin/env python3
"""
Portable F1 Setup Example
Demonstrates how to use the portable configuration functions
"""

def quick_setup_example():
    """Quick setup example for any computer"""
    print("🏁 F1 Live Timing - Quick Portable Setup")
    print("="*45)
    
    # Import the portable helper functions
    from config_examples import get_portable_data_dir, setup_data_directory
    
    # 1. Check available data directories
    print("📁 Available data directories:")
    data_types = ['test_data', 'race_2023', 'race_2024', 'user_data', 'backup_data']
    
    for data_type in data_types:
        path = get_portable_data_dir(data_type)
        import os
        exists = "✅ EXISTS" if os.path.exists(path) else "❌ Missing"
        print(f"   {data_type:12} -> {path}")
        print(f"   {' '*15}   {exists}")
    
    print("\n🔧 Setting up test data directory...")
    
    # 2. Setup the data directory (will create if missing)
    success, path, message = setup_data_directory('test_data', create_if_missing=True)
    
    if success:
        print(f"✅ SUCCESS: {message}")
        print(f"📂 Data path: {path}")
    else:
        print(f"❌ ERROR: {message}")
        return False
    
    print("\n🚀 Starting F1 Live Timing System...")
    
    # 3. Import and configure the system
    try:
        from config import config
        
        # Apply portable settings
        config.Data.BASE_DIR = path
        config.Server.PORT = 5002
        config.Simulation.DEFAULT_SPEED = 1.0
        
        print("✅ Configuration applied successfully!")
        
        # Display current config
        print(f"\n📊 Current Configuration:")
        print(f"   Data Directory: {config.Data.BASE_DIR}")
        print(f"   Server Port: {config.Server.PORT}")
        print(f"   Default Speed: {config.Simulation.DEFAULT_SPEED}x")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def advanced_portable_setup():
    """Advanced portable setup with environment detection"""
    print("\n🔬 Advanced Portable Setup")
    print("-"*30)
    
    import os
    from config_examples import setup_data_directory
    
    # Check environment variables
    custom_data_path = os.getenv('F1_DATA_PATH')
    custom_port = os.getenv('F1_PORT', '5002')
    
    print(f"Environment variables:")
    print(f"   F1_DATA_PATH: {custom_data_path or 'Not set'}")
    print(f"   F1_PORT: {custom_port}")
    
    # Choose data source based on availability
    data_priority = ['env_data', 'test_data', 'user_data', 'temp_data']
    
    for data_type in data_priority:
        success, path, message = setup_data_directory(data_type, create_if_missing=True)
        if success:
            print(f"\n✅ Using data type: {data_type}")
            print(f"📂 Path: {path}")
            break
    else:
        print("❌ Could not setup any data directory!")
        return False
    
    # Apply configuration
    from config import config
    config.Data.BASE_DIR = path
    config.Server.PORT = int(custom_port)
    
    print(f"\n🎯 Final Configuration:")
    print(f"   Data: {config.Data.BASE_DIR}")
    print(f"   Port: {config.Server.PORT}")
    
    return True

def create_user_data_setup():
    """Create a user-specific data setup"""
    print("\n👤 User Data Setup")
    print("-"*20)
    
    import os
    from config_examples import setup_data_directory
    
    # Setup user-specific directory
    success, path, message = setup_data_directory('user_data', create_if_missing=True)
    
    if success:
        print(f"✅ User data directory ready: {path}")
        
        # Create subdirectories
        subdirs = ['races', 'backups', 'exports', 'configs']
        for subdir in subdirs:
            subpath = os.path.join(path, subdir)
            os.makedirs(subpath, exist_ok=True)
            print(f"📁 Created: {subpath}")
        
        # Create a sample config file
        config_file = os.path.join(path, 'configs', 'user_settings.txt')
        with open(config_file, 'w') as f:
            f.write("# F1 Live Timing User Settings\n")
            f.write(f"data_path={path}\n")
            f.write("default_speed=1.0\n")
            f.write("theme=dark\n")
        
        print(f"📝 Created config: {config_file}")
        return True
    else:
        print(f"❌ {message}")
        return False

if __name__ == "__main__":
    print("Choose setup type:")
    print("1. Quick Setup (recommended)")
    print("2. Advanced Setup (with environment detection)")
    print("3. User Data Setup (creates ~/F1_Racing_Data)")
    print("4. Run all setups")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        quick_setup_example()
    elif choice == '2':
        advanced_portable_setup()
    elif choice == '3':
        create_user_data_setup()
    elif choice == '4':
        print("Running all setup examples...\n")
        quick_setup_example()
        advanced_portable_setup()
        create_user_data_setup()
    else:
        print("Invalid choice. Running quick setup...")
        quick_setup_example()
    
    print("\n" + "="*50)
    print("🏁 Setup complete! You can now run the F1 timing system:")
    print("   python f1_live_ui.py")
    print("   Open browser: http://localhost:5002")
