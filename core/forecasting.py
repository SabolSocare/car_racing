#!/usr/bin/env python3
"""
Forecasting Module
Handles overtaking predictions and speed requirement calculations
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from config import config


class OvertakingForecaster:
    """Handles overtaking forecasting and analysis"""
    
    def __init__(self):
        try:
            self.forecasting_config = config.Forecasting
        except AttributeError:
            # Create default config if not available
            self.forecasting_config = type('Config', (), {
                'SPEED_TREND_WINDOW': 30,
                'OVERTAKING_BUFFER_TIME': 5,
                'SPEED_INCREASE_SCENARIOS': [5, 10, 15, 20, 25],
                'SPEED_DECREASE_SCENARIOS': [0, 5, 10, 15]
            })()
    
    def calculate_speed_trend(self, car_data, current_time, window_seconds=None):
        """Calculate speed trend and acceleration for forecasting"""
        if window_seconds is None:
            try:
                window_seconds = self.forecasting_config.SPEED_TREND_WINDOW
            except AttributeError:
                window_seconds = 30  # Default 30 seconds
            
        df = car_data['data']
        
        # Get recent data for trend analysis
        start_window = current_time - timedelta(seconds=window_seconds)
        recent_data = df[(df['timeStamp'] >= start_window) & (df['timeStamp'] <= current_time)]
        
        if len(recent_data) < 3:
            # Not enough data for trend analysis, return basic info
            if len(recent_data) > 0:
                last_speed = recent_data['speed'].iloc[-1] if 'speed' in recent_data.columns else 0
                return {
                    'avg_speed': float(last_speed),
                    'acceleration': 0.0,
                    'trend': 'stable',
                    'current_speed': float(last_speed)
                }
            else:
                return {
                    'avg_speed': 0.0,
                    'acceleration': 0.0,
                    'trend': 'stable',
                    'current_speed': 0.0
                }
        
        # Calculate average speed and acceleration
        speeds = recent_data['speed'].values
        times = recent_data['timeStamp'].values
        
        # Convert timestamps to seconds for calculation
        time_seconds = [(pd.Timestamp(t) - pd.Timestamp(times[0])).total_seconds() for t in times]
        
        # Linear regression for speed trend
        if len(speeds) > 1:
            try:
                coeffs = np.polyfit(time_seconds, speeds, 1)
                acceleration = coeffs[0]  # km/h per second
                avg_speed = np.mean(speeds)
                
                # Determine trend
                if acceleration > 1:
                    trend = 'accelerating'
                elif acceleration < -1:
                    trend = 'decelerating'
                else:
                    trend = 'stable'
                
                return {
                    'avg_speed': avg_speed,
                    'acceleration': acceleration,
                    'trend': trend,
                    'current_speed': speeds[-1]
                }
            except:
                return {'avg_speed': np.mean(speeds), 'acceleration': 0, 'trend': 'stable', 'current_speed': speeds[-1]}
        
        return {'avg_speed': speeds[0], 'acceleration': 0, 'trend': 'stable', 'current_speed': speeds[0]}
    
    def forecast_overtake_time(self, chasing_car_data, target_car_data, chasing_distance, target_distance, current_time):
        """Forecast how long it will take for chasing car to overtake target car"""
        try:
            # If chasing car is already ahead, return meaningful data
            if chasing_distance >= target_distance:
                return {
                    'forecast_seconds': 0,
                    'forecast_minutes': 0,
                    'can_overtake': True,
                    'already_ahead': True,
                    'message': f"{chasing_car_data.get('truck_name', 'Chasing car')} is already ahead of {target_car_data.get('truck_name', 'Target car')}",
                    'distance_advantage': chasing_distance - target_distance,
                    'time_advantage': self._calculate_time_advantage(chasing_car_data, target_car_data, current_time),
                    'status': 'ahead'
                }
            
            # Get speed trends for both cars
            chasing_trend = self.calculate_speed_trend(chasing_car_data, current_time)
            target_trend = self.calculate_speed_trend(target_car_data, current_time)
            
            # Calculate gap in distance
            distance_gap = target_distance - chasing_distance
            
            # Get current speeds (convert km/h to m/s)
            chasing_speed_ms = max(chasing_trend['current_speed'] * 1000 / 3600, 0.1)
            target_speed_ms = max(target_trend['current_speed'] * 1000 / 3600, 0.1)
            
            # Calculate relative speed (how much faster chasing car is)
            relative_speed_ms = chasing_speed_ms - target_speed_ms
            
            # If chasing car is not faster, calculate with acceleration
            if relative_speed_ms <= 0:
                # Factor in acceleration trends
                chasing_accel = chasing_trend['acceleration'] * 1000 / 3600  # convert to m/s²
                target_accel = target_trend['acceleration'] * 1000 / 3600
                
                relative_acceleration = chasing_accel - target_accel
                
                # If both cars have similar speeds and accelerations, use projected speeds
                if abs(relative_speed_ms) < 1 and abs(relative_acceleration) > 0.1:
                    # Project speeds 60 seconds into future
                    future_chasing_speed = chasing_speed_ms + (chasing_accel * 60)
                    future_target_speed = target_speed_ms + (target_accel * 60)
                    relative_speed_ms = future_chasing_speed - future_target_speed
                
                # If still not faster, check if overtake is possible
                if relative_speed_ms <= 0:
                    return {
                        'forecast_seconds': -1,
                        'forecast_minutes': -1,
                        'can_overtake': False,
                        'already_ahead': False,
                        'message': f"{chasing_car_data['truck_name']} is not gaining on {target_car_data['truck_name']}",
                        'relative_speed_kmh': relative_speed_ms * 3600 / 1000,
                        'distance_gap_m': distance_gap,
                        'status': 'impossible'
                    }
            
            # Calculate time to overtake
            overtake_time_seconds = distance_gap / relative_speed_ms
            
            # Add some buffer time for actual overtaking maneuver
            try:
                buffer_time = self.forecasting_config.OVERTAKING_BUFFER_TIME
            except AttributeError:
                buffer_time = 5  # Default 5 seconds buffer
            
            overtake_time_seconds += buffer_time
            
            return {
                'forecast_seconds': overtake_time_seconds,
                'forecast_minutes': overtake_time_seconds / 60,
                'can_overtake': True,
                'already_ahead': False,
                'message': f"{chasing_car_data['truck_name']} will overtake {target_car_data['truck_name']} in {overtake_time_seconds:.1f} seconds",
                'relative_speed_kmh': relative_speed_ms * 3600 / 1000,
                'distance_gap_m': distance_gap,
                'chasing_car_trend': chasing_trend['trend'],
                'target_car_trend': target_trend['trend']
            }
            
        except Exception as e:
            return {
                'forecast_seconds': -1,
                'forecast_minutes': -1,
                'can_overtake': False,
                'already_ahead': False,
                'message': f"Error calculating forecast: {str(e)}",
                'error': True
            }
    
    def calculate_overtake_requirements(self, chasing_car_data, target_car_data, chasing_distance, target_distance, current_time):
        """Calculate detailed overtaking requirements and scenarios"""
        try:
            # Get speed trends for both cars
            chasing_trend = self.calculate_speed_trend(chasing_car_data, current_time)
            target_trend = self.calculate_speed_trend(target_car_data, current_time)
            
            # Calculate gap in distance
            distance_gap = target_distance - chasing_distance
            
            # Current speeds in km/h and m/s
            chasing_speed_kmh = chasing_trend['current_speed']
            target_speed_kmh = target_trend['current_speed']
            chasing_speed_ms = max(chasing_speed_kmh * 1000 / 3600, 0.1)
            target_speed_ms = max(target_speed_kmh * 1000 / 3600, 0.1)
            
            # Calculate current relative speed
            current_relative_speed_ms = chasing_speed_ms - target_speed_ms
            current_relative_speed_kmh = current_relative_speed_ms * 3600 / 1000
            
            # Calculate required speed scenarios
            scenarios = []
            
            # Scenario 1: Maintain current target speed, increase chasing speed
            if target_speed_kmh > 0:
                for time_window in [30, 60, 120, 300]:  # 30s, 1min, 2min, 5min
                    required_speed_ms = (distance_gap / time_window) + target_speed_ms
                    required_speed_kmh = required_speed_ms * 3600 / 1000
                    speed_increase_needed = required_speed_kmh - chasing_speed_kmh
                    
                    scenarios.append({
                        'scenario': f'Overtake in {time_window} seconds',
                        'time_window_seconds': int(time_window),
                        'target_maintains_speed': float(target_speed_kmh),
                        'chasing_required_speed': float(required_speed_kmh),
                        'speed_increase_needed': float(speed_increase_needed),
                        'feasible': bool(speed_increase_needed <= 30),  # Reasonable speed increase limit
                        'advantage_needed_percent': float((speed_increase_needed / max(chasing_speed_kmh, 1)) * 100)
                    })
            
            # Scenario 2: What if target car slows down
            for target_reduction in [5, 10, 20]:  # km/h reductions
                new_target_speed_kmh = max(target_speed_kmh - target_reduction, 0)
                new_target_speed_ms = new_target_speed_kmh * 1000 / 3600
                
                if distance_gap > 0:
                    # Time to overtake if target slows down
                    new_relative_speed_ms = chasing_speed_ms - new_target_speed_ms
                    new_relative_speed_kmh = new_relative_speed_ms * 3600 / 1000
                    
                    if new_relative_speed_ms > 0:
                        overtake_time = distance_gap / new_relative_speed_ms
                        scenarios.append({
                            'scenario': f'If target slows by {target_reduction} km/h',
                            'time_window_seconds': float(overtake_time),
                            'time_window_minutes': float(overtake_time / 60),
                            'target_new_speed': float(new_target_speed_kmh),
                            'chasing_maintains_speed': float(chasing_speed_kmh),
                            'speed_increase_needed': 0.0,
                            'relative_speed_advantage': float(new_relative_speed_kmh),
                            'feasible': bool(overtake_time <= 600),  # Within 10 minutes
                            'advantage_type': 'target_slowdown'
                        })
                    else:
                        # Even with target slowdown, chasing car still not fast enough
                        scenarios.append({
                            'scenario': f'If target slows by {target_reduction} km/h',
                            'time_window_seconds': -1,
                            'time_window_minutes': -1,
                            'target_new_speed': float(new_target_speed_kmh),
                            'chasing_maintains_speed': float(chasing_speed_kmh),
                            'speed_increase_needed': float(abs(new_relative_speed_kmh)),
                            'relative_speed_advantage': float(new_relative_speed_kmh),
                            'feasible': False,
                            'advantage_type': 'target_slowdown',
                            'note': 'Still need to increase chasing car speed'
                        })
            
            # Scenario 3: Optimal speed combinations
            optimal_scenarios = []
            
            # Use default speed scenarios if config not available
            try:
                speed_increases = self.forecasting_config.SPEED_INCREASE_SCENARIOS
                speed_decreases = self.forecasting_config.SPEED_DECREASE_SCENARIOS
            except AttributeError:
                # Default scenarios if not configured
                speed_increases = [5, 10, 15, 20, 25]  # km/h increases
                speed_decreases = [0, 5, 10, 15]       # km/h decreases
            
            for chasing_increase in speed_increases:
                for target_decrease in speed_decreases:
                    new_chasing_speed_kmh = chasing_speed_kmh + chasing_increase
                    new_target_speed_kmh = max(target_speed_kmh - target_decrease, 0)
                    
                    new_chasing_speed_ms = new_chasing_speed_kmh * 1000 / 3600
                    new_target_speed_ms = new_target_speed_kmh * 1000 / 3600
                    
                    relative_speed_ms = new_chasing_speed_ms - new_target_speed_ms
                    
                    if relative_speed_ms > 0 and distance_gap > 0:
                        overtake_time = distance_gap / relative_speed_ms
                        
                        if overtake_time <= 300:  # Within 5 minutes
                            optimal_scenarios.append({
                                'chasing_speed_increase': int(chasing_increase),
                                'target_speed_decrease': int(target_decrease),
                                'new_chasing_speed': float(new_chasing_speed_kmh),
                                'new_target_speed': float(new_target_speed_kmh),
                                'overtake_time_seconds': float(overtake_time),
                                'overtake_time_minutes': float(overtake_time / 60),
                                'relative_speed_advantage': float(relative_speed_ms * 3600 / 1000)
                            })
            
            # Sort optimal scenarios by time
            optimal_scenarios.sort(key=lambda x: x['overtake_time_seconds'])
            
            return {
                'chasing_car_name': chasing_car_data.get('truck_name', f'Car {chasing_car_data.get("id", "Unknown")}'),
                'target_car_name': target_car_data.get('truck_name', f'Car {target_car_data.get("id", "Unknown")}'),
                'current_gap_meters': float(distance_gap),
                'current_gap_seconds': float(distance_gap / max(chasing_speed_ms, 0.1) if distance_gap > 0 else 0),
                'current_speeds': {
                    'chasing_speed_kmh': float(chasing_speed_kmh),
                    'target_speed_kmh': float(target_speed_kmh),
                    'relative_speed_kmh': float(current_relative_speed_kmh)
                },
                'speed_trends': {
                    'chasing_trend': str(chasing_trend['trend']),
                    'target_trend': str(target_trend['trend']),
                    'chasing_acceleration': float(chasing_trend['acceleration']),
                    'target_acceleration': float(target_trend['acceleration'])
                },
                'time_based_scenarios': scenarios[:5],  # Top 5 time-based scenarios
                'optimal_combinations': optimal_scenarios[:10],  # Top 10 optimal combinations
                'recommendations': self._generate_overtake_recommendations(scenarios, optimal_scenarios, chasing_trend, target_trend),
                'analysis_time': current_time.strftime('%H:%M:%S.%f')[:-3]
            }
            
        except Exception as e:
            return {
                'error': True,
                'message': f'Error calculating overtake requirements: {str(e)}',
                'chasing_car_name': chasing_car_data.get('truck_name', f'Car {chasing_car_data.get("id", "Unknown")}'),
                'target_car_name': target_car_data.get('truck_name', f'Car {target_car_data.get("id", "Unknown")}')
            }
    
    def _generate_overtake_recommendations(self, scenarios, optimal_scenarios, chasing_trend, target_trend):
        """Generate intelligent recommendations for overtaking"""
        recommendations = []
        
        # Analyze feasible scenarios
        feasible_scenarios = [s for s in scenarios if s.get('feasible', False)]
        
        if not feasible_scenarios and not optimal_scenarios:
            recommendations.append({
                'type': 'impossible',
                'message': 'Overtaking appears very difficult with current speed patterns',
                'suggestion': 'Wait for target car to slow down or find opportunity to significantly increase speed'
            })
        elif optimal_scenarios:
            best_scenario = optimal_scenarios[0]
            if best_scenario['overtake_time_seconds'] <= 60:
                recommendations.append({
                    'type': 'immediate_opportunity',
                    'message': f'Quick overtake possible in {best_scenario["overtake_time_seconds"]:.1f} seconds',
                    'suggestion': f'Increase speed by {best_scenario["chasing_speed_increase"]} km/h to {best_scenario["new_chasing_speed"]} km/h'
                })
            else:
                recommendations.append({
                    'type': 'strategic_overtake',
                    'message': f'Strategic overtake possible in {best_scenario["overtake_time_minutes"]:.1f} minutes',
                    'suggestion': f'Gradually increase speed by {best_scenario["chasing_speed_increase"]} km/h'
                })
        
        # Speed trend analysis
        if chasing_trend['trend'] == 'accelerating' and target_trend['trend'] == 'decelerating':
            recommendations.append({
                'type': 'favorable_trends',
                'message': 'Speed trends are favorable for overtaking',
                'suggestion': 'Maintain current acceleration pattern'
            })
        elif chasing_trend['trend'] == 'decelerating':
            recommendations.append({
                'type': 'unfavorable_trend',
                'message': 'Chasing car is slowing down',
                'suggestion': 'Need to reverse deceleration trend to enable overtaking'
            })
        
        return recommendations
    
    def _calculate_time_advantage(self, leading_car_data, following_car_data, current_time):
        """Calculate how much time advantage the leading car has"""
        try:
            # Get current speeds
            leading_trend = self.calculate_speed_trend(leading_car_data, current_time)
            following_trend = self.calculate_speed_trend(following_car_data, current_time)
            
            # Calculate based on following car's speed
            following_speed_ms = max(following_trend['current_speed'] * 1000 / 3600, 0.1)
            
            # Time advantage is distance advantage divided by following car's speed
            return {
                'leading_speed': leading_trend['current_speed'],
                'following_speed': following_trend['current_speed'],
                'speed_difference': leading_trend['current_speed'] - following_trend['current_speed']
            }
        except Exception as e:
            return {
                'leading_speed': 0,
                'following_speed': 0,
                'speed_difference': 0,
                'error': str(e)
            }
