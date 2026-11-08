"""Materials for the falling-sand engine. Pure data, no Qt.

Colors are plain RGB tuples so the engine core stays portable and
testable; the toy layer converts them to QColor at render time.
"""

import enum


class Material(enum.IntEnum):
    EMPTY = 0
    WALL = 1
    SAND = 2
    WATER = 3


# Base color per material.
PALETTE = {
    Material.EMPTY: (18, 18, 20),
    Material.WALL:  (115, 120, 126),
    Material.SAND:  (196, 178, 122),
    Material.WATER: (64, 118, 224),
}


def shade(material: Material, x: int, y: int) -> tuple:
    """Deterministic per-cell brightness variation, for texture.

    Same cell always shades the same, so the world doesn't shimmer.
    """
    r, g, b = PALETTE[material]
    d = ((x * 11 + y * 17) & 7) - 4   # -4..3
    return (max(r + d, 0), max(g + d, 0), max(b + d, 0))