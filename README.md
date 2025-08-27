# 🏁 F1 Live Timing & Racing Analysis System

A comprehensive real-time Formula 1 racing analysis system with advanced overtaking predictions, distance reset handling, and live timing displays.

## 🚀 Features

### 🎯 **Core Functionality**
- **Real-time live timing** with WebSocket updates
- **Advanced overtaking analysis** with AI predictions
- **Distance reset detection & recovery** system
- **Multi-car comparison** and gap analysis
- **Speed requirement calculations** for overtaking scenarios

### 📊 **Distance Reset Handling System**
Our advanced system handles common telemetry issues:

- ✅ **GPS signal loss** → Speed integration fallback
- ✅ **Sensor resets** → History-based recovery
- ✅ **Data gaps** → Linear interpolation
- ✅ **Invalid coordinates** → GPS validation
- ✅ **Speed anomalies** → Realistic speed limits

### 🔧 **Recovery Methods**
1. **Speed Integration**: Recalculates from last good point using speed data
2. **GPS Recovery**: Uses coordinates when available
3. **Linear Interpolation**: Estimates based on average speed
4. **Fallback**: Uses last known good distance

### 📈 **Real-time Updates**
- Auto-refresh every 3 seconds
- Continuous data updates without hiding previous results
- Visual update indicators
- Timestamp tracking for all updates

## 🛠 Installation & Setup

### Prerequisites
- Python 3.8+
- Virtual environment support

### Quick Start

1. **Clone the repository:**
```bash
git clone git@github.com:SabolSocare/car_racing.git
cd car_racing
```

2. **Set up virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install flask flask-socketio pandas numpy psutil
```

4. **Configure data directory:**
Edit `config.py` and update the data directory path:
```python
class Data:
    BASE_DIR = "/path/to/your/csv/data/files"
```

5. **Run the server:**
```bash
python f1_live_ui.py
```

6. **Open your browser:**
Navigate to `http://localhost:5002`

## 📁 Project Structure

```
F1/
├── core/                          # Core system modules
│   ├── __init__.py
│   ├── timing_engine.py          # Main timing calculations
│   ├── distance_reset_handler.py # Distance reset detection & recovery
│   ├── car_status.py             # Car status detection
│   ├── forecasting.py            # Overtaking predictions
│   └── performance_monitor.py    # Performance monitoring
├── templates/                     # HTML templates
│   ├── control_center.html       # Main control interface
│   ├── f1_live_timing_websocket.html  # Live timing display
│   ├── overtake_analysis.html    # Overtaking analysis dashboard
│   └── *.html
├── static/                        # CSS and static files
│   └── f1_styles.css
├── Truck_Cal/                     # Sample data directory
│   └── cropped_data/             # Processed CSV files
├── config.py                      # System configuration
├── f1_live_ui.py                 # Main Flask application
└── README.md                      # This file
```

## 🎮 Usage

### 🏁 Live Timing
- **URL**: `http://localhost:5002/live-timing`
- Real-time position updates
- Gap calculations between cars
- Speed and status monitoring

### 📊 Overtake Analysis
- **URL**: `http://localhost:5002/overtake-analysis`
- Select chasing and target cars
- Get detailed overtaking scenarios
- Speed requirement calculations
- AI-powered recommendations

### 🎛 Control Center
- **URL**: `http://localhost:5002/`
- Simulation speed control
- Race start/stop/reset
- System monitoring

## 🔧 Configuration

The system is highly configurable through `config.py`:

### Key Configuration Sections:
- **Server Settings**: Port, host, debug mode
- **Data Configuration**: CSV file locations, processing settings
- **Performance**: Update intervals, cache sizes, client limits
- **Distance Reset**: Detection thresholds, recovery priorities
- **Simulation**: Speed ranges, auto-restart settings
- **UI Settings**: Themes, update frequencies, display limits

### Example Configuration:
```python
class Server:
    HOST = '0.0.0.0'
    PORT = 5002
    DEBUG = False

class DistanceReset:
    DROP_THRESHOLD_PERCENT = 80
    SPEED_ANOMALY_THRESHOLD = 150
    RECOVERY_PRIORITIES = {
        'speed_integration': 4,
        'gps_recovery': 3,
        'linear_interpolation': 2,
        'fallback': 1
    }
```

## 📡 API Endpoints

### Core APIs
- `GET /api/timing` - Current race timing data
- `GET /api/trucks` - Available cars/trucks
- `GET /api/start` - Start race simulation
- `GET /api/stop` - Stop race simulation
- `GET /api/reset` - Reset race to start

### Analysis APIs
- `GET /api/available-targets/<car_id>` - Available overtaking targets
- `GET /api/overtake-analysis/<chasing_id>/<target_id>` - Detailed analysis
- `GET /api/speed-requirements/<chasing_id>/<target_id>` - Speed calculations
- `GET /api/car-comparison/<car1_id>/<car2_id>` - Car comparison

### Monitoring APIs
- `GET /api/distance-reset-status` - Distance reset monitoring
- `GET /api/car-distance-status/<car_id>` - Individual car status

## 🎯 Data Format

The system expects CSV files with the following columns:
- `timeStamp` - ISO format timestamp
- `car` - Car/truck ID
- `lat`, `lon` - GPS coordinates (optional)
- `x`, `y` - Local coordinates
- `speed` - Speed in km/h

### Sample Data Format:
```csv
timeStamp,car,lat,lon,x,y,speed
2025-06-07T10:00:00.000Z,8,0.0,0.0,100.5,200.3,45.2
2025-06-07T10:00:01.000Z,8,0.0,0.0,101.2,201.1,46.8
```

## 🚀 Advanced Features

### Distance Reset Recovery
The system automatically detects and recovers from:
- Distance sensor resets (>80% drops)
- Speed anomalies (>150 km/h unrealistic speeds)
- GPS signal loss
- Data continuity issues

### Real-time Analysis
- Continuous overtaking predictions
- Speed trend analysis
- Gap calculations with sub-second precision
- Multi-scenario planning

### Performance Optimization
- Intelligent caching system
- Configurable update intervals
- Client connection limits
- Memory usage monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔍 Troubleshooting

### Common Issues:

**Port already in use:**
```bash
pkill -f f1_live_ui.py && sleep 2
python f1_live_ui.py
```

**No data loading:**
- Check CSV file format
- Verify data directory path in `config.py`
- Ensure files have proper permissions

**WebSocket connection issues:**
- Check firewall settings
- Verify port 5002 is available
- Test with `curl http://localhost:5002/api/timing`

## 📊 Performance Stats

- Supports up to 10 concurrent clients (configurable)
- Updates every 1-3 seconds (configurable)
- Handles 1000+ distance calculations per second
- Memory usage typically <100MB

## 🎖 Credits

Developed with advanced telemetry processing, real-time analysis algorithms, and comprehensive error recovery systems for professional racing analysis.

---

**Happy Racing! 🏁**
