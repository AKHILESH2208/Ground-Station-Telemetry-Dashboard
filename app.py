import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import os
import json
import base64
import streamlit.components.v1 as components
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# PAGE CONFIGURATION
st.set_page_config(
    layout="wide", 
    page_title="Ground Station Dashboard"
)

# CUSTOM CSS FOR PROFESSIONAL LOOK
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', Arial, sans-serif;
    }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #dadce0;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
    }
    .block-container {
        padding-top: 1.5rem;
    }
    h1, h2, h3 {
        color: #202124 !important;
        font-weight: 400;
    }
    [data-testid="stSidebar"] {
        box-shadow: 2px 0 8px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
# DATA LOADING AND PROCESSING
# ------------------------------------------------------------------ #

@st.cache_data
def load_data():
    try:
        telemetry = pd.read_csv("dataset/telemetry.csv")
        images = pd.read_csv("dataset/image_timestamps.csv")
        
        telemetry['timestamp'] = pd.to_datetime(telemetry['timestamp'])
        images['timestamp'] = pd.to_datetime(images['timestamp'])
        
        telemetry = telemetry.dropna(subset=['lat', 'lon', 'timestamp'])
        telemetry = telemetry.sort_values("timestamp").reset_index(drop=True)
        
        if 'speed' in telemetry.columns:
            telemetry['speed'] = telemetry['speed'].fillna(0.0)
        if 'battery' in telemetry.columns:
            telemetry['battery'] = telemetry['battery'].ffill().fillna(100.0)
        if 'signal_strength' in telemetry.columns:
            telemetry['signal_strength'] = telemetry['signal_strength'].ffill().fillna(-100.0)
            
        return telemetry, images
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        return pd.DataFrame(), pd.DataFrame()
    
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

telemetry_df, images_df = load_data()

if telemetry_df.empty or images_df.empty:
    st.stop()

telemetry_df['distance_km'] = calculate_distance(
    telemetry_df['lat'].shift(), telemetry_df['lon'].shift(),
    telemetry_df['lat'], telemetry_df['lon']
).fillna(0)

total_distance = telemetry_df['distance_km'].sum()
avg_speed = telemetry_df['speed'].mean()
max_speed = telemetry_df['speed'].max()
mission_duration = telemetry_df['timestamp'].max() - telemetry_df['timestamp'].min()

expected_packets = telemetry_df['packet_id'].max() - telemetry_df['packet_id'].min() + 1
received_packets = telemetry_df['packet_id'].nunique()
missing_packets = expected_packets - received_packets
packet_loss_pct = (missing_packets / expected_packets) * 100 if expected_packets > 0 else 0
health_status = "OPTIMAL" if packet_loss_pct < 5 else "WARNING" if packet_loss_pct < 15 else "CRITICAL"

images_df = images_df.sort_values("timestamp")
telemetry_df = telemetry_df.sort_values("timestamp")
synced_df = pd.merge_asof(
    images_df, telemetry_df,
    on="timestamp",
    direction="nearest"
)

# ------------------------------------------------------------------ #
# APP LAYOUT & SIDEBAR
# ------------------------------------------------------------------ #

st.sidebar.title("Ground Control Station")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["Overview", "Telemetry Map", "Data Logs & Validation"])

st.sidebar.markdown("### Live Status")
current_state = telemetry_df.iloc[-1]
st.sidebar.metric("Battery Level", f"{current_state['battery']}%")
battery_val = max(0.0, min(1.0, current_state['battery'] / 100.0))
st.sidebar.progress(battery_val)

st.sidebar.metric("Signal Strength", f"{current_state['signal_strength']} dBm")
st.sidebar.metric("Current Speed", f"{current_state['speed']} m/s")

# ------------------------------------------------------------------ #
# PAGE: OVERVIEW
# ------------------------------------------------------------------ #
if page == "Overview":
    st.title("Mission Overview")
    st.markdown("Real-time aggregated analytics and status for the underwater vehicle.")
    
    st.markdown("### Flight Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Distance", f"{total_distance*1000:.1f} m", delta="Completed")
    with col2:
         tot_sec = int(mission_duration.total_seconds())
         hours, remainder = divmod(tot_sec, 3600)
         minutes, seconds = divmod(remainder, 60)
         if hours > 0:
             dur_str = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
         else:
             dur_str = f"{minutes:02d}m {seconds:02d}s"
         st.metric("Mission Duration", dur_str)
    with col3:
        st.metric("Average Speed", f"{avg_speed:.2f} m/s")
    with col4:
        st.metric("Maximum Speed", f"{max_speed:.2f} m/s")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### Communication Health")
    col5, col6, col7, col8 = st.columns(4)
    
    health_color = "normal" if health_status == "OPTIMAL" else "off" if health_status == "WARNING" else "inverse"
    with col5:
        st.metric("System Health", health_status, delta="Stable" if health_status == "OPTIMAL" else "Check Links", delta_color=health_color)
    with col6:
        st.metric("Packets Received", received_packets)
    with col7:
        st.metric("Packets Missing", missing_packets, delta=f"-{missing_packets}" if missing_packets > 0 else None, delta_color="inverse")
    with col8:
        st.metric("Packet Loss Rate", f"{packet_loss_pct:.2f}%", delta=f"{packet_loss_pct:.2f}%" if packet_loss_pct > 0 else None, delta_color="inverse")

