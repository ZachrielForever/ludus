"""Falling Sand toy — draws materials into a living world.

Simulation lives in ludus.sand (pure Python); this module only
translates mouse input into grid edits and grid state into pixels.
"""

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QWidget

from ludus.registry import toy
from ludus.sand.engine import SandEngine
from ludus.sand.grid import Grid
from ludus.sand.materials import Material, shade

CELL = 5        # pixels per simulated cell
BRUSH = 3       # brush radius in cells
BINDINGS = {    # number-key material selection
    Qt.Key.Key_1: Material.SAND,
    Qt.Key.Key_2: Material.WATER,
    Qt.Key.Key_3: Material.WALL,
    Qt.Key.Key_4: Material.EMPTY,
}


@toy
class SandToy(QWidget):
    TITLE = "Falling Sand"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._material = Material.SAND
        self._drawing = False
        self._last = None
        # Grid sized to the fixed window; created lazily on first paint,
        # when the widget finally knows its real size.
        self._grid = None
        self._engine = None
        self._buffer = None

    # -- toy interface -------------------------------------------------------

    def update_step(self, dt):
        if self._engine:
            self._engine.step()
        self.update()

    # -- setup ----------------------------------------------------------------

    def _ensure_world(self):
        if self._grid is not None:
            return
        gw, gh = self.width() // CELL, self.height() // CELL
        self._grid = Grid(gw, gh)
        self._engine = SandEngine(self._grid)
        # Floor of wall so material doesn't just vanish off the bottom edge.
        for x in range(gw):
            self._grid.set(x, gh - 1, Material.WALL)

    # -- input ----------------------------------------------------------------

    def keyPressEvent(self, event):
        if event.key() in BINDINGS:
            self._material = BINDINGS[event.key()]
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self._drawing = True
        self._paint_at(event.position())
        self._last = event.position()

    def mouseReleaseEvent(self, event):
        self._drawing = False
        self._last = None

    def mouseMoveEvent(self, event):
        if not self._drawing:
            return
        # Interpolate so fast strokes don't leave dotted gaps.
        steps = int(max(abs(event.position().x() - self._last.x()),
                        abs(event.position().y() - self._last.y())) / CELL)
        for i in range(steps + 1):
            t = 0 if steps == 0 else i / steps
            x = self._last.x() + (event.position().x() - self._last.x()) * t
            y = self._last.y() + (event.position().y() - self._last.y()) * t
            self._paint_at(QPointF(x, y))
        self._last = event.position()

    def _paint_at(self, pos):
        self._ensure_world()
        cx, cy = int(pos.x()) // CELL, int(pos.y()) // CELL
        # Eraser may clear anything; other materials only fill emptiness.
        self._grid.fill_circle(cx, cy, BRUSH, self._material,
                               only_empty=self._material != Material.EMPTY)

    # -- rendering --------------------------------------------------------------

    def paintEvent(self, event):
        self._ensure_world()
        gw, gh = self._grid.width, self._grid.height
        self._buffer = bytes(
            v for y in range(gh) for x in range(gw)
            for v in shade(self._grid.get(x, y), x, y)
        )
        image = QImage(self._buffer, gw, gh, gw * 3, QImage.Format.Format_RGB888)
        painter = QPainter(self)
        try:
            painter.drawImage(self.rect(), image)
            painter.setPen(Qt.white)
            painter.drawText(
                10, 20,
                f"1 Sand  2 Water  3 Wall  4 Erase   [drawing: {self._material.name.title()}]",
            )
        finally:
            painter.end()