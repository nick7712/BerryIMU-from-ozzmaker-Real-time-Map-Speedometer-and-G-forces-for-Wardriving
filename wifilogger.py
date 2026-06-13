import csv
import os
import time
import math
import subprocess
import re
from datetime import datetime
from gps import gps, WATCH_ENABLE, WATCH_NEWSTYLE

# Configuration Settings
LOG_FILE = "wardrive_log.csv"
SCAN_INTERVAL_SECONDS = 5  # Time to pause between sweeps

# Initialize background network GPS stream connection
gps_client = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)

def initialize_csv():
    """Creates the spreadsheet file with proper structural columns if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Latitude", "Longitude", "SSID", "BSSID (MAC)", "Signal Strength", "Frequency"])
        print(f"[+] Initialized brand new spreadsheet log: {LOG_FILE}")

def run_wifi_scan():
    """Uses the Pi's native command line tools to sweep for networks without extra packages."""
    try:
        # Runs the system's low-level wireless scanning utility
        cmd = ["sudo", "iwlist", "wlan0", "scanning"]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[-] Native network scanning utility error: {e}")
        return []

    networks = []
    cells = output.split("Cell ")
    
    for cell in cells[1:]:
        bssid_match = re.search(r"Address:\s*([0-9A-Fa-f:]{17})", cell)
        ssid_match = re.search(r'ESSID:"([^"]*)"', cell)
        signal_match = re.search(r"Quality=[^ ]*\s+Signal level=(-\d+|\d+)", cell)
        freq_match = re.search(r"Frequency:(\d+\.\d+)\s+GHz", cell)

        if ssid_match and bssid_match:
            ssid = ssid_match.group(1) if ssid_match.group(1) != "" else "Hidden Network"
            bssid = bssid_match.group(1)
            signal = signal_match.group(1) + " dBm" if signal_match else "Unknown"
            freq = freq_match.group(1) + " GHz" if freq_match else "Unknown"
            
            networks.append({
                'ssid': ssid,
                'bssid': bssid,
                'signal': signal,
                'freq': freq
            })
    return networks

def scan_and_log():
    initialize_csv()
    print("[*] Starting Wi-Fi Wardrive Scanner Engine...")
    print("[*] Press Ctrl+C at any time to halt scanning.")
    
    while True:
        try:
            gps_client.next()
        except (StopIteration, Exception):
            pass
            
        lat, lon = 0.0, 0.0
        gps_status = "No Fix"
        
        if hasattr(gps_client, 'fix') and getattr(gps_client.fix, 'mode', 0) >= 2:
            get_lat = getattr(gps_client.fix, 'latitude', 0)
            get_lon = getattr(gps_client.fix, 'longitude', 0)
            if not math.isnan(get_lat) and not math.isnan(get_lon):
                lat = get_lat
                lon = get_lon
                gps_status = f"Fix OK ({lat:.5f}, {lon:.5f})"
                
        results = run_wifi_scan()
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M:%S")
        logged_count = 0
        
        if results:
            with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for ap in results:
                    writer.writerow([timestamp, lat, lon, ap['ssid'], ap['bssid'], ap['signal'], ap['freq']])
                    logged_count += 1
                    
        print(f"[{timestamp}] Status: {gps_status} | Captured {logged_count} networks in this sweep.")
        time.sleep(SCAN_INTERVAL_SECONDS)

if __name__ == '__main__':
    try:
        scan_and_log()
    except KeyboardInterrupt:
        print("\n[-] Scan halted cleanly by user. Spreadsheet saved successfully.")
