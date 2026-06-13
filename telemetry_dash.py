import dash
from dash import html, dcc, callback
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import math
from gps import gps, WATCH_ENABLE, WATCH_NEWSTYLE
import IMU

# Initialize OzzMaker IMU hardware
IMU.detectIMU()
IMU.initIMU()

# Initialize background network GPS stream connection
gps_client = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)

# Setup Dash Web Application with Mobile Viewport Scaler Enabled
app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}]
)

app.layout = html.Div([
    html.H1("Live Telemetry Tracker", style={
        'textAlign': 'center', 
        'fontFamily': 'sans-serif', 
        'fontSize': '28px',
        'margin': '10px 0'
    }),
    
    # MOBILE OPTIMIZED CARD GRID: Uses flex-wrap to stack cleanly on tiny phone screens
    html.Div([
        # Speed Card
        html.Div([
            html.H2("00.0", id='live-speed-text', style={'fontSize': '38px', 'margin': '0', 'color': '#2196F3'}),
            html.P("SPEED (MPH)", style={'margin': '0', 'fontSize': '12px', 'fontWeight': 'bold', 'color': '#555'})
        ], style={'flex': '1 1 200px', 'textAlign': 'center', 'backgroundColor': '#E3F2FD', 'padding': '15px', 'borderRadius': '10px'}),
        
        # Longitudinal G Card
        html.Div([
            html.H2("0.00 G", id='live-gforce-text', style={'fontSize': '38px', 'margin': '0', 'color': '#4CAF50'}),
            html.P("LONGITUDINAL G", style={'margin': '0', 'fontSize': '12px', 'fontWeight': 'bold', 'color': '#555'})
        ], style={'flex': '1 1 200px', 'textAlign': 'center', 'backgroundColor': '#E8F5E9', 'padding': '15px', 'borderRadius': '10px'}),
        
        # Lateral G Card
        html.Div([
            html.H2("0.00 G", id='live-latg-text', style={'fontSize': '38px', 'margin': '0', 'color': '#E91E63'}),
            html.P("LATERAL G (CORNER)", style={'margin': '0', 'fontSize': '12px', 'fontWeight': 'bold', 'color': '#555'})
        ], style={'flex': '1 1 200px', 'textAlign': 'center', 'backgroundColor': '#FCE4EC', 'padding': '15px', 'borderRadius': '10px'}),

        # Satellite Lock Count Card
        html.Div([
            html.H2("0 Sats", id='live-sat-text', style={'fontSize': '38px', 'margin': '0', 'color': '#FF9800'}),
            html.P("GPS SATELLITES", style={'margin': '0', 'fontSize': '12px', 'fontWeight': 'bold', 'color': '#555'})
        ], style={'flex': '1 1 200px', 'textAlign': 'center', 'backgroundColor': '#FFF3E0', 'padding': '15px', 'borderRadius': '10px'})
    ], style={
        'display': 'flex', 
        'flexWrap': 'wrap', 
        'gap': '10px', 
        'justifyContent': 'center', 
        'marginBottom': '15px'
    }),

    # MAP POSITION PANEL
    html.Div([
        html.Div([
            html.H3("Position Tracker", style={'textAlign': 'center', 'margin': '5px 0', 'fontSize': '16px'}),
            dcc.Graph(id='live-map-graph', style={'height': '450px'})
        ], style={'flex': '1 1 100%', 'padding': '5px', 'backgroundColor': '#fff', 'borderRadius': '10px'})
    ], style={
        'display': 'flex', 
        'flexWrap': 'wrap', 
        'gap': '15px', 
        'justifyContent': 'center'
    }),

    dcc.Interval(id='interval-component', interval=200, n_intervals=0)
], style={'backgroundColor': '#F9F9F9', 'padding': '10px', 'fontFamily': 'sans-serif'})

# Global fallbacks to keep page loading even if GPS is waiting
last_known_sats = 0
lat, lon = 43.54, -96.67
speed_mph = 0.0

# ------------------------------------------------------------------------------
@callback(
    [Output('live-map-graph', 'figure'),
     Output('live-speed-text', 'children'),
     Output('live-gforce-text', 'children'),
     Output('live-latg-text', 'children'),    
     Output('live-sat-text', 'children')],     
    [Input('interval-component', 'n_intervals')]
)
def update_telemetry_dashboard(n):
    global last_known_sats, lat, lon, speed_mph
    
    if gps_client.waiting(timeout=0.02):
        try:
            packet = gps_client.next()
            if packet and 'satellites' in gps_client.data:
                sats_list = gps_client.data.get('satellites', [])
                last_known_sats = len([s for s in sats_list if s.get('used', False)])
                
            if hasattr(gps_client, 'fix') and getattr(gps_client.fix, 'mode', 0) >= 2:
                get_lat = getattr(gps_client.fix, 'latitude', 0)
                get_lon = getattr(gps_client.fix, 'longitude', 0)
                get_speed = getattr(gps_client.fix, 'speed', 0)

                if not math.isnan(get_lat) and not math.isnan(get_lon) and get_lat != 0:
                    lat = get_lat
                    lon = get_lon
                if not math.isnan(get_speed):
                    raw_speed_mph = get_speed * 2.23694
                    speed_mph = raw_speed_mph if raw_speed_mph >= 3.0 else 0.0
        except Exception:
            pass

    map_zoom = 15 if last_known_sats > 0 else 2
    map_text = f"Live Position ({last_known_sats} Sats)" if last_known_sats > 0 else "Acquiring..."
    marker_color = 'blue' if last_known_sats > 0 else 'red'

    ACCx = IMU.readACCx()
    ACCy = IMU.readACCy()

    g_force_y = (ACCy * 0.000244) - 0.07 
    g_force_x = ACCx * 0.000244

    if abs(g_force_y) < 0.03: g_force_y = 0.0
    if abs(g_force_x) < 0.03: g_force_x = 0.0

    map_fig = go.Figure(go.Scattermap(lat=[lat], lon=[lon], mode='markers+text', marker=go.scattermap.Marker(size=14, color=marker_color), text=[map_text], textposition="top center"))
    map_fig.update_layout(map=dict(style="open-street-map", center=dict(lat=lat, lon=lon), zoom=map_zoom), margin=dict(l=0, r=0, t=0, b=0))

    return map_fig, f"{speed_mph:.1f}", f"{g_force_y:+.2f} G", f"{g_force_x:+.2f} G", f"{last_known_sats} Sats"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8060, debug=False, threaded=True)
