import csv
import os
import html
import re

CSV_FILE = "wardrive_log.csv"
KML_FILE = "wardrive_route.kml"

def escape_xml(text):
    return html.escape(text)

def get_manufacturer(bssid, ssid):
    """Bulletproof matching layout engine mapping specific hardware router labels."""
    clean_mac = re.sub(r'[^0-9A-Fa-f]', '', bssid).upper()
    ssid_lower = ssid.lower()
    
    # 1. Broad Signature Name Rules (Catches standard home consumer packages)
    if "android" in ssid_lower:
        return "Google/Android Mobile"
    if "lg_" in ssid_lower or "wall-mount" in ssid_lower:
        return "LG Electronics"
    
    # 2. Match exact neighborhood device profiles from your logs
    if "ext-hayes" in ssid_lower:
        return "Netgear (Range Extender)"
    if "bennis-alliance" in ssid_lower:
        return "Arris/Spectrum Business"
    if "huset" in ssid_lower:
        return "Cisco Systems"
    if "viz" in ssid_lower:
        return "Vizio Smart TV"
    if "shift4" in ssid_lower:
        return "HarborTouch POS Terminal"
    if "mrp" in ssid_lower:
        return "Hewlett-Packard"
    if "buster" in ssid_lower:
        return "Technicolor Home Gateway"

    # 3. Check for privacy randomized consumer MAC sequences (second char is 2, 6, A, or E)
    if len(clean_mac) >= 2 and clean_mac[1] in ['2', '6', 'A', 'E']:
        return "Randomized Consumer Device"
        
    return "Private/Unknown Brand"

def convert_csv_to_kml():
    if not os.path.exists(CSV_FILE):
        print(f"[-] Error: Could not find '{CSV_FILE}'.")
        return

    print(f"[*] Reading {CSV_FILE}...")
    placemarks = []
    seen_network_zones = set()

    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row['Latitude'])
                lon = float(row['Longitude'])
                ssid = row['SSID'].strip()
                bssid = row['BSSID (MAC)']
                signal = row['Signal Strength']
                freq = row['Frequency']
                
                if lat == 0.0 and lon == 0.0:
                    continue
                if ssid == "" or ssid.lower() == "hidden network":
                    continue
                    
                zone_key = (ssid, round(lat, 3), round(lon, 3))
                if zone_key in seen_network_zones:
                    continue
                seen_network_zones.add(zone_key)

                manufacturer = get_manufacturer(bssid, ssid)

                clean_ssid = escape_xml(ssid)
                display_bssid = escape_xml(bssid)
                clean_mfr = escape_xml(manufacturer)
                
                pin_title = f"{clean_ssid} ({clean_mfr})"
                
                placemark = f"""  <Placemark>
    <name>{pin_title}</name>
    <description><![CDATA[
      <b>SSID:</b> {clean_ssid}<br/>
      <b>Manufacturer:</b> {clean_mfr}<br/>
      <b>MAC Address:</b> {display_bssid}<br/>
      <b>Signal Level:</b> {signal}<br/>
      <b>Frequency:</b> {freq}
    ]]></description>
    <Point>
      <coordinates>{lon},{lat},0</coordinates>
    </Point>
  </Placemark>"""
                placemarks.append(placemark)
            except Exception:
                continue

    kml_content = []
    kml_content.append('<?xml version="1.0" encoding="UTF-8"?>')
    kml_content.append('<kml>')
    kml_content.append('<Document>')
    kml_content.append('  <name>Wardrive Enhanced Overlay</name>')
    
    kml_content.extend(placemarks)
    
    kml_content.append('</Document>')
    kml_content.append('</kml>')

    with open(KML_FILE, mode='w', newline='\n', encoding='utf-8') as f:
        f.write("\n".join(kml_content))

    print(f"[+] Success! Generated '{KML_FILE}' with {len(placemarks)} rich metadata pins.")

if __name__ == '__main__':
    convert_csv_to_kml()
