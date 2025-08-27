#!/usr/bin/env python3
"""
F1 Live Timing - Configuration Examples and Helper
This script shows how to easily modify configuration settings
"""

from config import config
import os

def setup_for_development():
    """Configure settings for development environment"""
    print("Setting up development configuration...")
    
    # Development server settings
    config.Server.DEBUG = True
    config.Server.PORT = 5003
    config.Server.USE_RELOADER = True
    
    # More verbose logging for development
    config.Logging.ENABLE_DEBUG_LOGGING = True
    config.Logging.VERBOSE_CONSOLE_OUTPUT = True
    
    # Faster updates for development
    config.Performance.UPDATE_INTERVAL = 0.5
    config.Performance.BROADCAST_INTERVAL = 1
    
    # Lower client limit for testing
    config.Performance.MAX_CLIENTS = 5
    
    print("✅ Development configuration applied")

def setup_for_production():
    """Configure settings for production environment"""
    print("Setting up production configuration...")
    
    # Production server settings
    config.Server.DEBUG = False
    config.Server.PORT = 5002
    config.Server.USE_RELOADER = False
    
    # Optimized logging for production
    config.Logging.ENABLE_DEBUG_LOGGING = False
    config.Logging.VERBOSE_CONSOLE_OUTPUT = False
    config.Logging.LOG_TO_FILE = True
    
    # Optimized performance for production
    config.Performance.UPDATE_INTERVAL = 1.0
    config.Performance.BROADCAST_INTERVAL = 2
    config.Performance.MAX_CLIENTS = 20
    
    print("✅ Production configuration applied")

def setup_for_demo():
    """Configure settings for demo/presentation"""
    print("Setting up demo configuration...")
    
    # Demo settings - faster simulation
    config.Simulation.DEFAULT_SPEED = 2.0  # 2x speed for demos
    
    # Responsive updates for demo
    config.Performance.UPDATE_INTERVAL = 0.5
    config.Performance.BROADCAST_INTERVAL = 1
    
    # More aggressive status detection for demo
    config.StatusDetection.STATUS_WINDOW_SECONDS = 15
    config.StatusDetection.DATA_TIMEOUT_SECONDS = 30
    
    print("✅ Demo configuration applied")

def set_data_directory(new_path):
    """Change the data directory"""
    if os.path.exists(new_path):
        config.Data.BASE_DIR = new_path
        print(f"✅ Data directory set to: {new_path}")
    else:
        print(f"❌ Directory does not exist: {new_path}")
        print("Please create the directory or provide a valid path")

def show_current_config():
    """Display current configuration"""
    print("\n" + "="*50)
    print("CURRENT CONFIGURATION")
    print("="*50)
    
    print(f"Server: {config.Server.HOST}:{config.Server.PORT}")
    print(f"Debug Mode: {config.Server.DEBUG}")
    print(f"Data Directory: {config.Data.BASE_DIR}")
    print(f"Max Clients: {config.Performance.MAX_CLIENTS}")
    print(f"Update Interval: {config.Performance.UPDATE_INTERVAL}s")
    print(f"Default Speed: {config.Simulation.DEFAULT_SPEED}x")
    print(f"Speed Range: {config.Simulation.MIN_SPEED}x - {config.Simulation.MAX_SPEED}x")
    print(f"Logging to File: {config.Logging.LOG_TO_FILE}")
    print(f"Debug Logging: {config.Logging.ENABLE_DEBUG_LOGGING}")
    
    print("\nSpeed Presets:")
    for name, speed in config.Simulation.SPEED_PRESETS.items():
        print(f"  {name}: {speed}x")
    
    print("="*50)

def interactive_config():
    """Interactive configuration setup"""
    print("\n🏎️  F1 Live Timing Configuration Helper")
    print("=" * 45)
    
    while True:
        print("\nSelect an option:")
        print("1. Setup for Development")
        print("2. Setup for Production") 
        print("3. Setup for Demo/Presentation")
        print("4. Change Data Directory")
        print("5. Show Current Configuration")
        print("6. Validate Configuration")
        print("7. Reset to Defaults")
        print("0. Exit")
        
        try:
            choice = input("\nEnter your choice (0-7): ").strip()
            
            if choice == '0':
                print("Goodbye! 👋")
                break
            elif choice == '1':
                setup_for_development()
            elif choice == '2':
                setup_for_production()
            elif choice == '3':
                setup_for_demo()
            elif choice == '4':
                new_path = input("Enter new data directory path: ").strip()
                set_data_directory(new_path)
            elif choice == '5':
                show_current_config()
            elif choice == '6':
                issues = config.validate_config()
                if issues:
                    print("❌ Configuration Issues Found:")
                    for issue in issues:
                        print(f"  - {issue}")
                else:
                    print("✅ Configuration is valid!")
            elif choice == '7':
                # Reset to defaults (reimport config)
                import importlib
                import config as config_module
                importlib.reload(config_module)
                globals()['config'] = config_module.config
                print("✅ Configuration reset to defaults")
            else:
                print("❌ Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def quick_setup_examples():
    """Show quick setup examples"""
    print("\n📝 QUICK SETUP EXAMPLES")
    print("=" * 30)
    
    print("\n1. Change port to 8080:")
    print("   config.Server.PORT = 8080")
    
    print("\n2. Set data directory:")
    print("   config.Data.BASE_DIR = '/path/to/your/data'")
    
    print("\n3. Change simulation speed:")
    print("   config.Simulation.DEFAULT_SPEED = 2.0  # 2x speed")
    
    print("\n4. Increase client limit:")
    print("   config.Performance.MAX_CLIENTS = 50")
    
    print("\n5. Enable debug mode:")
    print("   config.Server.DEBUG = True")
    print("   config.Logging.ENABLE_DEBUG_LOGGING = True")
    
    print("\n6. Optimize for performance:")
    print("   config.Performance.UPDATE_INTERVAL = 2.0")
    print("   config.Performance.BROADCAST_INTERVAL = 3")
    
    print("\n7. Use speed presets:")
    print("   config.Simulation.DEFAULT_SPEED = config.Simulation.SPEED_PRESETS['fast']")

if __name__ == "__main__":
    print("F1 Live Timing Configuration Helper")
    print("=" * 40)
    
    # Show quick examples first
    quick_setup_examples()
    
    # Ask if user wants interactive config
    response = input("\nWould you like to use interactive configuration? (y/n): ").strip().lower()
    
    if response in ['y', 'yes', '1']:
        interactive_config()
    else:
        print("\nConfiguration helper finished.")
        print("You can modify settings directly in config.py or import this module.")
        print("\nExample:")
        print("  from config_helper import setup_for_development")
        print("  setup_for_development()")
