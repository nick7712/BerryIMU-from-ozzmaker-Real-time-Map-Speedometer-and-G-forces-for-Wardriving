import time
import sys
import os
import csv
import math
from gps import gps, WATCH_ENABLE, WATCH_NEWSTYLE
import IMU

LOG_FILE = "telemetry_log.csv"
file_exists = os.path.isfile(LOG_FILE)

with open(LOG_FILE, mode='a', newline='') as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(["Timestamp", "Latitude", "Longitude", "GPS_Time", "Acc_X_Angle", "Acc_Y_Angle"])

IMU.detectIMU()
if IMU.BerryIMUversion == 99:
    print("Error: No BerryIMU hardware detected... exiting.")
    sys.exit()
IMU.initIMU()

try:
    gps_client = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
except Exception as e:
    print(f"Error: Could not connect to gpsd background socket: {e}")
    sys.exit()

print(f"Telemetry logging started! Writing data live to: {LOG_FILE}")

try:
    while True:
        gps_client.next()
        lat, lon, gps_time = "Searching...", "Searching...", "N/A"
        
        if hasattr(gps_client, 'fix') and gps_client.fix.mode >= 2:
            lat = getattr(gps_client.fix, 'latitude', "Searching...")
            lon = getattr(gps_client.fix, 'longitude', "Searching...")
            gps_time = getattr(gps_client, 'utc', "N/A")

        ACCx = IMU.readACCx()
        ACCy = IMU.readACCy()
        ACCz = IMU.readACCz()

        acc_x_angle = (math.atan2(ACCy, ACCz) * 180) / math.pi
        acc_y_angle = (math.atan2(ACCz, ACCx) * 180) / math.pi
        
        if acc_y_angle > 90:
            acc_y_angle -= 270
        else:
            acc_y_angle += 90

        current_time = time.strftime("%H:%M:%S")
        print(f"[{current_time}] GPS: {lat}, {lon} | IMU Tilt: X={acc_x_angle:.2f}°, Y={acc_y_angle:.2f}°")

        with open(LOG_FILE, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([time.time(), lat, lon, gps_time, f"{acc_x_angle:.2f}", f"{acc_y_angle:.2f}"])

        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nLogging stopped successfully.")
