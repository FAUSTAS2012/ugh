# StormWatch Control Center

StormWatch Control Center is an educational, local-only meteorological operations workstation inspired by professional weather operations environments such as AWIPS and SmartMet.

> Safety notice: this application never sends real emergency alerts. CAP messages, broadcasts, devices, and radio/phone delivery are simulated locally for training and demonstration.

## Features

- PySide6 dark operations-center UI
- Radar control panel with animated simulated scans
- PyQtGraph radar canvas with reflectivity, velocity, precipitation, storm tracks, and warning polygons
- Optional Folium map export for geographic context
- CAP 1.2 alert editor with XML import/export
- SQLite persistence for warnings, polygons, radar scans, actions, and history
- Timeline of radar updates, operator activity, warning lifecycle, and simulated broadcasts
- Simulated broadcast receivers for phones, tablet, and radio
- Keyboard shortcuts and full-screen operations mode

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r StormWatch/requirements.txt
python StormWatch/main.py
```

Python 3.13+ is recommended.
