# Ground Station Telemetry Dashboard

This repository contains the software developed for the underwater robotic vehicle Ground Station Telemetry Dashboard assignment.

## Overview

The dashboard is built using [Streamlit](https://streamlit.io/) to provide a highly interactive and easy-to-use web interface that visualizes telemetry data and synchronizes it with camera frames captured during the mission. 

It accomplishes the following tasks:
1. **Telemetry Processing:** Calculates and displays total distance traveled, average speed, max speed, mission duration, missing packets, and communication health.
2. **Camera-Telemetry Synchronization:** Matches image timestamps to the nearest telemetry timestamp using `pandas.merge_asof`.
3. **Ground Station Dashboard:** Displays an interactive map (via Folium) for visualizing the vehicle's trajectory along with camera markers, and enables viewing specific images alongside their synchronized telemetry.

## Structure

- `app.py`: Main Streamlit application containing data processing, synchronization, and UI layout.
- `dataset/`: Contains `telemetry.csv`, `image_timestamps.csv`, and the `frames/` folder.
- `requirements.txt`: Python package dependencies.

## Installation

Create a virtual environment and load dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

To launch the dashboard, use the `streamlit run` command:

```bash
streamlit run app.py
```

Open the provided local URL (typically `http://localhost:8501`) in your web browser.

## Features & Deliverables
- **Mission Statistics View:** Shows critical metrics automatically calculated from standard inputs, effectively handling lost packets or invalid records.
- **Data Table view:** Maps every given image to its exact vehicle state.
- **Interactive Map:** Displays trajectory PolyLine and start/stop positions, with specific camera icons representing the coordinates where frames were taken.
- **Image Inspector:** Clickable select box to inspect single frames and immediate state parameters (Battery, Signal, Speed).

#Demo- [https://drive.google.com/file/d/1QgE5Wbsdt5AfUm6QNdRXLikeCii_aaRe/view?usp=drive_link]
# Ground-Station-Telemetry-Dashboard