# ------------------------------------------------------------------ #
# PAGE: TELEMETRY MAP
# ------------------------------------------------------------------ #
elif page == "Telemetry Map":
    st.title("Interactive Telemetry Tracker")
    st.markdown("Visualize the vehicle trajectory, pinpoint camera shots, and inspect spatial data in 2D or 3D.")

    map_view = st.radio("Select Map Engine:", ["3D Map (Cesium)", "2D Map (Folium)"], horizontal=True)

    if map_view == "2D Map (Folium)":
        center_lat = telemetry_df['lat'].mean()
        center_lon = telemetry_df['lon'].mean()
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=18, tiles=None)
        folium.TileLayer(
            tiles='http://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Maps (Standard)',
            max_zoom=20
        ).add_to(m)
        folium.TileLayer(
            tiles='http://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Maps (Satellite)',
            max_zoom=20
        ).add_to(m)
        folium.LayerControl().add_to(m)
        
        points = list(zip(telemetry_df['lat'], telemetry_df['lon']))
        folium.PolyLine(points, color="#1a73e8", weight=6, opacity=0.9, tooltip="Vehicle Trajectory").add_to(m)
        
        folium.Marker(points[0], popup="Start").add_to(m)
        folium.Marker(points[-1], popup="End").add_to(m)
        
        for _, row in synced_df.iterrows():
            html_popup = f"""
            <div style="font-family: Arial; font-size: 12px;">
                <b>Image:</b> {row['image_name']}<br>
                <b>Time:</b> {row['timestamp'].strftime('%H:%M:%S')}<br>
                <b>Depth:</b> {row['altitude']}m<br>
                <b>Speed:</b> {row['speed']} m/s
            </div>
            """
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=6,
                color="#FF9900",
                fill=True,
                fill_color="#FF9900",
                fill_opacity=0.9,
                popup=folium.Popup(html_popup, max_width=250),
                tooltip=f"{row['image_name']}"
            ).add_to(m)

        st_map = st_folium(m, width=1200, height=500)

    else:
        cesium_token = os.getenv("CESIUM_ION_TOKEN", "")
        if not cesium_token:
            st.info("Tip: Add CESIUM_ION_TOKEN=your_token to the .env file to enable high-res 3D satellite tiles.")

        path_coords = []
        for _, row in telemetry_df.iterrows():
            path_coords.extend([row['lon'], row['lat'], row['altitude']])
        
        markers_js = ""
        for _, row in synced_df.iterrows():
            image_path = os.path.join("dataset/frames", row['image_name'])
            img_data_uri = ""
            if os.path.exists(image_path):
                with open(image_path, "rb") as img_file:
                    img_b64 = base64.b64encode(img_file.read()).decode('utf-8')
                    img_data_uri = f"data:image/jpeg;base64,{img_b64}"

            desc_html = f"""
                <div style="font-family: Arial; padding: 5px; color: white;">
                    <img src="{img_data_uri}" style="width: 100%; border-radius: 5px; margin-bottom: 5px;"/>
                    <b>Timestamp:</b> {row['timestamp'].strftime('%H:%M:%S')}<br>
                    <b>Lat:</b> {row['lat']:.5f}<br>
                    <b>Lon:</b> {row['lon']:.5f}<br>
                    <b>Depth:</b> {row['altitude']} m<br>
                    <b>Speed:</b> {row['speed']} m/s
                </div>
            """.replace("\n", "")

            markers_js += f"""
            viewer.entities.add({{
                name: 'Marker for {row['image_name']}',
                position: Cesium.Cartesian3.fromDegrees({row['lon']}, {row['lat']}, {row['altitude']}),
                point: {{
                    pixelSize: 12,
                    color: Cesium.Color.ORANGE,
                    outlineColor: Cesium.Color.WHITE,
                    outlineWidth: 2,
                    heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
                }},
                label: {{
                    text: 'IMG: {row['image_name']}',
                    font: '14pt sans-serif',
                    style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                    outlineWidth: 2,
                    verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                    pixelOffset: new Cesium.Cartesian2(0, -15),
                    heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
                }},
                description: '{desc_html}'
            }});
            """

        cesium_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <script>window.CESIUM_BASE_URL = 'https://unpkg.com/cesium@1.95.0/Build/Cesium/';</script>
          <script src="https://unpkg.com/cesium@1.95.0/Build/Cesium/Cesium.js"></script>
          <link href="https://unpkg.com/cesium@1.95.0/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
        </head>
        <body style="margin: 0; padding: 0; overflow: hidden; background: #000;">
          <div id="cesiumContainer" style="width: 100vw; height: 100vh; border-radius: 8px;"></div>
          <script>
            // Streamlit iframes block Web Workers via blob CORS. Disable them so Cesium renders on the main thread safely.
            if (Cesium.FeatureDetection) {{
                Cesium.FeatureDetection.supportsWebWorkers = function() {{ return false; }};
            }}

            (async function() {{
                const userToken = "{cesium_token}";
                if (userToken) {{
                    Cesium.Ion.defaultAccessToken = userToken;
                }}

                let activeTerrainProvider;
                if (userToken) {{
                    try {{
                        activeTerrainProvider = Cesium.createWorldTerrain();
                    }} catch (e) {{
                        console.log("Terrain error:", e);
                    }}
                }}

                let activeImageryProvider;
                if (!userToken) {{
                    activeImageryProvider = new Cesium.TileMapServiceImageryProvider({{
                        url : Cesium.buildModuleUrl('Assets/Textures/NaturalEarthII')
                    }});
                }}

                const viewer = new Cesium.Viewer('cesiumContainer', {{
                    terrainProvider: activeTerrainProvider,
                    baseLayerPicker: false,
                    geocoder: false,
                    animation: false,
                    timeline: false,
                    scene3DOnly: true,
                    infoBox: false,
                    selectionIndicator: false,
                    imageryProvider: activeImageryProvider
                }});

                if (userToken) {{
                    try {{
                        viewer.scene.primitives.add(Cesium.createOsmBuildings());
                    }} catch (e) {{
                        console.log(e);
                    }}
                }}

                const pathPositions = Cesium.Cartesian3.fromDegreesArrayHeights({json.dumps(path_coords)});

                const pathEntity = viewer.entities.add({{
                    name: 'Vehicle Path',
                    polyline: {{
                        positions: pathPositions,
                        width: 5,
                        clampToGround: true,
                        material: Cesium.Color.CYAN
                    }}
                }});

                {markers_js}

                viewer.zoomTo(viewer.entities);
            }})();
          </script>
        </body>
        </html>
        """

        components.html(cesium_html, height=700)

    st.markdown("---")
    st.markdown("### Camera Inspection")
    
    selected_img = st.selectbox("Select a camera frame to inspect environment & telemetry:", synced_df['image_name'])
    
    if selected_img:
        selected_data = synced_df[synced_df['image_name'] == selected_img].iloc[0]
        col_img, col_data = st.columns([1.5, 1])
        
        with col_img:
            image_path = os.path.join("dataset/frames", selected_data['image_name'])
            if os.path.exists(image_path):
                st.image(image_path, caption=f"Frame: {selected_data['image_name']}", width="stretch")
            else:
                st.warning(f"File not found: {image_path}")
                
        with col_data:
            st.markdown("#### Point State Data")
            st.markdown(f"**Timestamp:** `{selected_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}`")
            st.markdown(f"**GPS:** `{selected_data['lat']:.6f}, {selected_data['lon']:.6f}`")
            st.markdown(f"**Depth (Alt):** `{selected_data['altitude']} m`")
            st.markdown(f"**Speed:** `{selected_data['speed']} m/s`")
            st.markdown(f"**Heading:** `{selected_data['heading']}°`")
            st.markdown(f"**Battery:** `{selected_data['battery']}%`")
            st.markdown(f"**Signal:** `{selected_data['signal_strength']} dBm`")


# ------------------------------------------------------------------ #
# PAGE: DATA LOGS & VALIDATION
# ------------------------------------------------------------------ #
elif page == "Data Logs & Validation":
    st.title("Raw Telemetry & Synchronization Logs")
    st.markdown("Verify the raw synchronization outputs between the camera frames and the telemetry feed.")
    
    display_sync_df = synced_df[['image_name', 'timestamp', 'lat', 'lon', 'altitude', 'speed', 'battery']].copy()
    display_sync_df['timestamp'] = display_sync_df['timestamp'].dt.strftime('%H:%M:%S')
    display_sync_df.rename(columns={'altitude': 'Depth (m)', 'speed': 'Speed (m/s)', 'battery': 'Battery (%)', 'lat': 'Latitude', 'lon': 'Longitude', 'image_name': 'Image Name'}, inplace=True)
    
    st.dataframe(display_sync_df, width="stretch", hide_index=True)
    
    st.markdown("### Full Telemetry Dump")
    with st.expander("Expand to view raw vehicle telemetry"):
        st.dataframe(telemetry_df, width="stretch")
