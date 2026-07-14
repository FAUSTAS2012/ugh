from __future__ import annotations

from pathlib import Path

import folium

from database.models import WarningRecord, default_polygon


def build_operations_map(path: Path, warnings: list[WarningRecord] | None = None) -> Path:
    m = folium.Map(location=[41.9, -87.75], zoom_start=8, tiles="CartoDB dark_matter")
    folium.CircleMarker([41.9, -87.75], radius=6, color="#00d4ff", popup="KLOT Radar Simulation").add_to(m)
    for warning in warnings or []:
        folium.Polygon(
            locations=warning.polygon or default_polygon(),
            color="#ff3b30",
            fill=True,
            fill_opacity=0.22,
            popup=f"{warning.event} ({warning.status.value})",
        ).add_to(m)
    path.parent.mkdir(parents=True, exist_ok=True)
    m.save(path)
    return path
