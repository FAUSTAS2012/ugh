from __future__ import annotations

import sqlite3
from pathlib import Path

from database.models import TimelineEvent, WarningRecord, WarningStatus, utc_now_iso


class StormWatchStore:
    """SQLite persistence layer for the local simulation workstation."""

    def __init__(self, path: Path | str = "stormwatch.sqlite3") -> None:
        self.path = Path(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.initialize()

    def initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS warnings (
                identifier TEXT PRIMARY KEY,
                event TEXT NOT NULL,
                severity TEXT NOT NULL,
                urgency TEXT NOT NULL,
                certainty TEXT NOT NULL,
                area_desc TEXT NOT NULL,
                onset TEXT NOT NULL,
                expires TEXT NOT NULL,
                instructions TEXT NOT NULL,
                polygon TEXT NOT NULL,
                status TEXT NOT NULL,
                cap_xml TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS radar_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                scan_time TEXT NOT NULL,
                summary TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS operator_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                message TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS warning_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warning_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def save_warning(self, warning: WarningRecord) -> None:
        now = utc_now_iso()
        self.connection.execute(
            """
            INSERT INTO warnings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(identifier) DO UPDATE SET
                event=excluded.event, severity=excluded.severity, urgency=excluded.urgency,
                certainty=excluded.certainty, area_desc=excluded.area_desc, onset=excluded.onset,
                expires=excluded.expires, instructions=excluded.instructions, polygon=excluded.polygon,
                status=excluded.status, cap_xml=excluded.cap_xml, updated_at=excluded.updated_at
            """,
            (
                warning.identifier, warning.event, warning.severity, warning.urgency,
                warning.certainty, warning.area_desc, warning.onset, warning.expires,
                warning.instructions, warning.polygon_text(), warning.status.value,
                warning.cap_xml, now, now,
            ),
        )
        self.add_history(warning.identifier, warning.status.value, warning.event)
        self.connection.commit()

    def list_warnings(self) -> list[WarningRecord]:
        rows = self.connection.execute("SELECT * FROM warnings ORDER BY updated_at DESC").fetchall()
        return [
            WarningRecord(
                identifier=row["identifier"], event=row["event"], severity=row["severity"],
                urgency=row["urgency"], certainty=row["certainty"], area_desc=row["area_desc"],
                onset=row["onset"], expires=row["expires"], instructions=row["instructions"],
                polygon=WarningRecord.parse_polygon(row["polygon"]),
                status=WarningStatus(row["status"]), cap_xml=row["cap_xml"],
            )
            for row in rows
        ]

    def add_radar_scan(self, source: str, summary: str) -> None:
        self.connection.execute(
            "INSERT INTO radar_scans(source, scan_time, summary) VALUES (?, ?, ?)",
            (source, utc_now_iso(), summary),
        )
        self.log_action("Radar", summary)
        self.connection.commit()

    def log_action(self, category: str, message: str) -> None:
        self.connection.execute(
            "INSERT INTO operator_actions(timestamp, category, message) VALUES (?, ?, ?)",
            (utc_now_iso(), category, message),
        )

    def add_history(self, warning_id: str, action: str, details: str) -> None:
        self.connection.execute(
            "INSERT INTO warning_history(warning_id, timestamp, action, details) VALUES (?, ?, ?, ?)",
            (warning_id, utc_now_iso(), action, details),
        )

    def timeline(self, limit: int = 200) -> list[TimelineEvent]:
        rows = self.connection.execute(
            "SELECT timestamp, category, message FROM operator_actions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [TimelineEvent(row["timestamp"], row["category"], row["message"]) for row in reversed(rows)]
