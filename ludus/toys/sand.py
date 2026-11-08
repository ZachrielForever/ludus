"""Falling Sand toy — toolbar + canvas + HUD.

SandToy is the container (toolbar, keyboard, heartbeat delegation);
SandCanvas owns painting and mouse input. Simulation lives in
ludus.sand (pure Python, Qt-free) — tests exercise it headlessly.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QPushButton, QVBoxLayout, QWidget,
)

from ludus.registry import toy
from ludus.sand.engine import SandEngine
from ludus.sand.grid import Grid
from ludus.sand.materials import Material, shade

CELL = 5        # pixels per simulated cell
BRUSH = 3       # brush radius in cells

# Toolbar order == key order. Eraser listed last; it clears, not builds.
MATERIALS = (Material.SAND, Material.WATER, Material.WALL, Material.EMPTY)
LABELS = {
    Material.SAND: "Sand",
    Material.WATER: "Water",
    Material.WALL: "Wall",
    Material.EMPTY: "Eraser",
}
KEYS = {
    Qt.Key.Key_1: Material.SAND,
    Qt.Key.Key_2: Material.WATER,
    Qt.Key.Key_3: Material.WALL,
    Qt.Key.Key_4: Material.EMPTY,
}


class SandCanvas(QWidget):
    """The simulated world: mouse input in, pixels out."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.material = Material.SAND
        self._drawing = False
        self._last_pos = None
        self._grid = None
        self._engine = None

    def set_material(self, material: Material) -> None:
        self.material = material

    def tick(self):
        if self._engine:
            self._engine.step()
        self.update()

    def _ensure_world(self):
        if self._grid is not None:
            return
        gw, gh = self.width() // CELL, self.height() // CELL
        self._grid = Grid(gw, gh)
        self._engine = SandEngine(self._grid)
        for x in range(gw):                      # floor: nothing falls forever
            self._grid.set(x, gh - 1, Material.WALL)

    # -- input ----------------------------------------------------------------

    def mousePressEvent(self, event):
        self._drawing = True
        self._paint_at(event.position())
        self._last_pos = event.position()

    def mouseReleaseEvent(self, event):
        self._drawing = False
        self._last_pos = None

    def mouseMoveEvent(self, event):
        if not self._drawing:
            return
        steps = int(max(abs(event.position().x() - self._last_pos.x()),
                        abs(event.position().y() - self._last_pos.y())) / CELL)
        for i in range(steps + 1):
            t = 0 if steps == 0 else i / steps
            x = self._last_pos.x() + (event.position().x() - self._last_pos.x()) * t
            y = self._last_pos.y() + (event.position().y() - self._last_pos.y()) * t
            self._paint_at(event.position().__class__(x, y))
        self._last_pos = event.position()

    def _paint_at(self, pos):
        self._ensure_world()
        cx, cy = int(pos.x()) // CELL, int(pos.y()) // CELL
        self._grid.fill_circle(cx, cy, BRUSH, self.material,
                               only_empty=self.material != Material.EMPTY)

    # -- rendering --------------------------------------------------------------

    def paintEvent(self, event):
        self._ensure_world()
        g = self._grid
        gw, gh = g.width, g.height

        buffer = bytes(
            v for y in range(gh) for x in range(gw)
            for v in shade(g.get(x, y), x, y)
        )
        image = QImage(buffer, gw, gh, gw * 3, QImage.Format.Format_RGB888)

        painter = QPainter(self)
        try:
            painter.drawImage(self.rect(), image)

            # HUD: ground truth from the grid, next to what your eyes see.
            counts = {m: 0 for m in MATERIALS}
            for y in range(gh):
                for x in range(gw):
                    m = g.get(x, y)
                    if m in counts:
                        counts[m] += 1
            painter.setPen(Qt.white)
            painter.drawText(10, 20, (
                f"drawing: {LABELS[self.material].lower()}   "
                f"sand {counts[Material.SAND]}  water {counts[Material.WATER]}  "
                f"wall {counts[Material.WALL]}"
            ))
        finally:
            painter.end()


@toy
class SandToy(QWidget):
    TITLE = "Falling Sand"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = SandCanvas(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        bar = QHBoxLayout()
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = {}
        for m in MATERIALS:
            btn = QPushButton(LABELS[m])
            btn.setCheckable(True)
            self.group.addButton(btn, int(m))
            btn.clicked.connect(lambda _=False, mat=m: self.select(mat))
            bar.addWidget(btn)
            self.buttons[m] = btn

        layout.addLayout(bar)
        layout.addWidget(self.canvas, stretch=1)

        self.select(Material.SAND)                 # default selection

    def select(self, material: Material) -> None:
        """Single source of truth: updates canvas, button checks, keys."""
        self.canvas.set_material(material)
        for m, btn in self.buttons.items():
            btn.setChecked(m == material)

    # -- toy interface ---------------------------------------------------------

    def update_step(self, dt):
        self.canvas.tick()

    def keyPressEvent(self, event):
        if event.key() in KEYS:
            self.select(KEYS[event.key()])
        else:
            super().keyPressEvent(event)