from __future__ import annotations

from datetime import datetime, timezone
from xml.etree import ElementTree as ET

from database.models import WarningRecord

CAP_NS = "urn:oasis:names:tc:emergency:cap:1.2"
ET.register_namespace("", CAP_NS)


def _tag(name: str) -> str:
    return f"{{{CAP_NS}}}{name}"


def generate_cap_xml(warning: WarningRecord, sender: str = "operator@stormwatch.local") -> str:
    alert = ET.Element(_tag("alert"))
    values = {
        "identifier": warning.identifier,
        "sender": sender,
        "sent": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "Exercise",
        "msgType": "Alert" if warning.status.value != "Cancelled" else "Cancel",
        "scope": "Public",
    }
    for key, value in values.items():
        ET.SubElement(alert, _tag(key)).text = value

    info = ET.SubElement(alert, _tag("info"))
    for key, value in {
        "category": "Met",
        "event": warning.event,
        "urgency": warning.urgency,
        "severity": warning.severity,
        "certainty": warning.certainty,
        "effective": warning.onset,
        "expires": warning.expires,
        "senderName": "StormWatch Control Center Simulation",
        "headline": f"{warning.event} - SIMULATION ONLY",
        "description": warning.area_desc,
        "instruction": warning.instructions,
    }.items():
        ET.SubElement(info, _tag(key)).text = value

    area = ET.SubElement(info, _tag("area"))
    ET.SubElement(area, _tag("areaDesc")).text = warning.area_desc
    ET.SubElement(area, _tag("polygon")).text = warning.polygon_text()
    return ET.tostring(alert, encoding="unicode", xml_declaration=True)


def parse_cap_xml(xml_text: str) -> dict[str, str]:
    root = ET.fromstring(xml_text)
    info = root.find(_tag("info"))
    area = info.find(_tag("area")) if info is not None else None
    return {
        "identifier": root.findtext(_tag("identifier"), ""),
        "event": info.findtext(_tag("event"), "") if info is not None else "",
        "urgency": info.findtext(_tag("urgency"), "") if info is not None else "",
        "severity": info.findtext(_tag("severity"), "") if info is not None else "",
        "certainty": info.findtext(_tag("certainty"), "") if info is not None else "",
        "area_desc": area.findtext(_tag("areaDesc"), "") if area is not None else "",
        "polygon": area.findtext(_tag("polygon"), "") if area is not None else "",
        "instructions": info.findtext(_tag("instruction"), "") if info is not None else "",
        "onset": info.findtext(_tag("effective"), "") if info is not None else "",
        "expires": info.findtext(_tag("expires"), "") if info is not None else "",
    }
