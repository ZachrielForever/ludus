#!/usr/bin/env python3
"""Ludus — a desktop toybox. Entry point."""

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

import ludus.toys  # noqa: F401 — imports toys so @toy fires for each
from ludus.registry import all_toys

FPS = 60

class LudusWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ludus")

        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(False)  # never scroll; size to fit instead
        for toy_cls in all_toys():
            self.tabs.addTab(toy_cls(), toy_cls.TITLE)
        self.setCentralWidget(self.tabs)

        # Window sized by content: tab bar width + frame allowance, fixed height.
        bar_width = self.tabs.tabBar().sizeHint().width()
        needed = max(bar_width + 40, 900)   # 40px margin for window chrome
        self.setFixedSize(needed, 650)

        # Heartbeat: drive whichever toy is on-screen, ~60fps.
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(int(1000 / FPS))

    def _tick(self):
        widget = self.tabs.currentWidget()
        if hasattr(widget, "update_step"):
            widget.update_step(1 / FPS)

def main():
    app = QApplication(sys.argv)
    window = LudusWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()