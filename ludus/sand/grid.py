"""Grid storage for cellular automata. Holds state, enforces nothing."""

from ludus.sand.materials import Material


class Grid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells = bytearray(width * height)   # one Material byte per cell

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> Material:
        return Material(self.cells[y * self.width + x])

    def set(self, x: int, y: int, material: Material) -> None:
        self.cells[y * self.width + x] = material

    def fill_circle(self, cx: int, cy: int, radius: int,
                    material: Material, only_empty: bool = True) -> None:
        """Brush stamp. only_empty keeps paint from bulldozing existing cells."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy > radius * radius:
                    continue
                x, y = cx + dx, cy + dy
                if not self.in_bounds(x, y):
                    continue
                if only_empty and self.get(x, y) != Material.EMPTY:
                    continue
                self.set(x, y, material)