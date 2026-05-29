# Underwater Vehicle Telemetry Dashboard

## Live Links & Demo
- **Live Deployment**: [Streamlit App](https://ground-station-telemetry-dashboard-g9jqbmumxk5ajwlojrugrb.streamlit.app/#communication-health)
- **Video Demo**: [Google Drive](https://drive.google.com/file/d/1QgE5Wbsdt5AfUm6QNdRXLikeCii_aaRe/view?usp=sharing)

## Overview
This project provides a robust, professional Streamlit dashboard to monitor underwater vehicle telemetry, track spatial trajectories, and synchronize telemetry records with periodic camera imagery.

## Features
- **Real-Time Data Parsing**: Automatically filters and interpolates missing telemetry elements, maintaining application stability.
- **Mission Profiling**: Calculates Haversine distance tracking and evaluates communication network performance.
- **High-Fidelity 3D Virtual Environment**: Reconstructs vehicle location mapping in 3D using Cesium JS with integrated World Terrain Providers.
- **Google Maps 2D Mode**: Integrates folium for 2D map projections via Google Map Standard/Satellite layers.
- **Synchronization**: Employs pandas `merge_asof` to align loose image capture triggers with streaming GPS feeds.
- **Responsive UI**: Professional Google-styled UI with zero emojis, custom CSS typography, and clean statistics.

## Setup and Execution
1. Create a virtual environment:
```
python -m venv venv
source venv/bin/activate
```
2. Install dependencies:
```
pip install streamlit pandas numpy folium streamlit-folium python-dotenv
```
3. Add API tokens (create `.env`):
```
CESIUM_ION_TOKEN=your_token_here
```
4. Run:
```
streamlit run app.py
```
