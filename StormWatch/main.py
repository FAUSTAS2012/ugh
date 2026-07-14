from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication

from gui.main_window import StormWatchMainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("StormWatch Control Center")
    window = StormWatchMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
