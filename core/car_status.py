#!/usr/bin/env python3
"""
Car Status Detection Module
Handles detection of car states (RUNNING, STOPPED, PIT, OUT)
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from config import config


class CarStatusDetector:
    """Handles car status detection based on telemetry data"""
    
    def __init__(self):
        # Load configuration settings
        self.status_config = {
            'stopped_speed_threshold': config.StatusDetection.STOPPED_SPEED_THRESHOLD,
            'pit_speed_threshold': config.StatusDetection.PIT_SPEED_THRESHOLD,
            'data_timeout_seconds': config.StatusDetection.DATA_TIMEOUT_SECONDS,
            'status_window_seconds': config.StatusDetection.STATUS_WINDOW_SECONDS,
            'position_variance_threshold': config.StatusDetection.POSITION_VARIANCE_THRESHOLD
        }
    
    def determine_car_status(self, car_data, current_time):
        """Determine car status based on telemetry data"""
        df = car_data['data']
        
        # Get recent data within time window
        window_seconds = self.status_config['status_window_seconds']
        start_window = current_time - timedelta(seconds=window_seconds)
        recent_data = df[(df['timeStamp'] >= start_window) & (df['timeStamp'] <= current_time)]
        
        if len(recent_data) == 0:
            return "OUT"  # No recent data = car retired
        
        # Get current and recent speeds
        current_speed = recent_data['speed'].iloc[-1] if len(recent_data) > 0 else 0
        avg_speed = recent_data['speed'].mean()
        max_speed = recent_data['speed'].max()
        
        # Check data continuity
        last_data_time = df['timeStamp'].max()
        time_since_last_data = (current_time - last_data_time).total_seconds()
        
        if time_since_last_data > self.status_config['data_timeout_seconds']:
            return "OUT"
        
        # Position variance check for stopped detection
        if len(recent_data) > 3:
            x_variance = recent_data['x'].var()
            y_variance = recent_data['y'].var()
            position_variance = x_variance + y_variance
            
            if position_variance < self.status_config['position_variance_threshold']:
                if avg_speed < self.status_config['stopped_speed_threshold']:
                    return "STOPPED"
        
        # Speed-based status determination
        if current_speed < self.status_config['stopped_speed_threshold']:
            if max_speed < 10:  # Very low max speed in window
                return "STOPPED"
            else:
                return "PIT"  # Some movement but generally slow
        elif avg_speed < self.status_config['pit_speed_threshold']:
            return "PIT"  # Consistent low speed suggests pit lane
        else:
            return "RUNNING"
    
    def get_status_details(self, car_data, current_time):
        """Get detailed status information for a car"""
        status = self.determine_car_status(car_data, current_time)
        df = car_data['data']
        
        # Get recent data for analysis
        window_seconds = self.status_config['status_window_seconds']
        start_window = current_time - timedelta(seconds=window_seconds)
        recent_data = df[(df['timeStamp'] >= start_window) & (df['timeStamp'] <= current_time)]
        
        if len(recent_data) == 0:
            return {
                'status': status,
                'confidence': 'high',
                'reason': 'No recent data available',
                'last_seen': df['timeStamp'].max() if len(df) > 0 else None
            }
        
        # Calculate confidence and reason
        current_speed = recent_data['speed'].iloc[-1] if len(recent_data) > 0 else 0
        avg_speed = recent_data['speed'].mean()
        speed_variance = recent_data['speed'].var()
        
        confidence = 'medium'
        reason = f"Based on current speed: {current_speed:.1f} km/h, avg: {avg_speed:.1f} km/h"
        
        # High confidence conditions
        if status == "OUT" and len(recent_data) == 0:
            confidence = 'high'
            reason = "No data in recent time window"
        elif status == "STOPPED" and current_speed < 1 and avg_speed < 1:
            confidence = 'high'
            reason = "Consistently very low speed"
        elif status == "RUNNING" and current_speed > 60 and avg_speed > 50:
            confidence = 'high'
            reason = "Consistently high racing speed"
        
        # Low confidence conditions
        if speed_variance > 100:  # High speed variance
            confidence = 'low'
            reason += ", but highly variable speed patterns"
        
        return {
            'status': status,
            'confidence': confidence,
            'reason': reason,
            'current_speed': float(current_speed),
            'avg_speed': float(avg_speed),
            'speed_variance': float(speed_variance),
            'data_points': len(recent_data),
            'last_seen': recent_data['timeStamp'].max() if len(recent_data) > 0 else None
        }
