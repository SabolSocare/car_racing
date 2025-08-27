#!/usr/bin/env python3
"""
F1 Real-Time Racing UI - Flask Web Application
Creates a live timing display similar to Formula 1 broadcasts
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import threading
import time
import json
import psutil
from functools import wraps

# Import configuration
from config import config
from core.timing_engine import F1LiveTiming

app = Flask(__name__)
app.config['SECRET_KEY'] = config.Server.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins=config.Server.CORS_ALLOWED_ORIGINS)

# Connection management
connected_clients: set = set()
max_clients = config.Performance.MAX_CLIENTS

# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        
        # Use config for performance threshold
        if end_time - start_time > config.Performance.PERFORMANCE_LOG_THRESHOLD:
            print(f"Performance warning: {func.__name__} took {end_time - start_time:.2f}s")
        
        return result
    return wrapper

# Initialize the timing system
data_dir = config.get_data_directory()
f1_timing = F1LiveTiming(data_dir, socketio)
f1_timing.load_car_data()
@app.route('/')
def index():
    """Main page redirects to control center"""
    return render_template('control_center.html')

@app.route('/live-timing')
def live_timing():
    """Live timing display page"""
    return render_template('f1_live_timing_websocket.html')

@app.route('/performance')
def performance_mode():
    """Performance mode with reduced animations"""
    return render_template('f1_live_timing_light.html')

@app.route('/overtake-analysis')
def overtake_analysis():
    """Overtaking analysis dashboard"""
    return render_template('overtake_analysis.html')

@app.route('/control')
def control_panel():
    """Simulation control panel"""
    return render_template('control_panel.html')

@app.route('/api/timing')
def get_timing_data():
    """API endpoint for live timing data"""
    return jsonify(f1_timing.get_current_data())

@app.route('/api/start')
def start_race():
    """Start the live timing"""
    f1_timing.start_live_timing()
    return jsonify({'status': 'started'})

@app.route('/api/stop')
def stop_race():
    """Stop the live timing"""
    f1_timing.stop_live_timing()
    return jsonify({'status': 'stopped'})

@app.route('/api/reset')
def reset_race():
    """Reset to race start"""
    f1_timing.stop_live_timing()
    f1_timing.current_time = f1_timing.race_start_time
    f1_timing.current_rankings = []
    return jsonify({'status': 'reset'})

@app.route('/api/speed/<float:speed>')
def set_simulation_speed(speed):
    """Set simulation speed"""
    min_speed = config.Simulation.MIN_SPEED
    max_speed = config.Simulation.MAX_SPEED
    
    if min_speed <= speed <= max_speed:
        f1_timing.simulation_speed = speed
        return jsonify({
            'status': 'success',
            'simulation_speed': speed,
            'description': f'Simulation running at {speed}x speed'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Speed must be between {min_speed} and {max_speed}'
        })

@app.route('/api/speed')
def get_simulation_speed():
    """Get current simulation speed"""
    return jsonify({
        'simulation_speed': f1_timing.simulation_speed,
        'update_interval': f1_timing.update_interval,
        'time_advance_seconds': f1_timing.time_advance_seconds,
        'description': f'Simulation running at {f1_timing.simulation_speed}x speed'
    })

@app.route('/api/time-advance/<int:seconds>')
def set_time_advance(seconds):
    """Set how many race seconds to advance per update (1-10)"""
    if 1 <= seconds <= 10:
        f1_timing.time_advance_seconds = seconds
        return jsonify({
            'status': 'success',
            'time_advance_seconds': seconds,
            'description': f'Advancing {seconds} race seconds per update'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Time advance must be between 1 and 10 seconds'
        })

@app.route('/api/comparison/<int:start_pos>/<int:count>')
def get_comparison(start_pos, count):
    """Get comparison data for specific position range"""
    comparison_data = f1_timing.get_comparison_data(start_pos, count)
    return jsonify({
        'comparison': comparison_data,
        'start_position': start_pos,
        'count': count,
        'current_time': f1_timing.current_time.strftime('%H:%M:%S.%f')[:-3] if f1_timing.current_time else ''
    })

@app.route('/api/trucks')
def get_trucks():
    """Get list of all trucks"""
    return jsonify({'trucks': f1_timing.get_truck_list()})

@app.route('/api/live-update')
def live_update():
    """Enhanced live update endpoint with more data"""
    current_data = f1_timing.get_current_data()
    
    # Add position changes (simplified)
    for i, car in enumerate(current_data['rankings']):
        car['position_change'] = 0  # Could track actual changes
        car['trend'] = 'stable'  # up, down, stable
        
    return jsonify(current_data)

@app.route('/api/forecast/<int:chasing_car_id>/<int:target_car_id>')
def forecast_overtake(chasing_car_id, target_car_id):
    """Forecast when chasing car will overtake target car"""
    try:
        forecast = f1_timing.forecast_overtake_time(chasing_car_id, target_car_id, f1_timing.current_time)
        
        # Add car names for better readability
        chasing_name = f1_timing.car_data.get(chasing_car_id, {}).get('truck_name', f'Car {chasing_car_id}')
        target_name = f1_timing.car_data.get(target_car_id, {}).get('truck_name', f'Car {target_car_id}')
        
        forecast['chasing_car_name'] = chasing_name
        forecast['target_car_name'] = target_name
        forecast['current_time'] = f1_timing.current_time.strftime('%H:%M:%S.%f')[:-3] if f1_timing.current_time else ''
        
        return jsonify(forecast)
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error calculating forecast: {str(e)}',
            'forecast_seconds': -1
        })

@app.route('/api/car-status/<int:car_id>')
def get_car_status(car_id):
    """Get detailed status information for a specific car"""
    try:
        if car_id not in f1_timing.car_data:
            return jsonify({'error': True, 'message': 'Car not found'})
        
        status = f1_timing.determine_car_status(car_id, f1_timing.current_time)
        speed_trend = f1_timing.calculate_speed_trend(car_id, f1_timing.current_time)
        position_data = f1_timing.get_car_position_at_time(car_id, f1_timing.current_time)
        
        return jsonify({
            'car_id': car_id,
            'truck_name': f1_timing.car_data[car_id]['truck_name'],
            'status': status,
            'speed_trend': speed_trend,
            'position': position_data,
            'current_time': f1_timing.current_time.strftime('%H:%M:%S.%f')[:-3] if f1_timing.current_time else ''
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error getting car status: {str(e)}'
        })

@app.route('/api/forecast/bulk')
def forecast_bulk():
    """Get forecasting data for all possible car combinations"""
    try:
        forecasts = []
        current_rankings = f1_timing.current_rankings
        
        # Generate forecasts for cars behind trying to overtake cars ahead
        for i in range(len(current_rankings)):
            for j in range(i):  # Only check cars ahead
                chasing_car = current_rankings[i]
                target_car = current_rankings[j]
                
                forecast = f1_timing.forecast_overtake_time(
                    chasing_car['car_id'], 
                    target_car['car_id'], 
                    f1_timing.current_time
                )
                
                if forecast['can_overtake'] and not forecast['already_ahead']:
                    forecasts.append({
                        'chasing_car_id': chasing_car['car_id'],
                        'chasing_car_name': chasing_car['truck_name'],
                        'chasing_position': chasing_car['position'],
                        'target_car_id': target_car['car_id'],
                        'target_car_name': target_car['truck_name'],
                        'target_position': target_car['position'],
                        'forecast': forecast
                    })
        
        # Sort by forecast time (soonest first)
        forecasts.sort(key=lambda x: x['forecast']['forecast_seconds'])
        
        return jsonify({
            'forecasts': forecasts[:10],  # Return top 10 most likely overtakes
            'total_forecasts': len(forecasts),
            'current_time': f1_timing.current_time.strftime('%H:%M:%S.%f')[:-3] if f1_timing.current_time else ''
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error calculating bulk forecasts: {str(e)}',
            'forecasts': []
        })

@app.route('/api/overtake-analysis/<int:chasing_car_id>/<int:target_car_id>')
def get_overtake_analysis(chasing_car_id, target_car_id):
    """Get detailed overtaking analysis with speed requirements"""
    try:
        if chasing_car_id not in f1_timing.car_data or target_car_id not in f1_timing.car_data:
            return jsonify({'error': True, 'message': 'One or both cars not found'})
        
        analysis = f1_timing.calculate_overtake_requirements(chasing_car_id, target_car_id, f1_timing.current_time)
        analysis['current_time'] = f1_timing.current_time.strftime('%H:%M:%S.%f')[:-3] if f1_timing.current_time else ''
        
        return jsonify(analysis)
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error calculating overtake analysis: {str(e)}'
        })

@app.route('/api/car-comparison/<int:car1_id>/<int:car2_id>')
def get_car_comparison(car1_id, car2_id):
    """Get detailed comparison between two cars"""
    try:
        if car1_id not in f1_timing.car_data or car2_id not in f1_timing.car_data:
            return jsonify({'error': True, 'message': 'One or both cars not found'})
        
        comparison = f1_timing.get_car_comparison_analysis(car1_id, car2_id, f1_timing.current_time)
        comparison['current_time'] = f1_timing.current_time.strftime('%H:%M:%S.%f')[:-3] if f1_timing.current_time else ''
        
        return jsonify(comparison)
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error in car comparison: {str(e)}'
        })

@app.route('/api/overtake-scenarios/<int:car_id>')
def get_overtake_scenarios_for_car(car_id):
    """Get all possible overtaking scenarios for a specific car"""
    try:
        if car_id not in f1_timing.car_data:
            return jsonify({'error': True, 'message': 'Car not found'})
        
        current_rankings = f1_timing.current_rankings
        car_position = None
        
        # Find car's current position
        for car in current_rankings:
            if car['car_id'] == car_id:
                car_position = car['position']
                break
        
        if car_position is None:
            return jsonify({'error': True, 'message': 'Car not in current rankings'})
        
        scenarios = []
        
        # Get scenarios for overtaking cars ahead
        for car in current_rankings:
            if car['position'] < car_position:  # Cars ahead
                analysis = f1_timing.calculate_overtake_requirements(car_id, car['car_id'], f1_timing.current_time)
                scenarios.append({
                    'target_car_id': car['car_id'],
                    'target_car_name': car['truck_name'],
                    'target_position': car['position'],
                    'analysis': analysis
                })
        
        # Sort by target position (closest cars first)
        scenarios.sort(key=lambda x: x['target_position'], reverse=True)
        
        return jsonify({
            'car_id': car_id,
            'car_name': f1_timing.car_data[car_id]['truck_name'],
            'current_position': car_position,
            'overtake_scenarios': scenarios,
            'total_scenarios': len(scenarios),
            'current_time': f1_timing.current_time.strftime('%H:%M:%S.%f')[:-3] if f1_timing.current_time else ''
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error calculating overtake scenarios: {str(e)}'
        })

@app.route('/api/speed-requirements/<int:chasing_car_id>/<int:target_car_id>')
def get_speed_requirements(chasing_car_id, target_car_id):
    """Get specific speed requirements for overtaking in different time windows"""
    try:
        if chasing_car_id not in f1_timing.car_data or target_car_id not in f1_timing.car_data:
            return jsonify({'error': True, 'message': 'One or both cars not found'})
        
        # Get basic data
        chasing_distance = f1_timing.calculate_distance_traveled(chasing_car_id, f1_timing.current_time)
        target_distance = f1_timing.calculate_distance_traveled(target_car_id, f1_timing.current_time)
        chasing_trend = f1_timing.calculate_speed_trend(chasing_car_id, f1_timing.current_time)
        target_trend = f1_timing.calculate_speed_trend(target_car_id, f1_timing.current_time)
        
        distance_gap = target_distance - chasing_distance
        current_chasing_speed = chasing_trend['current_speed']
        current_target_speed = target_trend['current_speed']
        
        # Calculate requirements for different time windows
        time_windows = [15, 30, 60, 120, 300, 600]  # seconds
        requirements = []
        
        for time_window in time_windows:
            # Speed needed to close gap in this time
            target_speed_ms = current_target_speed * 1000 / 3600
            required_speed_ms = (distance_gap / time_window) + target_speed_ms
            required_speed_kmh = required_speed_ms * 3600 / 1000
            speed_increase = required_speed_kmh - current_chasing_speed
            
            requirements.append({
                'time_window_seconds': int(time_window),
                'time_window_minutes': float(time_window / 60),
                'required_speed_kmh': float(required_speed_kmh),
                'current_speed_kmh': float(current_chasing_speed),
                'speed_increase_needed_kmh': float(speed_increase),
                'speed_increase_percent': float((speed_increase / max(current_chasing_speed, 1)) * 100),
                'feasible': bool(speed_increase <= 25),  # Reasonable limit
                'difficulty': 'easy' if speed_increase <= 5 else 'moderate' if speed_increase <= 15 else 'hard'
            })
        
        return jsonify({
            'chasing_car_name': f1_timing.car_data[chasing_car_id]['truck_name'],
            'target_car_name': f1_timing.car_data[target_car_id]['truck_name'],
            'current_gap_meters': float(distance_gap),
            'current_speeds': {
                'chasing': float(current_chasing_speed),
                'target': float(current_target_speed)
            },
            'speed_requirements': requirements,
            'current_time': f1_timing.current_time.strftime('%H:%M:%S.%f')[:-3] if f1_timing.current_time else ''
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error calculating speed requirements: {str(e)}'
        })

@app.route('/api/speed-control', methods=['GET', 'POST'])
def speed_control():
    """Get or set simulation speed"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            speed = float(data.get('speed', 1.0))
            
            # Validate speed range
            if speed < 0.1 or speed > 5.0:
                return jsonify({'error': True, 'message': 'Speed must be between 0.1 and 5.0'})
            
            f1_timing.simulation_speed = speed
            
            return jsonify({
                'status': 'success',
                'current_speed': speed,
                'message': f'Simulation speed set to {speed}x'
            })
        except Exception as e:
            return jsonify({
                'error': True,
                'message': f'Error setting speed: {str(e)}'
            })
    else:
        # GET request - return current speed
        return jsonify({
            'current_speed': f1_timing.simulation_speed,
            'min_speed': 0.1,
            'max_speed': 5.0,
            'default_speed': 1.0
        })

