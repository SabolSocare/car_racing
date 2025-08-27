#!/usr/bin/env python3
"""
Distance Reset Handler Module
Handles distance reset detection and recovery for F1 timing system
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DistanceResetEvent:
    """Data class for distance reset events"""
    car_id: int
    timestamp: datetime
    prev_distance: float
    current_distance: float
    drop_percentage: float
    reset_type: str
    recovery_method: str
    confidence: float
    details: Dict[str, Any]

@dataclass
class RecoveryResult:
    """Data class for recovery operation results"""
    success: bool
    recovered_distance: float
    method_used: str
    confidence: float
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DistanceResetHandler:
    """
    Advanced distance reset detection and recovery system
    
    Handles the common causes of distance resets:
    - GPS signal loss → Speed integration fallback
    - Sensor resets → History-based recovery  
    - Data gaps → Interpolation
    - Invalid coordinates → GPS validation
    - Speed anomalies → Realistic limits
    """
    
    def __init__(self):
        # Detection thresholds from config
        self.drop_threshold = getattr(config.DistanceReset, 'DROP_THRESHOLD_PERCENT', 80)
        self.speed_anomaly_threshold = getattr(config.DistanceReset, 'SPEED_ANOMALY_THRESHOLD', 150)  # km/h
        self.max_speed_increase = getattr(config.DistanceReset, 'MAX_SPEED_INCREASE', 50)  # km/h per second
        self.min_valid_distance = getattr(config.DistanceReset, 'MIN_VALID_DISTANCE', 10)  # meters
        
        # Recovery configuration
        self.history_window_seconds = getattr(config.DistanceReset, 'HISTORY_WINDOW_SECONDS', 300)
        self.interpolation_max_gap = getattr(config.DistanceReset, 'INTERPOLATION_MAX_GAP_SECONDS', 60)
        self.gps_validation_radius = getattr(config.DistanceReset, 'GPS_VALIDATION_RADIUS_METERS', 1000)
        
        # Internal state
        self.distance_history: Dict[int, List[Tuple[datetime, float]]] = {}
        self.last_good_positions: Dict[int, Dict[str, Any]] = {}
        self.reset_events: List[DistanceResetEvent] = []
        self.recovery_stats: Dict[str, int] = {
            'speed_integration': 0,
            'gps_recovery': 0,
            'linear_interpolation': 0,
            'fallback': 0,
            'total_resets': 0
        }
        
        # GPS validation cache
        self.gps_validation_cache: Dict[str, bool] = {}
        
    def detect_distance_reset(self, car_id: int, current_time: datetime, 
                            current_distance: float, car_data: Dict[str, Any]) -> Optional[DistanceResetEvent]:
        """
        Detect if a distance reset has occurred
        
        Returns:
            DistanceResetEvent if reset detected, None otherwise
        """
        
        # Initialize history if needed
        if car_id not in self.distance_history:
            self.distance_history[car_id] = []
            
        history = self.distance_history[car_id]
        
        # Need at least one previous reading
        if not history:
            self._add_to_history(car_id, current_time, current_distance)
            return None
            
        # Get most recent distance
        prev_time, prev_distance = history[-1]
        time_diff = (current_time - prev_time).total_seconds()
        
        # Skip if too much time has passed (data gap)
        if time_diff > 300:  # 5 minutes
            logger.warning(f"Large time gap for car {car_id}: {time_diff:.1f}s")
            self._add_to_history(car_id, current_time, current_distance)
            return None
        
        # Detection Method 1: Large distance drop
        if prev_distance > 0 and current_distance < prev_distance:
            drop_amount = prev_distance - current_distance
            drop_percentage = (drop_amount / prev_distance) * 100
            
            if drop_percentage > self.drop_threshold:
                reset_event = DistanceResetEvent(
                    car_id=car_id,
                    timestamp=current_time,
                    prev_distance=prev_distance,
                    current_distance=current_distance,
                    drop_percentage=drop_percentage,
                    reset_type='distance_drop',
                    recovery_method='',
                    confidence=min(drop_percentage / 100, 1.0),
                    details={
                        'drop_amount': drop_amount,
                        'time_diff': time_diff,
                        'prev_time': prev_time
                    }
                )
                
                logger.warning(f"Distance drop detected for car {car_id}: "
                             f"{drop_percentage:.1f}% drop ({prev_distance:.1f}m → {current_distance:.1f}m)")
                
                self.reset_events.append(reset_event)
                self.recovery_stats['total_resets'] += 1
                return reset_event
        
        # Detection Method 2: Unrealistic speed increase
        if time_diff > 0:
            distance_change = abs(current_distance - prev_distance)
            implied_speed_ms = distance_change / time_diff
            implied_speed_kmh = implied_speed_ms * 3.6
            
            if implied_speed_kmh > self.speed_anomaly_threshold:
                reset_event = DistanceResetEvent(
                    car_id=car_id,
                    timestamp=current_time,
                    prev_distance=prev_distance,
                    current_distance=current_distance,
                    drop_percentage=0,
                    reset_type='speed_anomaly',
                    recovery_method='',
                    confidence=min(implied_speed_kmh / 200, 1.0),
                    details={
                        'implied_speed_kmh': implied_speed_kmh,
                        'time_diff': time_diff,
                        'distance_change': distance_change
                    }
                )
                
                logger.warning(f"Speed anomaly detected for car {car_id}: "
                             f"implied speed {implied_speed_kmh:.1f} km/h")
                
                self.reset_events.append(reset_event)
                self.recovery_stats['total_resets'] += 1
                return reset_event
        
        # Detection Method 3: Distance validation against GPS
        position_data = self._get_position_data_at_time(car_data, current_time)
        if position_data and self._is_valid_gps_coordinate(position_data.get('lat', 0), position_data.get('lon', 0)):
            gps_based_distance = self._calculate_gps_distance_from_start(car_data, current_time)
            if gps_based_distance > 0:
                distance_diff = abs(current_distance - gps_based_distance)
                diff_percentage = (distance_diff / max(gps_based_distance, 1)) * 100
                
                if diff_percentage > 50:  # 50% difference threshold
                    reset_event = DistanceResetEvent(
                        car_id=car_id,
                        timestamp=current_time,
                        prev_distance=prev_distance,
                        current_distance=current_distance,
                        drop_percentage=diff_percentage,
                        reset_type='gps_mismatch',
                        recovery_method='',
                        confidence=min(diff_percentage / 100, 1.0),
                        details={
                            'gps_distance': gps_based_distance,
                            'calculated_distance': current_distance,
                            'difference': distance_diff
                        }
                    )
                    
                    logger.warning(f"GPS mismatch detected for car {car_id}: "
                                 f"calculated {current_distance:.1f}m vs GPS {gps_based_distance:.1f}m")
                    
                    self.reset_events.append(reset_event)
                    self.recovery_stats['total_resets'] += 1
                    return reset_event
        
        # No reset detected - add to history
        self._add_to_history(car_id, current_time, current_distance)
        return None
    
    def recover_distance(self, reset_event: DistanceResetEvent, car_data: Dict[str, Any]) -> RecoveryResult:
        """
        Recover distance using multiple methods in order of preference
        
        Recovery Methods:
        1. Speed Integration: Recalculates from last good point
        2. GPS Recovery: Uses coordinates when available  
        3. Linear Interpolation: Estimates based on average speed
        4. Fallback: Uses last known good distance
        """
        
        car_id = reset_event.car_id
        timestamp = reset_event.timestamp
        
        logger.info(f"Attempting distance recovery for car {car_id} at {timestamp}")
        
        # Method 1: Speed Integration Recovery
        result = self._recover_by_speed_integration(reset_event, car_data)
        if result.success:
            reset_event.recovery_method = 'speed_integration'
            self.recovery_stats['speed_integration'] += 1
            logger.info(f"Speed integration recovery successful for car {car_id}: {result.recovered_distance:.1f}m")
            return result
        
        # Method 2: GPS Recovery
        result = self._recover_by_gps(reset_event, car_data)
        if result.success:
            reset_event.recovery_method = 'gps_recovery'
            self.recovery_stats['gps_recovery'] += 1
            logger.info(f"GPS recovery successful for car {car_id}: {result.recovered_distance:.1f}m")
            return result
        
        # Method 3: Linear Interpolation
        result = self._recover_by_interpolation(reset_event, car_data)
        if result.success:
            reset_event.recovery_method = 'linear_interpolation'
            self.recovery_stats['linear_interpolation'] += 1
            logger.info(f"Interpolation recovery successful for car {car_id}: {result.recovered_distance:.1f}m")
            return result
        
        # Method 4: Fallback to last good distance
        result = self._recover_by_fallback(reset_event)
        reset_event.recovery_method = 'fallback'
        self.recovery_stats['fallback'] += 1
        logger.warning(f"Using fallback recovery for car {car_id}: {result.recovered_distance:.1f}m")
        
        return result
    
    def _recover_by_speed_integration(self, reset_event: DistanceResetEvent, car_data: Dict[str, Any]) -> RecoveryResult:
        """Recovery Method 1: Speed Integration from last good point"""
        try:
            car_id = reset_event.car_id
            current_time = reset_event.timestamp
            
            # Find last good distance point
            history = self.distance_history.get(car_id, [])
            if len(history) < 2:
                return RecoveryResult(False, 0, 'speed_integration', 0, "Insufficient history")
            
            last_good_time, last_good_distance = history[-2]  # Skip the problematic one
            
            # Get speed data between last good point and current time
            df = car_data['data']
            mask = (df['timeStamp'] > last_good_time) & (df['timeStamp'] <= current_time)
            speed_data = df.loc[mask].copy()
            
            if len(speed_data) == 0:
                return RecoveryResult(False, 0, 'speed_integration', 0, "No speed data available")
            
            # Integrate speed over time
            recovered_distance = last_good_distance
            
            for i in range(len(speed_data)):
                if i == 0:
                    time_diff = (speed_data.iloc[i]['timeStamp'] - last_good_time).total_seconds()
                else:
                    time_diff = (speed_data.iloc[i]['timeStamp'] - speed_data.iloc[i-1]['timeStamp']).total_seconds()
                
                speed_kmh = speed_data.iloc[i].get('speed', 0)
                if pd.isna(speed_kmh) or speed_kmh < 0:
                    continue
                    
                # Apply realistic speed limits
                speed_kmh = min(speed_kmh, self.speed_anomaly_threshold)
                
                speed_ms = speed_kmh * 1000 / 3600
                distance_increment = speed_ms * time_diff
                recovered_distance += distance_increment
            
            # Validate result
            if recovered_distance > last_good_distance and recovered_distance < last_good_distance * 3:
                return RecoveryResult(
                    True, 
                    recovered_distance, 
                    'speed_integration', 
                    0.9,
                    metadata={
                        'last_good_distance': last_good_distance,
                        'integration_points': len(speed_data),
                        'time_span': (current_time - last_good_time).total_seconds()
                    }
                )
            
            return RecoveryResult(False, 0, 'speed_integration', 0, "Unrealistic result")
            
        except Exception as e:
            return RecoveryResult(False, 0, 'speed_integration', 0, f"Integration error: {str(e)}")
    
    def _recover_by_gps(self, reset_event: DistanceResetEvent, car_data: Dict[str, Any]) -> RecoveryResult:
        """Recovery Method 2: GPS-based distance calculation"""
        try:
            car_id = reset_event.car_id
            current_time = reset_event.timestamp
            
            # Calculate distance from GPS coordinates
            gps_distance = self._calculate_gps_distance_from_start(car_data, current_time)
            
            if gps_distance <= 0:
                return RecoveryResult(False, 0, 'gps_recovery', 0, "Invalid GPS distance")
            
            # Validate against history
            history = self.distance_history.get(car_id, [])
            if history:
                last_distance = history[-1][1]
                if gps_distance < last_distance * 0.5:  # Sanity check
                    return RecoveryResult(False, 0, 'gps_recovery', 0, "GPS distance too low")
            
            return RecoveryResult(
                True,
                gps_distance,
                'gps_recovery',
                0.8,
                metadata={
                    'gps_coordinates_used': True,
                    'validation_passed': True
                }
            )
            
        except Exception as e:
            return RecoveryResult(False, 0, 'gps_recovery', 0, f"GPS error: {str(e)}")
    
    def _recover_by_interpolation(self, reset_event: DistanceResetEvent, car_data: Dict[str, Any]) -> RecoveryResult:
        """Recovery Method 3: Linear interpolation based on average speed"""
        try:
            car_id = reset_event.car_id
            current_time = reset_event.timestamp
            
            # Get history for interpolation
            history = self.distance_history.get(car_id, [])
            if len(history) < 3:
                return RecoveryResult(False, 0, 'linear_interpolation', 0, "Insufficient history for interpolation")
            
            # Use last few points to calculate average speed
            recent_points = history[-3:]
            total_distance_change = recent_points[-1][1] - recent_points[0][1]
            total_time_change = (recent_points[-1][0] - recent_points[0][0]).total_seconds()
            
            if total_time_change <= 0:
                return RecoveryResult(False, 0, 'linear_interpolation', 0, "Invalid time range")
            
            avg_speed_ms = total_distance_change / total_time_change
            avg_speed_kmh = avg_speed_ms * 3.6
            
            # Apply realistic limits
            if avg_speed_kmh > self.speed_anomaly_threshold or avg_speed_kmh < 0:
                return RecoveryResult(False, 0, 'linear_interpolation', 0, "Unrealistic average speed")
            
            # Interpolate distance
            last_good_time, last_good_distance = recent_points[-1]
            time_diff = (current_time - last_good_time).total_seconds()
            
            if time_diff > self.interpolation_max_gap:
                return RecoveryResult(False, 0, 'linear_interpolation', 0, "Time gap too large for interpolation")
            
            distance_increment = avg_speed_ms * time_diff
            interpolated_distance = last_good_distance + distance_increment
            
            return RecoveryResult(
                True,
                interpolated_distance,
                'linear_interpolation',
                0.7,
                metadata={
                    'avg_speed_kmh': avg_speed_kmh,
                    'time_gap': time_diff,
                    'interpolation_points': len(recent_points)
                }
            )
            
        except Exception as e:
            return RecoveryResult(False, 0, 'linear_interpolation', 0, f"Interpolation error: {str(e)}")
    
    def _recover_by_fallback(self, reset_event: DistanceResetEvent) -> RecoveryResult:
        """Recovery Method 4: Fallback to last known good distance"""
        car_id = reset_event.car_id
        history = self.distance_history.get(car_id, [])
        
        if history:
            # Use the last good distance before the reset
            if len(history) >= 2:
                fallback_distance = history[-2][1]  # Skip the problematic reading
            else:
                fallback_distance = history[-1][1]
        else:
            fallback_distance = reset_event.prev_distance
        
        return RecoveryResult(
            True,
            fallback_distance,
            'fallback',
            0.5,
            metadata={
                'fallback_source': 'last_good_distance',
                'original_distance': reset_event.current_distance
            }
        )
    
    def _calculate_gps_distance_from_start(self, car_data: Dict[str, Any], target_time: datetime) -> float:
        """Calculate total distance traveled using GPS coordinates"""
        try:
            df = car_data['data']
            mask = df['timeStamp'] <= target_time
            gps_data = df.loc[mask].copy()
            
            if len(gps_data) < 2:
                return 0.0
            
            # Filter valid GPS coordinates
            valid_gps = (gps_data['lat'] != 0.0) & (gps_data['lon'] != 0.0) & \
                       (~gps_data['lat'].isna()) & (~gps_data['lon'].isna())
            
            gps_points = gps_data[valid_gps].copy()
            
            if len(gps_points) < 2:
                return 0.0
            
            # Calculate distance using Haversine formula for GPS coordinates
            total_distance = 0.0
            
            for i in range(1, len(gps_points)):
                lat1, lon1 = gps_points.iloc[i-1][['lat', 'lon']]
                lat2, lon2 = gps_points.iloc[i][['lat', 'lon']]
                
                if self._is_valid_gps_coordinate(lat1, lon1) and self._is_valid_gps_coordinate(lat2, lon2):
                    distance = self._haversine_distance(lat1, lon1, lat2, lon2)
                    total_distance += distance
            
            return total_distance
            
        except Exception as e:
            logger.error(f"GPS distance calculation error: {str(e)}")
            return 0.0
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS points using Haversine formula"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def _is_valid_gps_coordinate(self, lat: float, lon: float) -> bool:
        """Validate GPS coordinates"""
        if pd.isna(lat) or pd.isna(lon):
            return False
        
        # Check if coordinates are reasonable (not 0,0 or obviously wrong)
        if lat == 0.0 and lon == 0.0:
            return False
        
        # Basic range checks
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return False
        
        return True
    
    def _get_position_data_at_time(self, car_data: Dict[str, Any], target_time: datetime) -> Optional[Dict[str, Any]]:
        """Get position data at specific time"""
        try:
            df = car_data['data']
            time_diff = abs(df['timeStamp'] - target_time)
            if len(time_diff) == 0:
                return None
                
            closest_idx = time_diff.idxmin()
            row = df.loc[closest_idx]
            
            return {
                'timestamp': row['timeStamp'],
                'lat': row.get('lat', 0),
                'lon': row.get('lon', 0),
                'speed': row.get('speed', 0),
                'x': row.get('x', 0),
                'y': row.get('y', 0)
            }
        except Exception:
            return None
    
    def _add_to_history(self, car_id: int, timestamp: datetime, distance: float):
        """Add distance reading to history"""
        if car_id not in self.distance_history:
            self.distance_history[car_id] = []
        
        history = self.distance_history[car_id]
        history.append((timestamp, distance))
        
        # Limit history size
        max_history = getattr(config.DistanceReset, 'MAX_HISTORY_SIZE', 1000)
        if len(history) > max_history:
            history[:] = history[-max_history:]
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status for API endpoint"""
        total_events = len(self.reset_events)
        
        # Calculate success rates
        success_rates = {}
        for method, count in self.recovery_stats.items():
            if method != 'total_resets' and self.recovery_stats['total_resets'] > 0:
                success_rates[method] = (count / self.recovery_stats['total_resets']) * 100
        
        # Recent events (last 10)
        recent_events = []
        for event in self.reset_events[-10:]:
            recent_events.append({
                'car_id': event.car_id,
                'timestamp': event.timestamp.isoformat(),
                'reset_type': event.reset_type,
                'recovery_method': event.recovery_method,
                'drop_percentage': event.drop_percentage,
                'confidence': event.confidence
            })
        
        return {
            'system_status': 'active',
            'total_resets_detected': total_events,
            'recovery_stats': self.recovery_stats.copy(),
            'success_rates': success_rates,
            'recent_events': recent_events,
            'cars_monitored': len(self.distance_history),
            'detection_thresholds': {
                'drop_threshold_percent': self.drop_threshold,
                'speed_anomaly_threshold_kmh': self.speed_anomaly_threshold,
                'max_speed_increase_kmh_per_s': self.max_speed_increase
            },
            'recovery_methods': {
                'speed_integration': 'Recalculates from last good point using speed data',
                'gps_recovery': 'Uses GPS coordinates when available',
                'linear_interpolation': 'Estimates based on average speed',
                'fallback': 'Uses last known good distance'
            },
            'validation_features': [
                'Real-time distance monitoring',
                'Automatic error correction', 
                'Logging of all issues',
                'API endpoint for monitoring status'
            ],
            'common_causes_addressed': {
                'gps_signal_loss': '✅ Speed integration fallback',
                'sensor_resets': '✅ History-based recovery',
                'data_gaps': '✅ Interpolation',
                'invalid_coordinates': '✅ GPS validation',
                'speed_anomalies': '✅ Realistic limits'
            }
        }
    
    def get_car_distance_status(self, car_id: int) -> Dict[str, Any]:
        """Get distance status for specific car"""
        history = self.distance_history.get(car_id, [])
        car_events = [e for e in self.reset_events if e.car_id == car_id]
        
        return {
            'car_id': car_id,
            'history_points': len(history),
            'last_update': history[-1][0].isoformat() if history else None,
            'current_distance': history[-1][1] if history else 0,
            'reset_events_count': len(car_events),
            'last_reset': car_events[-1].timestamp.isoformat() if car_events else None,
            'recovery_methods_used': list(set(e.recovery_method for e in car_events if e.recovery_method))
        }
