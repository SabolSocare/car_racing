#!/usr/bin/env python3
"""
Timing Engine Module
Core timing and ranking calculation engine
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import threading
import time

from config import config
from .performance_monitor import monitor_performance
from .car_status import CarStatusDetector
from .forecasting import OvertakingForecaster
from .distance_reset_handler import DistanceResetHandler


class F1LiveTiming:
    """Main F1 Live Timing System"""
    
    def __init__(self, data_directory, socketio_instance):
        self.data_directory = data_directory
        self.socketio = socketio_instance
        self.car_data = {}
        self.current_time = None
        self.race_start_time = None
        self.current_rankings = []
        self.is_running = False
        
        # Load configuration settings
        self.update_interval = config.Performance.UPDATE_INTERVAL
        self.broadcast_interval = config.Performance.BROADCAST_INTERVAL
        self.distance_cache = {}  # Cache for distance calculations
        self.position_cache = {}  # Cache for position data
        
        # Simulation speed control
        self.simulation_speed = config.Simulation.DEFAULT_SPEED
        
        # Initialize sub-modules
        self.status_detector = CarStatusDetector()
        self.forecaster = OvertakingForecaster()
        self.distance_reset_handler = DistanceResetHandler()
        
    def load_car_data(self):
        """Load all car data from CSV files"""
        csv_files = [f for f in os.listdir(self.data_directory) if f.endswith('.csv')]
        print(f"Found {len(csv_files)} CSV files.")

        for csv_file in csv_files:
            file_path = os.path.join(self.data_directory, csv_file)
            print(os.path.abspath(file_path))
            
            try:
                df = pd.read_csv(file_path)
                df['timeStamp'] = pd.to_datetime(df['timeStamp'])
                
                # Extract truck name from filename
                truck_name = ""
                if 'truck' in csv_file:
                    # Extract truck number from filename like "truck45" or "truck5"
                    truck_part = csv_file.split('truck')[1].split('-')[0]
                    truck_name = f"TRUCK{truck_part}"
                
                # Extract car ID for internal use
                car_id = df['car'].iloc[0]
                if pd.isna(car_id):
                    car_id = int(csv_file.split('truck')[1].split('-')[0])
                else:
                    car_id = int(float(car_id))
                
                # Store both the dataframe and truck name
                self.car_data[car_id] = {
                    'data': df.sort_values('timeStamp'),
                    'truck_name': truck_name,
                    'file_name': csv_file
                }
                print(f"Loaded {truck_name} (Car #{car_id}): {len(df)} records")
                
            except Exception as e:
                print(f"Error loading {csv_file}: {str(e)}")
        
        if self.car_data:
            # Find the latest start time among all cars (for synchronized lab race start)
            all_start_times = [car['data']['timeStamp'].min() for car in self.car_data.values()]
            self.race_start_time = max(all_start_times)  # Use latest start to sync all cars
            self.current_time = self.race_start_time
            print(f"Race start time (synchronized): {self.race_start_time}")
            
            # Log data quality for each car
            for car_id, car_info in self.car_data.items():
                df = car_info['data']
                valid_gps_count = 0
                if 'lat' in df.columns and 'lon' in df.columns:
                    valid_gps = (df['lat'] != 0.0) & (df['lon'] != 0.0) & \
                               (~df['lat'].isna()) & (~df['lon'].isna())
                    valid_gps_count = valid_gps.sum()
                
                print(f"{car_info['truck_name']}: {len(df)} records, {valid_gps_count} with valid GPS")
    
    @monitor_performance
    def calculate_distance_traveled(self, car_id, up_to_time):
        """Calculate total distance traveled with reset detection and recovery"""
        cache_key = f"{car_id}_{up_to_time.timestamp()}"
        
        if cache_key in self.distance_cache:
            return self.distance_cache[cache_key]
        
        df = self.car_data[car_id]['data']
        mask = df['timeStamp'] <= up_to_time
        car_positions = df.loc[mask].copy()
        
        if len(car_positions) < 2:
            return 0.0
        
        # Calculate preliminary distance using best available method
        preliminary_distance = self._calculate_preliminary_distance(car_id, car_positions)
        
        # Check for distance reset issues
        reset_event = self.distance_reset_handler.detect_distance_reset(
            car_id, up_to_time, preliminary_distance, self.car_data[car_id]
        )
        
        final_distance = preliminary_distance
        
        # If reset detected, attempt recovery
        if reset_event:
            recovery_result = self.distance_reset_handler.recover_distance(
                reset_event, self.car_data[car_id]
            )
            
            if recovery_result.success:
                final_distance = recovery_result.recovered_distance
                print(f"✅ Distance recovered for car {car_id}: "
                      f"{preliminary_distance:.1f}m → {final_distance:.1f}m "
                      f"using {recovery_result.method_used}")
            else:
                print(f"❌ Distance recovery failed for car {car_id}: {recovery_result.error_message}")
        
        # Cache the result
        self.distance_cache[cache_key] = final_distance
        
        # Limit cache size to prevent memory bloat
        if len(self.distance_cache) > config.Performance.DISTANCE_CACHE_SIZE:
            oldest_keys = list(self.distance_cache.keys())[:config.Performance.CACHE_CLEANUP_THRESHOLD]
            for key in oldest_keys:
                del self.distance_cache[key]
        
        return final_distance
    
    def _calculate_preliminary_distance(self, car_id, car_positions):
        """Calculate distance using best available method (before reset detection)"""
        # Method 1: Try GPS-based calculation for cars with valid coordinates
        if 'lat' in car_positions.columns and 'lon' in car_positions.columns:
            valid_gps = (car_positions['lat'] != 0.0) & (car_positions['lon'] != 0.0) & \
                       (~car_positions['lat'].isna()) & (~car_positions['lon'].isna())
            
            if valid_gps.any():
                car_positions_gps = car_positions[valid_gps].copy()
                if len(car_positions_gps) >= 2:
                    # Calculate distance using lat/lon (more accurate for lab races)
                    lat_diff = car_positions_gps['lat'].diff() * 111000  # ~111km per degree
                    lon_diff = car_positions_gps['lon'].diff() * 111000 * np.cos(np.radians(car_positions_gps['lat']))
                    distances = np.sqrt(lat_diff**2 + lon_diff**2)
                    total_distance = distances.sum()
                    return total_distance
        
        # Method 2: Speed integration method (more accurate for lab data)
        if 'speed' in car_positions.columns and not car_positions['speed'].isna().all():
            # Remove invalid speed data
            valid_speed = car_positions['speed'].notna() & (car_positions['speed'] >= 0)
            if valid_speed.any():
                speed_data = car_positions[valid_speed].copy()
                if len(speed_data) >= 2:
                    # Calculate time differences in seconds
                    speed_data['time_diff'] = speed_data['timeStamp'].diff().dt.total_seconds()
                    
                    # Convert speed from km/h to m/s and integrate over time
                    speed_data['speed_ms'] = speed_data['speed'] * 1000 / 3600
                    speed_data['distance_segment'] = speed_data['speed_ms'] * speed_data['time_diff']
                    
                    # Remove invalid segments
                    valid_segments = speed_data['distance_segment'].notna() & (speed_data['distance_segment'] >= 0)
                    total_distance = speed_data.loc[valid_segments, 'distance_segment'].sum()
                    return total_distance
        
        # Method 3: Fallback to x,y coordinates (least accurate)
        print(f"Warning: Car {car_id} using x,y coordinates (least accurate method)")
        x_diff = car_positions['x'].diff()
        y_diff = car_positions['y'].diff()
        distances = np.sqrt(x_diff**2 + y_diff**2)
        total_distance = distances.sum()
        
        return total_distance
    
    def get_car_position_at_time(self, car_id, target_time):
        """Get car's position data at a specific time"""
        df = self.car_data[car_id]['data']
        
        # Find the closest timestamp
        time_diff = abs(df['timeStamp'] - target_time)
        if len(time_diff) == 0:
            return None
            
        closest_idx = time_diff.idxmin()
        row = df.loc[closest_idx]
        
        return {
            'timestamp': row['timeStamp'],
            'lat': row['lat'] if not pd.isna(row['lat']) else 0,
            'lon': row['lon'] if not pd.isna(row['lon']) else 0,
            'speed': row['speed'] if not pd.isna(row['speed']) else 0,
            'x': row['x'],
            'y': row['y']
        }
    
    def determine_car_status(self, car_id, current_time):
        """Determine car status using the status detector"""
        return self.status_detector.determine_car_status(self.car_data[car_id], current_time)
    
    def calculate_speed_trend(self, car_id, current_time, window_seconds=None):
        """Calculate speed trend using the forecaster"""
        return self.forecaster.calculate_speed_trend(self.car_data[car_id], current_time, window_seconds)
    
    def forecast_overtake_time(self, chasing_car_id, target_car_id, current_time):
        """Forecast overtake time using the forecaster"""
        chasing_distance = self.calculate_distance_traveled(chasing_car_id, current_time)
        target_distance = self.calculate_distance_traveled(target_car_id, current_time)
        
        return self.forecaster.forecast_overtake_time(
            self.car_data[chasing_car_id],
            self.car_data[target_car_id],
            chasing_distance,
            target_distance,
            current_time
        )
    
    def calculate_overtake_requirements(self, chasing_car_id, target_car_id, current_time):
        """Calculate overtake requirements using the forecaster"""
        chasing_distance = self.calculate_distance_traveled(chasing_car_id, current_time)
        target_distance = self.calculate_distance_traveled(target_car_id, current_time)
        
        return self.forecaster.calculate_overtake_requirements(
            self.car_data[chasing_car_id],
            self.car_data[target_car_id],
            chasing_distance,
            target_distance,
            current_time
        )
    
    def get_car_comparison_analysis(self, car1_id, car2_id, current_time):
        """Get detailed comparison analysis between two cars"""
        try:
            car1_data = {
                'id': car1_id,
                'name': self.car_data[car1_id]['truck_name'],
                'distance': self.calculate_distance_traveled(car1_id, current_time),
                'position_data': self.get_car_position_at_time(car1_id, current_time),
                'speed_trend': self.calculate_speed_trend(car1_id, current_time),
                'status': self.determine_car_status(car1_id, current_time)
            }
            
            car2_data = {
                'id': car2_id,
                'name': self.car_data[car2_id]['truck_name'],
                'distance': self.calculate_distance_traveled(car2_id, current_time),
                'position_data': self.get_car_position_at_time(car2_id, current_time),
                'speed_trend': self.calculate_speed_trend(car2_id, current_time),
                'status': self.determine_car_status(car2_id, current_time)
            }
            
            # Determine who's ahead
            if car1_data['distance'] > car2_data['distance']:
                ahead_car, behind_car = car1_data, car2_data
            else:
                ahead_car, behind_car = car2_data, car1_data
            
            distance_gap = ahead_car['distance'] - behind_car['distance']
            speed_gap = behind_car['speed_trend']['current_speed'] - ahead_car['speed_trend']['current_speed']
            
            return {
                'car1': car1_data,
                'car2': car2_data,
                'leader': ahead_car,
                'chaser': behind_car,
                'gap_analysis': {
                    'distance_gap_meters': distance_gap,
                    'speed_gap_kmh': speed_gap,
                    'time_gap_seconds': distance_gap / max(behind_car['speed_trend']['current_speed'] * 1000 / 3600, 0.1)
                },
                'overtake_forecast': self.forecast_overtake_time(behind_car['id'], ahead_car['id'], current_time),
                'overtake_requirements': self.calculate_overtake_requirements(behind_car['id'], ahead_car['id'], current_time)
            }
            
        except Exception as e:
            return {
                'error': True,
                'message': f'Error in comparison analysis: {str(e)}'
            }
    
    @monitor_performance
    def calculate_live_rankings(self):
        """Calculate current rankings and intervals with synchronized timestamps"""
        rankings = []
        # Ensure all calculations use the exact same timestamp
        synchronized_time = self.current_time
        
        for car_id in self.car_data.keys():
            # Check if car has data at synchronized time
            df = self.car_data[car_id]['data']
            if synchronized_time < df['timeStamp'].min() or synchronized_time > df['timeStamp'].max():
                continue
            
            # Calculate distance at the synchronized timestamp
            distance = self.calculate_distance_traveled(car_id, synchronized_time)
            position_data = self.get_car_position_at_time(car_id, synchronized_time)
            
            # Determine car status at synchronized time
            status = self.determine_car_status(car_id, synchronized_time)
            
            if position_data:
                race_time = (synchronized_time - self.race_start_time).total_seconds()
                
                rankings.append({
                    'car_id': car_id,
                    'truck_name': self.car_data[car_id]['truck_name'],
                    'distance_traveled': distance,
                    'current_speed': position_data['speed'],
                    'race_time': race_time,
                    'lat': position_data['lat'],
                    'lon': position_data['lon'],
                    'timestamp': synchronized_time.isoformat(),
                    'status': status,
                    'sync_timestamp': synchronized_time  # Store for gap calculations
                })
        
        # Sort by distance traveled (descending)
        rankings.sort(key=lambda x: x['distance_traveled'], reverse=True)
        
        # Add position numbers and calculate intervals
        for i, car in enumerate(rankings):
            car['position'] = i + 1
        
        # Calculate intervals with enhanced accuracy for lab races
        if rankings:
            # Leader has no gap
            rankings[0]['gap_to_leader'] = 0.0
            rankings[0]['gap_to_ahead'] = 0.0
            
            leader_distance = rankings[0]['distance_traveled']
            
            for i in range(1, len(rankings)):
                car = rankings[i]
                car_ahead = rankings[i-1]
                
                # Distance gaps (calculated at same synchronized timestamp)
                distance_gap_to_leader = leader_distance - car['distance_traveled']
                distance_gap_to_ahead = car_ahead['distance_traveled'] - car['distance_traveled']
                
                # Enhanced time gap calculation using synchronized timestamp
                time_gap_to_leader = self._calculate_enhanced_time_gap(
                    rankings[0], car, distance_gap_to_leader, synchronized_time)
                time_gap_to_ahead = self._calculate_enhanced_time_gap(
                    car_ahead, car, distance_gap_to_ahead, synchronized_time)
                
                # Apply realistic limits for lab races (max 300 seconds gap)
                MAX_REALISTIC_GAP = 300.0  # seconds
                
                if time_gap_to_leader > MAX_REALISTIC_GAP:
                    print(f"Warning: Large gap for {car['truck_name']}: {time_gap_to_leader:.1f}s")
                    time_gap_to_leader = min(time_gap_to_leader, MAX_REALISTIC_GAP)
                    
                if time_gap_to_ahead > MAX_REALISTIC_GAP:
                    time_gap_to_ahead = min(time_gap_to_ahead, MAX_REALISTIC_GAP)
                
                car['gap_to_leader'] = time_gap_to_leader
                car['gap_to_ahead'] = time_gap_to_ahead
        
        # Validate timestamp synchronization for debugging
        self.validate_timestamp_synchronization(rankings)
        
        self.current_rankings = rankings
        return rankings
    
    def _calculate_enhanced_time_gap(self, leading_car, following_car, distance_gap, synchronized_time):
        """Calculate more accurate time gap using average speeds and race progression at synchronized timestamp"""
        if distance_gap <= 0:
            return 0.0
        
        # Method 1: Use average pace instead of current speed for stability
        # Both cars calculated using the same synchronized timestamp
        leading_pace = self.get_average_pace_at_time(leading_car['car_id'], synchronized_time, 30)
        following_pace = self.get_average_pace_at_time(following_car['car_id'], synchronized_time, 30)
        
        # Convert to m/s
        leading_speed_ms = max(leading_pace * 1000 / 3600, 1)
        following_speed_ms = max(following_pace * 1000 / 3600, 1)
        
        # Enhanced gap calculation considering both cars' paces
        # Use harmonic mean for more realistic race gap calculation
        if leading_speed_ms > 0 and following_speed_ms > 0:
            harmonic_mean_speed = 2 / ((1/leading_speed_ms) + (1/following_speed_ms))
            time_gap = distance_gap / harmonic_mean_speed
        else:
            # Fallback to simple calculation
            effective_speed = (following_speed_ms + leading_speed_ms) / 2
            time_gap = distance_gap / max(effective_speed, 1)
        
        # Method 2: Apply pace differential adjustment
        pace_differential = following_pace - leading_pace
        
        if abs(pace_differential) > 2:  # Significant pace difference (> 2 km/h)
            # If following car is consistently faster, they'll close the gap faster
            # If leading car is consistently faster, the gap is more stable
            adjustment_factor = 1.0 - (pace_differential * 0.05)  # 5% per km/h difference
            adjustment_factor = max(0.6, min(1.5, adjustment_factor))  # Limit adjustment
            time_gap *= adjustment_factor
        
        return time_gap
    
    def get_average_pace_at_time(self, car_id, reference_time, time_window_seconds=60):
        """Calculate average pace over a time window at a specific synchronized timestamp"""
        try:
            df = self.car_data[car_id]['data']
            
            # Get data from the time window ending at reference_time
            start_time = reference_time - pd.Timedelta(seconds=time_window_seconds)
            mask = (df['timeStamp'] >= start_time) & (df['timeStamp'] <= reference_time)
            recent_data = df.loc[mask].copy()
            
            if len(recent_data) < 2:
                return self._get_current_speed_from_data_at_time(car_id, reference_time)
            
            # Calculate average speed from distance and time
            if 'speed' in recent_data.columns and not recent_data['speed'].isna().all():
                valid_speeds = recent_data['speed'].dropna()
                if len(valid_speeds) > 0:
                    return valid_speeds.mean()
            
            # Fallback: calculate from position changes
            time_span = (recent_data['timeStamp'].max() - recent_data['timeStamp'].min()).total_seconds()
            if time_span > 0:
                distance_start = self.calculate_distance_traveled(car_id, recent_data['timeStamp'].min())
                distance_end = self.calculate_distance_traveled(car_id, recent_data['timeStamp'].max())
                distance_covered = distance_end - distance_start
                
                if distance_covered > 0:
                    avg_speed_ms = distance_covered / time_span
                    return avg_speed_ms * 3600 / 1000  # Convert to km/h
            
            return self._get_current_speed_from_data_at_time(car_id, reference_time)
            
        except Exception as e:
            return self._get_current_speed_from_data_at_time(car_id, reference_time)
    
    def _get_current_speed_from_data_at_time(self, car_id, timestamp):
        """Helper method to get current speed from car data at specific timestamp"""
        try:
            position_data = self.get_car_position_at_time(car_id, timestamp)
            if position_data and 'speed' in position_data:
                return position_data['speed']
            return 0.0
        except:
            return 0.0
    
    def validate_timestamp_synchronization(self, rankings):
        """Validate that all cars in rankings use the same synchronized timestamp"""
        if not rankings:
            return True
            
        reference_timestamp = rankings[0].get('sync_timestamp')
        if not reference_timestamp:
            return False
            
        for car in rankings:
            if car.get('sync_timestamp') != reference_timestamp:
                print(f"Warning: Timestamp mismatch for {car['truck_name']}")
                return False
                
        print(f"✅ All {len(rankings)} cars synchronized at {reference_timestamp.strftime('%H:%M:%S.%f')[:-3]}")
        return True
    
    def get_average_pace(self, car_id, time_window_seconds=60):
        """Calculate average pace over a time window for more stable gap calculations"""
        try:
            df = self.car_data[car_id]['data']
            
            # Get data from the last time window
            start_time = self.current_time - pd.Timedelta(seconds=time_window_seconds)
            mask = (df['timeStamp'] >= start_time) & (df['timeStamp'] <= self.current_time)
            recent_data = df.loc[mask].copy()
            
            if len(recent_data) < 2:
                return self._get_current_speed_from_data(car_id)
            
            # Calculate average speed from distance and time
            if 'speed' in recent_data.columns and not recent_data['speed'].isna().all():
                valid_speeds = recent_data['speed'].dropna()
                if len(valid_speeds) > 0:
                    return valid_speeds.mean()
            
            # Fallback: calculate from position changes
            time_span = (recent_data['timeStamp'].max() - recent_data['timeStamp'].min()).total_seconds()
            if time_span > 0:
                distance_start = self.calculate_distance_traveled(car_id, recent_data['timeStamp'].min())
                distance_end = self.calculate_distance_traveled(car_id, recent_data['timeStamp'].max())
                distance_covered = distance_end - distance_start
                
                if distance_covered > 0:
                    avg_speed_ms = distance_covered / time_span
                    return avg_speed_ms * 3600 / 1000  # Convert to km/h
            
            return self._get_current_speed_from_data(car_id)
            
        except Exception as e:
            return self._get_current_speed_from_data(car_id)
    
    def _get_current_speed_from_data(self, car_id):
        """Helper method to get current speed from car data"""
        try:
            position_data = self.get_current_data(car_id, self.current_time)
            if position_data and 'speed' in position_data:
                return position_data['speed']
            return 0.0
        except:
            return 0.0
    
    def _rankings_changed_significantly(self, old_rankings, new_rankings):
        """Check if rankings have changed significantly"""
        if not old_rankings or not new_rankings:
            return True
        
        if len(old_rankings) != len(new_rankings):
            return True
        
        # Check position changes
        for i, new_car in enumerate(new_rankings):
            if i >= len(old_rankings):
                return True
            old_car = old_rankings[i]
            if (new_car['car_id'] != old_car['car_id'] or 
                abs(new_car['current_speed'] - old_car['current_speed']) > config.Ranking.SIGNIFICANT_SPEED_CHANGE):
                return True
        
        return False

    def start_live_timing(self):
        """Start the live timing simulation with optimized performance"""
        self.is_running = True
        
        # Get the time range
        all_times = []
        for car_data in self.car_data.values():
            all_times.extend(car_data['data']['timeStamp'].tolist())
        
        end_time = max(all_times)
        
        def timing_loop():
            last_rankings = None
            update_counter = 0
            
            while self.is_running and self.current_time <= end_time:
                rankings = self.calculate_live_rankings()
                
                # Only emit if data has changed significantly or every nth update
                update_counter += 1
                should_broadcast = (
                    update_counter % self.broadcast_interval == 0 or  # Every nth update
                    self._rankings_changed_significantly(last_rankings, rankings)
                )
                
                if should_broadcast:
                    timing_data = self.get_current_data()
                    self.socketio.emit('timing_update', timing_data)
                    last_rankings = rankings.copy() if rankings else None
                
                # Advance simulation time based on speed setting
                race_time_advance_seconds = self.update_interval * self.simulation_speed
                race_time_advance = timedelta(seconds=race_time_advance_seconds)
                self.current_time += race_time_advance
                
                # Always sleep for the update interval (real time)
                time.sleep(self.update_interval)
            
            # Reset to start when finished and notify clients
            if self.current_time > end_time:
                self.current_time = self.race_start_time
                self.socketio.emit('race_finished', {'message': 'Race completed, resetting to start'})
        
        timing_thread = threading.Thread(target=timing_loop)
        timing_thread.daemon = True
        timing_thread.start()
    
    def stop_live_timing(self):
        """Stop the live timing simulation"""
        self.is_running = False
    
    def get_current_data(self):
        """Get current timing data for API"""
        # Clean rankings data for JSON serialization (remove sync_timestamp)
        clean_rankings = []
        if self.current_rankings:
            for car in self.current_rankings:
                clean_car = car.copy()
                # Remove non-serializable fields
                clean_car.pop('sync_timestamp', None)
                clean_rankings.append(clean_car)
        
        return {
            'current_time': self.current_time.strftime('%H:%M:%S.%f')[:-3] if self.current_time else '',
            'race_time': (self.current_time - self.race_start_time).total_seconds() if self.current_time and self.race_start_time else 0,
            'rankings': clean_rankings,
            'is_running': self.is_running,
            'total_cars': len(self.car_data)
        }
    
    def get_comparison_data(self, start_pos=1, count=5):
        """Get comparison data for specific position range"""
        if not self.current_rankings:
            return []
        
        # Get the requested range of cars
        end_pos = min(start_pos + count - 1, len(self.current_rankings))
        comparison_cars = self.current_rankings[start_pos-1:end_pos]
        
        # Add additional comparison metrics
        for i, car in enumerate(comparison_cars):
            car['relative_position'] = start_pos + i
            
        return comparison_cars
    
    def get_truck_list(self):
        """Get list of all trucks with their names"""
        trucks = []
        for car_id, car_info in self.car_data.items():
            trucks.append({
                'car_id': car_id,
                'truck_name': car_info['truck_name'],
                'file_name': car_info['file_name']
            })
        return sorted(trucks, key=lambda x: x['car_id'])
    
    def get_distance_reset_status(self):
        """Get distance reset monitoring status"""
        return self.distance_reset_handler.get_monitoring_status()
    
    def get_car_distance_status(self, car_id):
        """Get distance status for specific car"""
        return self.distance_reset_handler.get_car_distance_status(car_id)