# WebSocket event handlers

@app.route('/api/distance-reset-status')
def get_distance_reset_status():
    """Get distance reset monitoring status"""
    try:
        status = f1_timing.get_distance_reset_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error getting distance reset status: {str(e)}'
        })

@app.route('/api/car-distance-status/<int:car_id>')
def get_car_distance_status_api(car_id):
    """Get distance status for specific car"""
    try:
        if car_id not in f1_timing.car_data:
            return jsonify({'error': True, 'message': 'Car not found'})
        
        status = f1_timing.get_car_distance_status(car_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error getting car distance status: {str(e)}'
        })

@app.route('/api/available-targets/<int:chasing_car_id>')
def get_available_targets(chasing_car_id):
    """Get available target cars for a chasing car (cars ahead in the race)"""
    try:
        if chasing_car_id not in f1_timing.car_data:
            return jsonify({'error': True, 'message': 'Chasing car not found'})
        
        # Make sure we have current rankings
        if not f1_timing.current_rankings:
            rankings = f1_timing.calculate_live_rankings()
        else:
            rankings = f1_timing.current_rankings
        
        # Find the chasing car's position
        chasing_car_position = None
        chasing_car_data = None
        
        for car in rankings:
            if car['car_id'] == chasing_car_id:
                chasing_car_position = car['position']
                chasing_car_data = car
                break
        
        if chasing_car_position is None:
            return jsonify({
                'error': True, 
                'message': 'Chasing car not found in current rankings'
            })
        
        # Get all cars ahead of the chasing car
        available_targets = []
        
        for car in rankings:
            if car['position'] < chasing_car_position:  # Cars ahead have lower position numbers
                # Calculate gap between chasing car and this target
                gap_distance = car['distance_traveled'] - chasing_car_data['distance_traveled']
                
                available_targets.append({
                    'car_id': car['car_id'],
                    'truck_name': car['truck_name'],
                    'position': car['position'],
                    'current_speed': car['current_speed'],
                    'distance_traveled': car['distance_traveled'],
                    'gap_to_chasing_car': gap_distance,
                    'status': car.get('status', 'RUNNING')
                })
        
        # Sort by position (closest targets first)
        available_targets.sort(key=lambda x: x['position'], reverse=True)
        
        return jsonify({
            'chasing_car_id': chasing_car_id,
            'chasing_car_name': chasing_car_data['truck_name'],
            'chasing_car_position': chasing_car_position,
            'total_targets': len(available_targets),
            'available_targets': available_targets,
            'message': f"{len(available_targets)} cars available for overtaking",
            'current_time': f1_timing.current_time.strftime('%H:%M:%S.%f')[:-3] if f1_timing.current_time else ''
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Error getting available targets: {str(e)}'
        })

