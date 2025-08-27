#!/usr/bin/env python3
"""
F1 Live Timing System Configuration
Central configuration file for easy system setup and customization
"""

import os
from pathlib import Path

class F1Config:
    """Main configuration class for F1 Live Timing System"""
    
    # ========== SERVER CONFIGURATION ==========
    class Server:
        """Flask and WebSocket server settings"""
        SECRET_KEY = 'f1_racing_secret_key'
        HOST = '0.0.0.0'
        PORT = 5002
        DEBUG = False
        USE_RELOADER = False
        CORS_ALLOWED_ORIGINS = "*"
    
    # ========== DATA CONFIGURATION ==========
    class Data:
        """Data source and file handling settings"""
        # Default data directory (can be overridden)
        BASE_DIR = "/Users/socaresabol/POC/test/F1/Truck_Cal/cropped_data"
        
        # Alternative data directories (uncomment to use)
        # BASE_DIR = "/path/to/your/data/directory"
        # BASE_DIR = os.path.join(os.path.dirname(__file__), "data")
        
        # File patterns
        CSV_FILE_PATTERN = "*.csv"
        BACKUP_DATA_DIR = None  # Optional backup directory
        
        # Data processing settings
        MAX_FILE_SIZE_MB = 100  # Maximum file size to process
        VALIDATE_DATA_ON_LOAD = True
    
    # ========== PERFORMANCE CONFIGURATION ==========
    class Performance:
        """System performance and optimization settings"""
        # Client connection limits
        MAX_CLIENTS = 10
        
        # Update intervals (in seconds)
        UPDATE_INTERVAL = 1.0  # How often to process data
        BROADCAST_INTERVAL = 2  # How often to send updates to clients
        
        # Cache settings
        DISTANCE_CACHE_SIZE = 1000  # Maximum cache entries
        POSITION_CACHE_SIZE = 500
        CACHE_CLEANUP_THRESHOLD = 200  # Remove this many when cache is full
        
        # Performance monitoring
        PERFORMANCE_LOG_THRESHOLD = 0.5  # Log functions taking longer than this (seconds)
        ENABLE_PERFORMANCE_MONITORING = True
        
        # Memory optimization
        MAX_RANKINGS_HISTORY = 100  # Keep last N ranking snapshots
    
    # ========== SIMULATION CONFIGURATION ==========
    class Simulation:
        """Race simulation and timing settings"""
        # Speed control
        DEFAULT_SPEED = 1.0  # 1.0 = real-time
        MIN_SPEED = 0.1      # Minimum simulation speed
        MAX_SPEED = 10.0     # Maximum simulation speed
        
        # Speed presets for easy access
        SPEED_PRESETS = {
            'very_slow': 0.25,
            'slow': 0.5,
            'normal': 1.0,
            'fast': 2.0,
            'very_fast': 4.0
        }
        
        # Auto-restart settings
        AUTO_RESTART_ON_FINISH = True
        RESTART_DELAY_SECONDS = 5
    
    # ========== STATUS DETECTION CONFIGURATION ==========
    class StatusDetection:
        """Car status detection parameters"""
        # Speed thresholds (km/h)
        STOPPED_SPEED_THRESHOLD = 5      # Below this = stopped
        PIT_SPEED_THRESHOLD = 60         # Below this = possibly in pits
        RACING_SPEED_THRESHOLD = 80      # Above this = definitely racing
        
        # Time windows (seconds)
        DATA_TIMEOUT_SECONDS = 60        # No data = OUT
        STATUS_WINDOW_SECONDS = 30       # Time window for status analysis
        SPEED_ANALYSIS_WINDOW = 15       # Window for speed trend analysis
        
        # Position variance thresholds
        POSITION_VARIANCE_THRESHOLD = 100  # Position variance for stopped detection
        MIN_MOVEMENT_THRESHOLD = 5         # Minimum movement to be considered moving
        
        # Status validation
        MIN_DATA_POINTS = 3  # Minimum data points needed for status determination
    
    # ========== RANKING CONFIGURATION ==========
    class Ranking:
        """Ranking calculation and display settings"""
        # Update thresholds
        SIGNIFICANT_SPEED_CHANGE = 5  # km/h - triggers ranking update
        SIGNIFICANT_POSITION_CHANGE = 1  # positions
        
        # Interval calculations
        ENABLE_TIME_GAPS = True
        ENABLE_DISTANCE_GAPS = True
        MAX_GAP_DISPLAY_SECONDS = 999  # Show "+999s" for gaps larger than this
        
        # Display options
        SHOW_DECIMAL_GAPS = True  # Show gaps like "1.2s" vs "1s"
        GAP_DECIMAL_PLACES = 1
    
    # ========== FORECASTING CONFIGURATION ==========
    class Forecasting:
        """Overtaking prediction and analysis settings"""
        # Forecast parameters
        FORECAST_TIME_WINDOW = 600  # Maximum forecast time (seconds)
        MIN_FORECAST_ACCURACY = 0.7  # Minimum confidence for showing forecasts
        
        # Speed requirements
        MAX_REASONABLE_SPEED_INCREASE = 30  # km/h - maximum "reasonable" speed increase
        OVERTAKING_BUFFER_TIME = 7  # seconds - additional time for overtaking maneuver
        
        # Analysis windows
        SPEED_TREND_WINDOW = 60     # seconds - window for speed trend analysis
        ACCELERATION_WINDOW = 30    # seconds - window for acceleration calculation
        
        # Scenario generation
        SPEED_INCREASE_SCENARIOS = [5, 10, 15, 20, 25]  # km/h increases to test
        SPEED_DECREASE_SCENARIOS = [0, 5, 10]            # km/h decreases to test
        TIME_SCENARIOS = [30, 60, 120, 300]              # time windows to test
        
        # Forecast quality thresholds
        EXCELLENT_FORECAST_THRESHOLD = 30   # seconds - very likely
        GOOD_FORECAST_THRESHOLD = 120       # seconds - likely
        FAIR_FORECAST_THRESHOLD = 300       # seconds - possible
    
    # ========== UI CONFIGURATION ==========
    class UI:
        """User interface and display settings"""
        # Theme settings
        DEFAULT_THEME = 'dark'  # 'dark' or 'light'
        
        # Update frequencies for different UI elements
        LIVE_TIMING_UPDATE_MS = 1000    # Main timing display
        CHART_UPDATE_MS = 2000          # Charts and graphs
        ANALYSIS_UPDATE_MS = 5000       # Analysis panels
        
        # Display limits
        MAX_CARS_IN_TIMING = 20         # Maximum cars to show in timing display
        MAX_FORECAST_ITEMS = 10         # Maximum forecasts to show
        MAX_COMPARISON_ITEMS = 5        # Maximum cars in comparison view
        
        # Animation settings
        ENABLE_SMOOTH_ANIMATIONS = True
        ANIMATION_DURATION_MS = 500
        ENABLE_POSITION_ANIMATIONS = True
    
    # ========== LOGGING CONFIGURATION ==========
    class Logging:
        """Logging and debugging settings"""
        # Log levels
        ENABLE_DEBUG_LOGGING = False
        ENABLE_PERFORMANCE_LOGGING = True
        ENABLE_ERROR_LOGGING = True
        
        # Log file settings
        LOG_TO_FILE = True
        LOG_FILE_PATH = "f1_timing.log"
        MAX_LOG_FILE_SIZE_MB = 50
        LOG_BACKUP_COUNT = 3
        
        # Console output
        VERBOSE_CONSOLE_OUTPUT = False
        SHOW_CLIENT_CONNECTIONS = True
        SHOW_DATA_LOADING = True
    
    # ========== DISTANCE RESET HANDLING ==========
    class DistanceReset:
        """Distance reset detection and recovery configuration"""
        # Detection thresholds
        DROP_THRESHOLD_PERCENT = 80          # Percentage drop to trigger reset detection
        SPEED_ANOMALY_THRESHOLD = 150        # km/h - unrealistic speed threshold
        MAX_SPEED_INCREASE = 50              # km/h per second - maximum realistic acceleration
        MIN_VALID_DISTANCE = 10              # meters - minimum valid distance
        
        # Recovery configuration
        HISTORY_WINDOW_SECONDS = 300         # seconds - history window for analysis
        INTERPOLATION_MAX_GAP_SECONDS = 60   # seconds - maximum gap for interpolation
        GPS_VALIDATION_RADIUS_METERS = 1000  # meters - GPS validation radius
        MAX_HISTORY_SIZE = 1000              # maximum history entries per car
        
        # Recovery method priorities (higher number = higher priority)
        RECOVERY_PRIORITIES = {
            'speed_integration': 4,
            'gps_recovery': 3,
            'linear_interpolation': 2,
            'fallback': 1
        }
        
        # Validation settings
        ENABLE_GPS_VALIDATION = True
        ENABLE_SPEED_VALIDATION = True
        ENABLE_CONTINUITY_CHECKS = True
        CONFIDENCE_THRESHOLD = 0.6           # minimum confidence for recovery
        
        # Monitoring and logging
        LOG_ALL_RESETS = True
        LOG_RECOVERY_ATTEMPTS = True
        ALERT_ON_MULTIPLE_RESETS = True
        MAX_RESETS_PER_CAR = 10              # alert threshold

    # ========== SAFETY AND LIMITS ==========
    class Safety:
        """Safety limits and error handling"""
        # Resource limits
        MAX_MEMORY_USAGE_MB = 512
        MAX_CPU_USAGE_PERCENT = 80
        
        # Error handling
        MAX_CONSECUTIVE_ERRORS = 5
        ERROR_RECOVERY_DELAY = 2  # seconds
        
        # Data validation
        VALIDATE_TIMESTAMPS = True
        VALIDATE_COORDINATES = True
        VALIDATE_SPEEDS = True
        MAX_SPEED_KMH = 300  # Maximum realistic speed
        
        # Connection limits
        CONNECTION_TIMEOUT_SECONDS = 30
        MAX_WEBSOCKET_MESSAGE_SIZE = 1024 * 1024  # 1MB

    # ========== HELPER METHODS ==========
    @classmethod
    def get_data_directory(cls):
        """Get the configured data directory, creating it if it doesn't exist"""
        data_dir = Path(cls.Data.BASE_DIR)
        if not data_dir.exists():
            print(f"Warning: Data directory {data_dir} does not exist!")
            print(f"Please update config.py with the correct path or create the directory.")
        return str(data_dir)
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        issues = []
        
        # Check data directory
        if not os.path.exists(cls.Data.BASE_DIR):
            issues.append(f"Data directory does not exist: {cls.Data.BASE_DIR}")
        
        # Check speed ranges
        if cls.Simulation.MIN_SPEED >= cls.Simulation.MAX_SPEED:
            issues.append("MIN_SPEED must be less than MAX_SPEED")
        
        # Check thresholds
        if cls.StatusDetection.STOPPED_SPEED_THRESHOLD >= cls.StatusDetection.PIT_SPEED_THRESHOLD:
            issues.append("STOPPED_SPEED_THRESHOLD must be less than PIT_SPEED_THRESHOLD")
        
        # Check performance settings
        if cls.Performance.UPDATE_INTERVAL <= 0:
            issues.append("UPDATE_INTERVAL must be positive")
        
        return issues
    
    @classmethod
    def print_config_summary(cls):
        """Print a summary of current configuration"""
        print("=== F1 Live Timing Configuration Summary ===")
        print(f"Server: {cls.Server.HOST}:{cls.Server.PORT}")
        print(f"Data Directory: {cls.Data.BASE_DIR}")
        print(f"Max Clients: {cls.Performance.MAX_CLIENTS}")
        print(f"Default Speed: {cls.Simulation.DEFAULT_SPEED}x")
        print(f"Update Interval: {cls.Performance.UPDATE_INTERVAL}s")
        print(f"Theme: {cls.UI.DEFAULT_THEME}")
        
        # Validate and show any issues
        issues = cls.validate_config()
        if issues:
            print("\n⚠️  Configuration Issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n✅ Configuration is valid")
        print("=" * 45)

# Create a default configuration instance for easy importing
config = F1Config()

# Example usage and documentation
if __name__ == "__main__":
    print(__doc__)
    config.print_config_summary()
    
    print("\n=== Configuration Examples ===")
    print("# To change data directory:")
    print("config.Data.BASE_DIR = '/path/to/your/data'")
    print()
    print("# To change server port:")
    print("config.Server.PORT = 8080")
    print()
    print("# To change simulation speed:")
    print("config.Simulation.DEFAULT_SPEED = 2.0  # 2x speed")
    print()
    print("# To change performance settings:")
    print("config.Performance.MAX_CLIENTS = 20")
    print("config.Performance.UPDATE_INTERVAL = 0.5  # 500ms updates")
