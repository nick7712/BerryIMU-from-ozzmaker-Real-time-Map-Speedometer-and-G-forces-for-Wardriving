# Real-Time Car Telemetry Dashboard & Wi-Fi Wardrive Tracker

A custom, automated telemetry platform built for the Raspberry Pi 4 that bridges hardware sensor arrays with a responsive web browser interface. This project splits processing loads into two independent tracks: a multi-threaded live sensor dashboard and a background wireless network scanner.

## 🚀 Features

*   **Live Web Dashboard (5Hz refresh)**: Built using Plotly Dash to serve local network devices without an internet dependency.
    *   **GPS Speedometer**: Translates raw GNSS satellite data streams into digital MPH values, featuring an intelligent speed threshold filter to eliminate stationary GPS drift.
    *   **Longitudinal G-Force Meter**: Translates raw I2C accelerometer data from the BerryIMU into standard Earth G-forces, filtered against minor idle noise vibrations.
    *   **3D Board Orientation Matrix**: Applies real-time Euler rotation matrix trigonometry to accelerometer structures, rendering a live 3D mesh block that reacts instantly to vehicle hills, tilt, and cornering pitch/roll.
    *   **Geographic Map View**: Incorporates an automated fallback mode that gracefully displays satellite searching statuses without crashing the browser layout engine.
*   **Independent Wardrive Logging Engine**: Sweeps the surrounding airwaves using native Linux wireless network utility layers (`iwlist`) and logs nearby SSIDs, MAC addresses (BSSIDs), signal strengths (dBm), and precise geographic coordinates into an Excel-compatible CSV file.
*   **Smart Map Overlay Converter**: A post-processing script that translates raw wardrive spreadsheets into a standard KML map overlay for Google Earth/Google My Maps. It utilizes an advanced network name (SSID) and regional proximity filter to completely eliminate crowded duplicate pins from multi-frequency routers (2.4GHz/5GHz/Guest networks) on your driveway or street.
*   **Fully Automated Startup**: Seamlessly runs the core telemetry server on system boot using localized startup tables and task managers (`rc.local` and `cron`), auto-repairing background serial sockets if the device experiences an unexpected power loss or dead battery.

## 🛠️ Hardware Requirements

*   **Processor**: Raspberry Pi 4 Model B
*   **IMU Sensor**: OzzMaker BerryIMU (LSM9DS1/LSM6DSL Accelerometer & Gyroscope) via I2C interface
*   **GPS Module**: NMEA-compliant USB or GPIO Serial GNSS Receiver managed by the `gpsd` daemon

## 📦 Project File Mapping

*   `telemetry_dash.py` - Core Plotly Dash application server. Runs automatically on system startup.
*   `wifilogger.py` - Standalone wireless network scanning utility. Run manually to map routers.
*   `log_to_kml.py` - Data parsing script that generates clean, deduplicated map overlays.
*   `IMU.py` / `LSM9DS1.py` - Hardware driver interaction layers for the OzzMaker sensor suite.

## 📝 Usage Instructions

### 1. Starting the Wardriving Logger
While the main dashboard serves gauges to your phone or laptop browser automatically, launch the companion wireless logging utility in a second terminal window before heading out on a drive:
```bash
cd ~/BerryIMU/python-BerryIMU-gyro-accel-compass
sudo python3 wifilogger.py
```
Press `Ctrl + C` when you return home to save the spreadsheet safely.

### 2. Generating the Google Earth Overlay
To process your raw `wardrive_log.csv` file into a clean, deduplicated KML file, run the conversion utility:
```bash
python3 log_to_kml.py
```
This produces `wardrive_route.kml`, which can be transferred to a PC via WinSCP and opened natively inside **Google Earth Pro** or imported directly into **Google My Maps**.

---
*Developed as an educational hardware and embedded software telemetry mapping project.*