@app.route('/api/simulation-speed', methods=['GET', 'POST'])
def simulation_speed():
    """Get or set simulation speed"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            new_speed = float(data.get('speed', config.Simulation.DEFAULT_SPEED))
            
            # Validate speed range using config
            min_speed = config.Simulation.MIN_SPEED
            max_speed = config.Simulation.MAX_SPEED
            
            if min_speed <= new_speed <= max_speed:
                f1_timing.simulation_speed = new_speed
                return jsonify({
                    'status': 'success',
                    'simulation_speed': f1_timing.simulation_speed,
                    'message': f'Simulation speed set to {new_speed}x',
                    'update_interval': f1_timing.update_interval,
                    'race_time_per_real_time': f1_timing.simulation_speed
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Speed must be between {min_speed}x and {max_speed}x'
                })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error setting speed: {str(e)}'
            })
    
    # GET request - return current settings
    return jsonify({
        'simulation_speed': f1_timing.simulation_speed,
        'update_interval': f1_timing.update_interval,
        'is_running': f1_timing.is_running,
        'race_time_per_real_time': f1_timing.simulation_speed,
        'min_speed': config.Simulation.MIN_SPEED,
        'max_speed': config.Simulation.MAX_SPEED,
        'speed_presets': config.Simulation.SPEED_PRESETS,
        'description': f'At {f1_timing.simulation_speed}x speed: {f1_timing.simulation_speed} seconds of race time per 1 second of real time'
    })

@app.route('/control')
def control_center():
    """Main control center page"""
    return render_template('control_center.html')

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection with limits"""
    max_clients_limit = config.Performance.MAX_CLIENTS
    
    if len(connected_clients) >= max_clients_limit:
        print(f'Connection rejected: Maximum {max_clients_limit} clients reached')
        return False
    
    connected_clients.add(request.sid)
    if config.Logging.SHOW_CLIENT_CONNECTIONS:
        print(f'Client connected. Total clients: {len(connected_clients)}')
    
    # Send current data to newly connected client
    current_data = f1_timing.get_current_data()
    emit('timing_update', current_data)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    connected_clients.discard(request.sid)
    if config.Logging.SHOW_CLIENT_CONNECTIONS:
        print(f'Client disconnected. Total clients: {len(connected_clients)}')

