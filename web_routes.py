#!/usr/bin/env python3
"""
Web Routes Module
Contains all Flask routes and API endpoints
"""

from flask import render_template, jsonify, request
from config import config


def register_routes(app, f1_timing):
    """Register all routes with the Flask app"""
    
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

    @app.route('/control')
    def control_center():
        """Main control center page"""
        return render_template('control_center.html')

    # ========== API ENDPOINTS ==========

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
            'description': f'Simulation running at {f1_timing.simulation_speed}x speed'
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

    @app.route('/api/available-targets/<int:chasing_car_id>')
    def get_available_targets(chasing_car_id):
        """Get list of cars that are ahead of the specified chasing car"""
        try:
            if chasing_car_id not in f1_timing.car_data:
                return jsonify({'error': True, 'message': 'Chasing car not found'})
            
            # Get current rankings
            current_rankings = f1_timing.current_rankings
            if not current_rankings:
                # If no current rankings, calculate them
                current_rankings = f1_timing.calculate_live_rankings()
            
            # Find chasing car position
            chasing_car_position = None
            for car in current_rankings:
                if car['car_id'] == chasing_car_id:
                    chasing_car_position = car['position']
                    break
            
            if chasing_car_position is None:
                return jsonify({'error': True, 'message': 'Chasing car not found in current rankings'})
            
            # Get cars that are ahead (lower position number)
            available_targets = []
            for car in current_rankings:
                if car['position'] < chasing_car_position:  # Car is ahead
                    available_targets.append({
                        'car_id': car['car_id'],
                        'truck_name': car['truck_name'],
                        'position': car['position'],
                        'current_speed': car['current_speed'],
                        'distance_traveled': car['distance_traveled'],
                        'gap_to_chasing_car': car['distance_traveled'] - next(c['distance_traveled'] for c in current_rankings if c['car_id'] == chasing_car_id)
                    })
            
            return jsonify({
                'chasing_car_id': chasing_car_id,
                'chasing_car_name': f1_timing.car_data[chasing_car_id]['truck_name'],
                'chasing_car_position': chasing_car_position,
                'available_targets': available_targets,
                'total_targets': len(available_targets),
                'current_time': f1_timing.current_time.strftime('%H:%M:%S.%f')[:-3] if f1_timing.current_time else ''
            })
            
        except Exception as e:
            return jsonify({
                'error': True,
                'message': f'Error getting available targets: {str(e)}'
            })

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
