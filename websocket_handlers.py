#!/usr/bin/env python3
"""
WebSocket Handlers Module
Contains all SocketIO event handlers and connection management
"""

from flask import request
from flask_socketio import emit
from config import config


# Connection management
connected_clients = set()
max_clients = config.Performance.MAX_CLIENTS


def register_socketio_handlers(socketio, f1_timing):
    """Register all SocketIO event handlers"""
    
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

    @socketio.on('request_forecast')
    def handle_forecast_request(data):
        """Handle forecast request via WebSocket"""
        try:
            chasing_car_id = int(data.get('chasing_car_id'))
            target_car_id = int(data.get('target_car_id'))
            
            forecast = f1_timing.forecast_overtake_time(
                chasing_car_id, 
                target_car_id, 
                f1_timing.current_time
            )
            
            emit('forecast_result', {
                'chasing_car_id': chasing_car_id,
                'target_car_id': target_car_id,
                'forecast': forecast
            })
        except Exception as e:
            emit('forecast_error', {
                'message': f'Error calculating forecast: {str(e)}'
            })

    @socketio.on('request_car_status')
    def handle_car_status_request(data):
        """Handle car status request via WebSocket"""
        try:
            car_id = int(data.get('car_id'))
            
            if car_id not in f1_timing.car_data:
                emit('car_status_error', {'message': 'Car not found'})
                return
            
            status = f1_timing.determine_car_status(car_id, f1_timing.current_time)
            speed_trend = f1_timing.calculate_speed_trend(car_id, f1_timing.current_time)
            position_data = f1_timing.get_car_position_at_time(car_id, f1_timing.current_time)
            
            emit('car_status_result', {
                'car_id': car_id,
                'truck_name': f1_timing.car_data[car_id]['truck_name'],
                'status': status,
                'speed_trend': speed_trend,
                'position': position_data,
                'current_time': f1_timing.current_time.strftime('%H:%M:%S.%f')[:-3] if f1_timing.current_time else ''
            })
        except Exception as e:
            emit('car_status_error', {
                'message': f'Error getting car status: {str(e)}'
            })

    @socketio.on('set_simulation_speed')
    def handle_speed_change(data):
        """Handle simulation speed change via WebSocket"""
        try:
            speed = float(data.get('speed', 1.0))
            
            min_speed = config.Simulation.MIN_SPEED
            max_speed = config.Simulation.MAX_SPEED
            
            if min_speed <= speed <= max_speed:
                f1_timing.simulation_speed = speed
                emit('speed_change_result', {
                    'status': 'success',
                    'simulation_speed': speed,
                    'message': f'Simulation speed set to {speed}x'
                }, broadcast=True)
            else:
                emit('speed_change_error', {
                    'message': f'Speed must be between {min_speed} and {max_speed}'
                })
        except Exception as e:
            emit('speed_change_error', {
                'message': f'Error setting speed: {str(e)}'
            })

    @socketio.on('request_bulk_forecast')
    def handle_bulk_forecast_request():
        """Handle bulk forecast request via WebSocket"""
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
            
            emit('bulk_forecast_result', {
                'forecasts': forecasts[:10],  # Return top 10 most likely overtakes
                'total_forecasts': len(forecasts),
                'current_time': f1_timing.current_time.strftime('%H:%M:%S.%f')[:-3] if f1_timing.current_time else ''
            })
        except Exception as e:
            emit('bulk_forecast_error', {
                'message': f'Error calculating bulk forecasts: {str(e)}'
            })

    return {
        'connected_clients': connected_clients,
        'max_clients': max_clients
    }
