"""Falling Sand toy — category dropdowns + canvas + HUD.

SandToy is the container (comboboxes per material category, eraser,
keyboard, heartbeat delegation); SandCanvas owns painting and mouse
input. Simulation lives in ludus.sand (pure Python, Qt-free) — tests
exercise it headlessly.

Toolbar structure is generated from materials.CATEGORIES — new
materials slot into their category combobox automatically.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget,
)

from ludus.registry import toy
from ludus.sand.engine import SandEngine
from ludus.sand.grid import Grid
from ludus.sand.materials import CATEGORIES, Material, shade

CELL = 5        # pixels per simulated cell
BRUSH = 3       # brush radius in cells

LABELS = {
    Material.SAND: "Sand",
    Material.WATER: "Water",
    Material.OIL: "Oil",
    Material.WOOD: "Wood",
    Material.WALL: "Wall",
    Material.FIRE: "Fire",
    Material.STEAM: "Steam",
    Material.EMPTY: "Eraser",
}

# Number keys walk the flattened category order, eraser last.
_FLAT = [m for _label, members in CATEGORIES for m in members]
KEYS = {
    getattr(Qt.Key, f"Key_{i}"): m
    for i, m in enumerate(_FLAT, start=1)
}
KEYS[getattr(Qt.Key, f"Key_{len(_FLAT) + 1}")] = Material.EMPTY

COUNTED = [m for m in _FLAT]   # HUD order matches the toolbar order

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

            # HUD: grid truth beside visual truth; zero-counts stay quiet.
            counts = {m: 0 for m in COUNTED}
            for y in range(gh):
                for x in range(gw):
                    m = g.get(x, y)
                    if m in counts:
                        counts[m] += 1
            shown = "   ".join(
                f"{LABELS[m].lower()} {counts[m]}"
                for m in COUNTED if counts[m]
            )
            painter.setPen(Qt.white)
            painter.drawText(10, 20,
                             f"drawing: {LABELS[self.material].lower()}   {shown}")
        finally:
            painter.end()

@toy
class SandToy(QWidget):
    TITLE = "Falling Sand"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = SandCanvas(self)
        self._syncing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        bar = QHBoxLayout()
        self.combos = []
        for label, members in CATEGORIES:
            box = QComboBox()
            for m in members:
                box.addItem(f"{label}: {LABELS[m]}", int(m))
            box.currentIndexChanged.connect(self._combo_changed)
            bar.addWidget(box)
            self.combos.append(box)

        self.eraser_btn = QPushButton("Eraser")
        self.eraser_btn.setCheckable(True)
        self.eraser_btn.toggled.connect(self._eraser_toggled)
        bar.addWidget(self.eraser_btn)

        bar.addStretch(1)
        layout.addLayout(bar)
        layout.addWidget(self.canvas, stretch=1)

        self.select(Material.SAND)                 # default selection

    # -- selection plumbing ---------------------------------------------------

    def _combo_changed(self, index: int) -> None:
        if self._syncing:
            return
        box = self.sender()
        data = box.itemData(index)
        if data is not None:
            self.select(Material(data))

    def _eraser_toggled(self, checked: bool) -> None:
        if self._syncing:
            return
        self.select(Material.EMPTY if checked else Material.SAND)

    def select(self, material: Material) -> None:
        """Single source of truth: canvas, comboboxes, eraser, keys."""
        self._syncing = True
        try:
            self.canvas.set_material(material)
            for box in self.combos:
                box.setCurrentIndex(box.findData(int(material)))
            self.eraser_btn.setChecked(material == Material.EMPTY)
        finally:
            self._syncing = False

    # -- toy interface ---------------------------------------------------------

    def update_step(self, dt):
        self.canvas.tick()

    def keyPressEvent(self, event):
        if event.key() in KEYS:
            self.select(KEYS[event.key()])
        else:
            super().keyPressEvent(event)