from __future__ import annotations

from dataclasses import dataclass

from database.models import WarningRecord


@dataclass(slots=True)
class SimulatedDevice:
    name: str
    kind: str
    received: bool = False


class BroadcastSimulator:
    """Local-only fake alert distribution network."""

    def __init__(self) -> None:
        self.devices = [
            SimulatedDevice("Telefonas 1", "phone"),
            SimulatedDevice("Telefonas 2", "phone"),
            SimulatedDevice("Planšetė", "tablet"),
            SimulatedDevice("Radijo imtuvas", "radio"),
        ]

    def broadcast(self, warning: WarningRecord) -> list[str]:
        for device in self.devices:
            device.received = True
        return [
            f"{device.name}: WARNING RECEIVED — {warning.event} / {warning.severity}"
            for device in self.devices
        ]
