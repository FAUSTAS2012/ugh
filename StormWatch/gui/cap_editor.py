from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (
    QComboBox, QDateTimeEdit, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
    QLineEdit, QMessageBox, QPushButton, QTextEdit, QVBoxLayout,
)

from cap.cap12 import generate_cap_xml, parse_cap_xml
from database.models import WarningRecord, WarningStatus, default_polygon


class CapEditorDialog(QDialog):
    def __init__(self, parent=None, warning: WarningRecord | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("CAP 1.2 perspėjimo redaktorius")
        self.resize(720, 680)
        now = datetime.now(timezone.utc).replace(microsecond=0)
        self.identifier = QLineEdit(warning.identifier if warning else f"SWCC-{uuid4()}")
        self.event = QComboBox(); self.event.addItems(["Tornado Warning", "Severe Thunderstorm Warning", "Flash Flood Warning", "Extreme Weather Warning"])
        self.severity = QComboBox(); self.severity.addItems(["Extreme", "Severe", "Moderate", "Minor", "Unknown"])
        self.urgency = QComboBox(); self.urgency.addItems(["Immediate", "Expected", "Future", "Past", "Unknown"])
        self.certainty = QComboBox(); self.certainty.addItems(["Observed", "Likely", "Possible", "Unlikely", "Unknown"])
        self.area_desc = QLineEdit("Simulated warning polygon near operations sector")
        self.onset = QDateTimeEdit(QDateTime.fromSecsSinceEpoch(int(now.timestamp())))
        self.expires = QDateTimeEdit(QDateTime.fromSecsSinceEpoch(int((now + timedelta(minutes=45)).timestamp())))
        self.instructions = QTextEdit("Move to an interior room. This is a StormWatch training simulation only.")
        self.polygon = QTextEdit(" ".join(f"{lat},{lon}" for lat, lon in default_polygon()))
        self.preview = QTextEdit(); self.preview.setReadOnly(True)
        if warning:
            self._load_warning(warning)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        for label, widget in [("Identifier", self.identifier), ("Įvykis", self.event), ("Svarbumas", self.severity), ("Skubumas", self.urgency), ("Patikimumas", self.certainty), ("Teritorijos aprašymas", self.area_desc), ("Galiojimo pradžia", self.onset), ("Galiojimo pabaiga", self.expires), ("Instrukcijos", self.instructions), ("Poligono koordinatės", self.polygon)]:
            form.addRow(label, widget)
        layout.addLayout(form); layout.addWidget(self.preview)
        buttons = QHBoxLayout()
        for text, slot in [("Generuoti CAP XML", self.refresh_preview), ("Importuoti XML", self.import_xml), ("Eksportuoti XML", self.export_xml), ("Išsaugoti", self.accept), ("Atšaukti", self.reject)]:
            button = QPushButton(text); button.clicked.connect(slot); buttons.addWidget(button)
        layout.addLayout(buttons)
        self.refresh_preview()

    def _load_warning(self, warning: WarningRecord) -> None:
        self.event.setCurrentText(warning.event); self.severity.setCurrentText(warning.severity)
        self.urgency.setCurrentText(warning.urgency); self.certainty.setCurrentText(warning.certainty)
        self.area_desc.setText(warning.area_desc); self.instructions.setPlainText(warning.instructions)
        self.polygon.setPlainText(warning.polygon_text())

    def warning_record(self) -> WarningRecord:
        warning = WarningRecord(
            identifier=self.identifier.text(), event=self.event.currentText(), severity=self.severity.currentText(),
            urgency=self.urgency.currentText(), certainty=self.certainty.currentText(), area_desc=self.area_desc.text(),
            onset=self.onset.dateTime().toUTC().toString("yyyy-MM-ddTHH:mm:ss+00:00"),
            expires=self.expires.dateTime().toUTC().toString("yyyy-MM-ddTHH:mm:ss+00:00"),
            instructions=self.instructions.toPlainText(), polygon=WarningRecord.parse_polygon(self.polygon.toPlainText()),
            status=WarningStatus.ISSUED,
        )
        warning.cap_xml = generate_cap_xml(warning)
        return warning

    def refresh_preview(self) -> None:
        try:
            self.preview.setPlainText(generate_cap_xml(self.warning_record()))
        except Exception as exc:
            self.preview.setPlainText(f"CAP validation error: {exc}")

    def import_xml(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Importuoti CAP XML", "", "CAP XML (*.xml)")
        if not path: return
        data = parse_cap_xml(open(path, encoding="utf-8").read())
        self.identifier.setText(data["identifier"]); self.event.setCurrentText(data["event"])
        self.urgency.setCurrentText(data["urgency"]); self.severity.setCurrentText(data["severity"])
        self.certainty.setCurrentText(data["certainty"]); self.area_desc.setText(data["area_desc"])
        self.instructions.setPlainText(data["instructions"]); self.polygon.setPlainText(data["polygon"])
        self.refresh_preview()

    def export_xml(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Eksportuoti CAP XML", f"{self.identifier.text()}.xml", "CAP XML (*.xml)")
        if path:
            open(path, "w", encoding="utf-8").write(self.preview.toPlainText())
            QMessageBox.information(self, "CAP eksportas", "CAP XML išsaugotas lokaliai.")
