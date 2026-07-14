from __future__ import annotations

from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDockWidget, QGroupBox, QHBoxLayout, QLabel, QListWidget,
    QMainWindow, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from database.models import WarningRecord, WarningStatus
from database.store import StormWatchStore
from gui.cap_editor import CapEditorDialog
from gui.theme import DARK_STYLESHEET
from maps.folium_map import build_operations_map
from radar.simulator import RadarSimulator
from warnings.broadcast import BroadcastSimulator


class StormWatchMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("StormWatch Control Center")
        self.resize(1600, 950)
        self.setStyleSheet(DARK_STYLESHEET)
        self.store = StormWatchStore(Path.home() / ".stormwatch_control_center.sqlite3")
        self.radar = RadarSimulator()
        self.broadcast_sim = BroadcastSimulator()
        self.current_warning: WarningRecord | None = None
        self.timer = QTimer(self); self.timer.timeout.connect(self.update_radar)
        self._build_menu(); self._build_central(); self._build_left_dock(); self._build_right_dock(); self._build_timeline()
        self.statusBar().showMessage("SIMULATION MODE — no real emergency traffic leaves this workstation")
        self.update_radar(); self.refresh_warning_table(); self.refresh_timeline()

    def _build_menu(self) -> None:
        toolbar = self.addToolBar("Operations")
        for text, shortcut, slot in [("New Warning", "Ctrl+N", self.create_warning), ("Broadcast", "Ctrl+B", self.broadcast_warning), ("Fullscreen", "F11", self.toggle_fullscreen), ("Export Map", "Ctrl+M", self.export_map)]:
            action = QAction(text, self); action.setShortcut(QKeySequence(shortcut)); action.triggered.connect(slot); toolbar.addAction(action)

    def _build_central(self) -> None:
        container = QWidget(); layout = QVBoxLayout(container)
        self.plot = pg.PlotWidget(); self.plot.setBackground("#071016"); self.plot.setAspectLocked(True); self.plot.hideAxis("bottom"); self.plot.hideAxis("left")
        self.image = pg.ImageItem(); self.plot.addItem(self.image)
        self.warning_curve = pg.PlotDataItem(pen=pg.mkPen("#ff3b30", width=3)); self.plot.addItem(self.warning_curve)
        self.cell_scatter = pg.ScatterPlotItem(size=14, brush=pg.mkBrush("#ffcc00"), pen=pg.mkPen("#111")); self.plot.addItem(self.cell_scatter)
        layout.addWidget(QLabel("Interactive Radar / Geographic Operations Canvas (simulated live radar layers + editable warning polygons)"))
        layout.addWidget(self.plot, 1)
        self.setCentralWidget(container)

    def _build_left_dock(self) -> None:
        dock = QDockWidget("Radarų valdymas", self); panel = QWidget(); layout = QVBoxLayout(panel)
        self.source = QComboBox(); self.source.addItems(["KLOT Chicago Simulation", "KDMX Des Moines Simulation", "KICT Wichita Simulation"])
        layout.addWidget(QLabel("Radaro šaltinis")); layout.addWidget(self.source)
        self.layer_checks = []
        group = QGroupBox("Radarų sluoksniai"); gl = QVBoxLayout(group)
        for layer in ["Atspindys (Reflectivity)", "Greitis (Velocity)", "Kritulių intensyvumas", "Audrų sekimas", "Perspėjimų zonos"]:
            cb = QCheckBox(layer); cb.setChecked(True); cb.stateChanged.connect(self.update_radar); self.layer_checks.append(cb); gl.addWidget(cb)
        layout.addWidget(group)
        self.radar_time = QLabel("Radar time: --") ; layout.addWidget(self.radar_time)
        for text, slot in [("Paleisti", lambda: self.timer.start(1200)), ("Sustabdyti", self.timer.stop), ("Ankstesnis skenavimas", self.update_radar), ("Kitas skenavimas", self.update_radar)]:
            b = QPushButton(text); b.clicked.connect(slot); layout.addWidget(b)
        layout.addStretch(); dock.setWidget(panel); self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def _build_right_dock(self) -> None:
        dock = QDockWidget("Perspėjimų valdymo centras", self); panel = QWidget(); layout = QVBoxLayout(panel)
        for text, slot in [("+ Sukurti perspėjimą", self.create_warning), ("+ Redaguoti perspėjimą", self.edit_warning), ("+ Atšaukti perspėjimą", self.cancel_warning), ("+ Transliuoti simuliaciją", self.broadcast_warning)]:
            b = QPushButton(text); b.clicked.connect(slot); layout.addWidget(b)
        self.warning_table = QTableWidget(0, 4); self.warning_table.setHorizontalHeaderLabels(["Event", "Severity", "Status", "Expires"]); self.warning_table.itemSelectionChanged.connect(self.select_warning)
        layout.addWidget(self.warning_table, 1)
        self.devices = QListWidget(); layout.addWidget(QLabel("Broadcast receivers")); layout.addWidget(self.devices)
        dock.setWidget(panel); self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def _build_timeline(self) -> None:
        dock = QDockWidget("Operacijų laiko juosta", self); dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.timeline = QListWidget(); dock.setWidget(self.timeline); self.addDockWidget(Qt.BottomDockWidgetArea, dock)

    def update_radar(self) -> None:
        frame = self.radar.next_frame(); self.radar_time.setText(f"Radar time: {frame.timestamp}")
        data = frame.reflectivity
        if "Greitis" in self._enabled_layers(): data = data + (frame.velocity / 8)
        if "Kritulių" in self._enabled_layers(): data = data + frame.precipitation * 10
        self.image.setImage(data.T, autoLevels=True)
        spots = [{"pos": (120 + x * 100, 120 + y * 100), "data": strength} for x, y, strength in frame.storm_cells]
        self.cell_scatter.setData(spots if "Audrų" in self._enabled_layers() else [])
        self.store.add_radar_scan(self.source.currentText(), "Naujas radaro skenavimas; aptiktos audrų celės")
        self.refresh_timeline()

    def _enabled_layers(self) -> str:
        return " ".join(cb.text() for cb in self.layer_checks if cb.isChecked())

    def create_warning(self) -> None:
        dialog = CapEditorDialog(self)
        if dialog.exec():
            warning = dialog.warning_record(); self.current_warning = warning; self.store.save_warning(warning)
            self.store.log_action("Warning", f"Išduotas {warning.event}"); self.refresh_warning_table(); self.draw_warning_polygon(warning); self.refresh_timeline()

    def edit_warning(self) -> None:
        if not self.current_warning: return
        dialog = CapEditorDialog(self, self.current_warning)
        if dialog.exec():
            warning = dialog.warning_record(); warning.status = WarningStatus.UPDATED; self.current_warning = warning; self.store.save_warning(warning)
            self.store.log_action("Warning", f"Perspėjimas atnaujintas: {warning.event}"); self.refresh_warning_table(); self.draw_warning_polygon(warning); self.refresh_timeline()

    def cancel_warning(self) -> None:
        if not self.current_warning: return
        self.current_warning.status = WarningStatus.CANCELLED; self.store.save_warning(self.current_warning)
        self.store.log_action("Warning", f"Atšauktas perspėjimas: {self.current_warning.event}"); self.refresh_warning_table(); self.refresh_timeline()

    def broadcast_warning(self) -> None:
        if not self.current_warning:
            QMessageBox.warning(self, "No warning", "Pirmiausia sukurkite arba pasirinkite perspėjimą."); return
        self.devices.clear()
        for line in self.broadcast_sim.broadcast(self.current_warning): self.devices.addItem(line)
        self.store.log_action("Broadcast", f"Simuliuota transliacija: {self.current_warning.event}")
        QMessageBox.information(self, "WARNING RECEIVED", f"\aSIMULATION ONLY\n\n{self.current_warning.cap_xml[:900]}")
        self.refresh_timeline()

    def refresh_warning_table(self) -> None:
        warnings = self.store.list_warnings(); self.warning_table.setRowCount(len(warnings))
        for row, warning in enumerate(warnings):
            for col, value in enumerate([warning.event, warning.severity, warning.status.value, warning.expires]):
                self.warning_table.setItem(row, col, QTableWidgetItem(value))
        if warnings and self.current_warning is None: self.current_warning = warnings[0]; self.draw_warning_polygon(warnings[0])

    def select_warning(self) -> None:
        row = self.warning_table.currentRow(); warnings = self.store.list_warnings()
        if 0 <= row < len(warnings): self.current_warning = warnings[row]; self.draw_warning_polygon(self.current_warning)

    def draw_warning_polygon(self, warning: WarningRecord) -> None:
        pts = warning.polygon + [warning.polygon[0]] if warning.polygon else []
        self.warning_curve.setData([120 + lon % 1 * 160 for _, lon in pts], [120 + lat % 1 * 160 for lat, _ in pts])

    def refresh_timeline(self) -> None:
        self.timeline.clear()
        for event in self.store.timeline(120):
            self.timeline.addItem(f"{event.timestamp[11:16]} - {event.message} ({event.category})")

    def export_map(self) -> None:
        path = build_operations_map(Path.home() / "stormwatch_operations_map.html", self.store.list_warnings())
        QMessageBox.information(self, "Map exported", f"Folium operations map exported to {path}")

    def toggle_fullscreen(self) -> None:
        self.showNormal() if self.isFullScreen() else self.showFullScreen()
