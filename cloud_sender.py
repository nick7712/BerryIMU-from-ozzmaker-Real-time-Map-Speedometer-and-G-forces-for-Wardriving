import time
import math
import requests
import IMU
from gps import gps, WATCH_ENABLE, WATCH_NEWSTYLE

# 1. CONNECTIVITY SCHEME
AWS_DOMAIN = "mypiprojects.com"
CLOUD_URL = f"http://{AWS_DOMAIN}:8060/api/telemetry"
SECRET_API_TOKEN = "my_private_pi_upload_token_99"

# 2. COMMENCE HARDWARE PIPELINES
try:
    IMU.detectIMU()
    IMU.initIMU()
except Exception:
    print("IMU Hardware initialization skipped or missing.")

gps_client = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)

# Persistent tracking arrays
satellites_locked = 0
lat, lon = 43.54, -96.67
speed_mph = 0.0

print(f"10DOF Core Telemetry Engine Engaged! Broadcasting to {CLOUD_URL}...")

while True:
    # A. Process GPS Sentences if waiting
    if gps_client.waiting(timeout=0.01):
        try:
            gps_client.next()
            if 'satellites' in gps_client.data:
                sats_list = gps_client.data.get('satellites', [])
                satellites_locked = len([s for s in sats_list if s.get('used', False)])
            if hasattr(gps_client, 'fix') and getattr(gps_client.fix, 'mode', 0) >= 2:
                get_lat = getattr(gps_client.fix, 'latitude', 0)
                get_lon = getattr(gps_client.fix, 'longitude', 0)
                get_speed = getattr(gps_client.fix, 'speed', 0)
                if not math.isnan(get_lat) and get_lat != 0:
                    lat, lon = get_lat, get_lon
                if not math.isnan(get_speed):
                    raw_speed = get_speed * 2.23694
                    speed_mph = raw_speed if raw_speed >= 2.0 else 0.0
        except Exception:
            pass

    # B. Initialize all variables with default fallbacks
    g_long = 0.0
    g_lat = 0.0
    pitch = 0.0
    roll = 0.0
    heading = 0.0
    pressure_hpa = 1013.25
    altitude_ft = 0.0
    temp_f = 72.0

    # C. Read all extra IMU sensors inside a giant bulletproof safety shield
    try:
        # Capture Accelerometer Force Values
        ACCx = IMU.readACCx()
        ACCy = IMU.readACCy()
        ACCz = IMU.readACCz()
        g_long = (ACCy * 0.000244) - 0.07  # Calibrated offset axis
        g_lat = ACCx * 0.000244
        if abs(g_long) < 0.03: g_long = 0.0
        if abs(g_lat) < 0.03: g_lat = 0.0

        # Calculate Pitch & Roll
        pitch = math.atan2(ACCx, math.sqrt(ACCy*ACCy + ACCz*ACCz)) * 57.29578
        roll = math.atan2(ACCy, math.sqrt(ACCx*ACCx + ACCz*ACCz)) * 57.29578

        # Capture Magnetometer Headings
        MAGx = IMU.readMAGx()
        MAGy = IMU.readMAGy()
        heading = math.atan2(MAGy, MAGx) * 57.29578
        if heading < 0:
            heading += 360.0

        # Capture Pressure and Temp registers if available
        if hasattr(IMU, 'readPRESSURE'):
            pressure_hpa = IMU.readPRESSURE()
            altitude_ft = (1 - (pressure_hpa / 1013.25) ** 0.190284) * 145366.45
        if hasattr(IMU, 'readTEMP'):
            temp_f = (IMU.readTEMP() * 9/5) + 32
    except Exception:
        pass  # If any specific sensor library calls fail, do not crash! Keep moving.

    # D. SHIP WORKING DATAFRAME PAYLOAD PACKET UP TO AWS
    payload = {
        "speed": speed_mph, "lat": lat, "lon": lon, "sats": satellites_locked,
        "g_long": g_long, "g_lat": g_lat,
        "pitch": pitch, "roll": roll, "compass": heading,
        "pressure": pressure_hpa, "altitude": altitude_ft, "temp": temp_f
    }
    
    headers = {"Authorization": f"Bearer {SECRET_API_TOKEN}"}
    try:
        requests.post(CLOUD_URL, json=payload, headers=headers, timeout=0.1)
    except Exception:
        pass

    time.sleep(0.2)  # 5Hz telemetry cycle refresh frame rate
