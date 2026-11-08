"""Placeholder toys — prove the shell, registry, and heartbeat work."""

import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QWidget

from ludus.registry import toy

class PlaceholderToy(QWidget):
    """Base toy: a swaying purple dot, driven by the shell heartbeat."""

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
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#6d4aff"))
            painter.drawEllipse(x - 8, h // 2 - 8, 16, 16)
        finally:
            painter.end()

@toy
class SandToy(PlaceholderToy):
    TITLE = "Falling Sand"

@toy
class BuddyToy(PlaceholderToy):
    TITLE = "Interactive Buddy"

@toy
class WindTunnelToy(PlaceholderToy):
    TITLE = "Wind Tunnel"

@toy
class TbdToy(PlaceholderToy):
    """Reserved slot — claims a tab until a real toy earns it."""

    TITLE = "TBD"

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QColor("#8a8a8a"))
            painter.setFont(QFont(self.font().family(), 16))
            painter.drawText(self.rect(), Qt.AlignCenter, "TBD")
        finally:
            painter.end()