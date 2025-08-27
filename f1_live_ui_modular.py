#!/usr/bin/env python3
"""
F1 Real-Time Racing UI - Modular Flask Web Application
Creates a live timing display similar to Formula 1 broadcasts

This is the main entry point for the F1 Live Timing System.
The application is now modularized for better maintainability:

- core/: Core timing engine and business logic
- web_routes.py: Flask route handlers and API endpoints  
- websocket_handlers.py: SocketIO event handlers
- config.py: Centralized configuration
"""

from flask import Flask
from flask_socketio import SocketIO

# Import configuration
from config import config

# Import core modules
from core import F1LiveTiming

# Import modular components
from web_routes import register_routes
from websocket_handlers import register_socketio_handlers


def create_app():
    """Application factory pattern for creating Flask app"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.Server.SECRET_KEY
    
    return app


def create_socketio(app):
    """Create SocketIO instance with configuration"""
    socketio = SocketIO(
        app, 
        cors_allowed_origins=config.Server.CORS_ALLOWED_ORIGINS
    )
    return socketio


def initialize_timing_system(socketio):
    """Initialize the F1 timing system"""
    data_dir = config.get_data_directory()
    f1_timing = F1LiveTiming(data_dir, socketio)
    f1_timing.load_car_data()
    return f1_timing


def main():
    """Main application entry point"""
    # Print configuration summary
    config.print_config_summary()
    
    # Create Flask app and SocketIO
    app = create_app()
    socketio = create_socketio(app)
    
    # Initialize timing system
    f1_timing = initialize_timing_system(socketio)
    
    # Register routes and handlers
    register_routes(app, f1_timing)
    register_socketio_handlers(socketio, f1_timing)
    
    print("Starting F1 Live Timing Web Server with WebSocket support...")
    print(f"Open your browser and go to: http://localhost:{config.Server.PORT}")
    
    # Start the application
    socketio.run(
        app, 
        debug=config.Server.DEBUG,
        host=config.Server.HOST, 
        port=config.Server.PORT,
        use_reloader=config.Server.USE_RELOADER
    )


if __name__ == '__main__':
    main()
