from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


UTC = timezone.utc


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


class WarningStatus(str, Enum):
    DRAFT = "Draft"
    ISSUED = "Issued"
    UPDATED = "Updated"
    CANCELLED = "Cancelled"
    EXPIRED = "Expired"


@dataclass(slots=True)
class WarningRecord:
    identifier: str
    event: str
    severity: str
    urgency: str
    certainty: str
    area_desc: str
    onset: str
    expires: str
    instructions: str
    polygon: list[tuple[float, float]]
    status: WarningStatus = WarningStatus.DRAFT
    cap_xml: str = ""

    def polygon_text(self) -> str:
        return " ".join(f"{lat:.4f},{lon:.4f}" for lat, lon in self.polygon)

    @classmethod
    def parse_polygon(cls, text: str) -> list[tuple[float, float]]:
        points: list[tuple[float, float]] = []
        for raw in text.replace(";", " ").split():
            if not raw.strip():
                continue
            lat_text, lon_text = raw.split(",", 1)
            points.append((float(lat_text), float(lon_text)))
        return points


@dataclass(slots=True)
class TimelineEvent:
    timestamp: str
    category: str
    message: str


def default_polygon() -> list[tuple[float, float]]:
    return [(41.85, -88.10), (42.18, -87.82), (42.02, -87.35), (41.70, -87.60)]


def polygon_bounds(points: Iterable[tuple[float, float]]) -> tuple[float, float, float, float]:
    latitudes = [p[0] for p in points]
    longitudes = [p[1] for p in points]
    return min(latitudes), min(longitudes), max(latitudes), max(longitudes)
