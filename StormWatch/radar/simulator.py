from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np


@dataclass(slots=True)
class RadarFrame:
    timestamp: str
    reflectivity: np.ndarray
    velocity: np.ndarray
    precipitation: np.ndarray
    storm_cells: list[tuple[float, float, float]]


class RadarSimulator:
    def __init__(self, size: int = 240) -> None:
        self.size = size
        self.frame_index = 0
        axis = np.linspace(-1.0, 1.0, size)
        self.x_grid, self.y_grid = np.meshgrid(axis, axis)

    def next_frame(self) -> RadarFrame:
        self.frame_index += 1
        t = self.frame_index / 8.0
        reflectivity = np.zeros((self.size, self.size), dtype=float)
        cells: list[tuple[float, float, float]] = []
        for i, base in enumerate((-0.45, 0.05, 0.38)):
            cx = base + 0.25 * math.sin(t + i)
            cy = -0.15 + 0.35 * math.cos(t * 0.7 + i * 1.6)
            strength = 38 + 22 * abs(math.sin(t + i * 0.9))
            core = np.exp(-(((self.x_grid - cx) ** 2) / 0.016 + ((self.y_grid - cy) ** 2) / 0.028))
            anvil = np.exp(-(((self.x_grid - cx + 0.08) ** 2) / 0.075 + ((self.y_grid - cy - 0.04) ** 2) / 0.040))
            reflectivity += strength * core + (strength * 0.45) * anvil
            cells.append((cx, cy, strength))
        reflectivity += random.random() * 3.0
        velocity = 70 * np.sin(4 * self.x_grid + t) * np.cos(3 * self.y_grid - t)
        precipitation = np.clip(reflectivity / 65.0, 0.0, 1.0)
        return RadarFrame(
            timestamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            reflectivity=np.clip(reflectivity, 0, 75),
            velocity=velocity,
            precipitation=precipitation,
            storm_cells=cells,
        )
