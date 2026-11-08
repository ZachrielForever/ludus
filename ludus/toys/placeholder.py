"""Placeholder toy — proves the shell, registry, and heartbeat work."""

import math

from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from ludus.registry import toy


@toy
class PlaceholderToy(QWidget):
    TITLE = "Placeholder"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._t = 0.0

    def update_step(self, dt):
        self._t += dt
        self.update()  # schedule a repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            w, h = self.width(), self.height()
            x = int(w / 2 + math.sin(self._t) * (w / 3))
            y = h // 2
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QColor("#6d4aff"))
            painter.setBrush(QColor("#6d4aff"))
            painter.drawEllipse(x - 8, y - 8, 16, 16)
        finally:
            painter.end()