@socketio.on('request_data')
def handle_data_request():
    """Handle explicit data request from client"""
    current_data = f1_timing.get_current_data()
    emit('timing_update', current_data)

@socketio.on('start_race')
def handle_start_race():
    """Handle race start via WebSocket"""
    f1_timing.start_live_timing()
    emit('race_status', {'status': 'started'}, broadcast=True)

@socketio.on('stop_race')
def handle_stop_race():
    """Handle race stop via WebSocket"""
    f1_timing.stop_live_timing()
    emit('race_status', {'status': 'stopped'}, broadcast=True)

@socketio.on('reset_race')
def handle_reset_race():
    """Handle race reset via WebSocket"""
    f1_timing.stop_live_timing()
    f1_timing.current_time = f1_timing.race_start_time
    f1_timing.current_rankings = []
    current_data = f1_timing.get_current_data()
    emit('timing_update', current_data, broadcast=True)
    emit('race_status', {'status': 'reset'}, broadcast=True)

if __name__ == '__main__':
    # Print configuration summary
    config.print_config_summary()
    
    print("Starting F1 Live Timing Web Server with WebSocket support...")
    print(f"Open your browser and go to: http://localhost:{config.Server.PORT}")
    
    # Optimized configuration for better performance
    socketio.run(
        app, 
        debug=config.Server.DEBUG,
        host=config.Server.HOST, 
        port=config.Server.PORT,
        use_reloader=config.Server.USE_RELOADER
    )
