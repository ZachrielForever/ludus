"""Materials for the falling-sand engine. Pure data, no Qt.

Colors are plain RGB tuples so the engine core stays portable and
testable; the toy layer converts them to QColor at render time.

DENSITY — relative units (kg/m³-ish). The engine's single rule:
a mobile material descends into strictly less-dense mobile material.
IMMOVABLE cells block everything. One rule yields sand sinking
through water, water sinking through oil, oil floating — no pairs.

VISCOSITY — lateral-flow throttle. A liquid attempts sideways motion
on average once per VISCOSITY[m] frames. 1 = runny, higher = thick.
"""

import enum
import random

class Material(enum.IntEnum):
    EMPTY = 0
    WALL = 1
    SAND = 2
    WATER = 3
    OIL = 4
    WOOD = 5
    FIRE = 6
    STEAM = 7

# Base color per material.
PALETTE = {
    Material.EMPTY: (28, 28, 32),      # flat system-dark grey, no dither
    Material.WALL:  (115, 120, 126),
    Material.SAND:  (196, 178, 122),
    Material.WATER: (64, 118, 224),
    Material.OIL:   (82, 66, 46),
    Material.WOOD:  (128, 86, 52),
    Material.FIRE:   (232, 120, 48),
    Material.STEAM: (170, 182, 192),
}

# One number now carries what SINKS_THROUGH used to hard-code.
DENSITY = {
    Material.EMPTY: 0,
    Material.STEAM: 1,
    Material.FIRE:  2,
    Material.OIL:   900,
    Material.WATER: 1000,
    Material.SAND:  1600,
    Material.WOOD:  2400,     # static today; density awaits future flotation
    Material.WALL:  10_000,
}

IMMOVABLE = frozenset({Material.WALL, Material.WOOD})

VISCOSITY = {
    Material.WATER: 1,        # flows freely
    Material.OIL: 3,          # crawls; sits in thick blobs
}

# Toolbar organization — the UI renders this structurally, not by hand.
CATEGORIES = (
    ("Solids",  (Material.SAND, Material.WALL, Material.WOOD)),
    ("Liquids", (Material.WATER, Material.OIL)),
    ("Gases",   (Material.STEAM, Material.FIRE)),
)

def shade(material: Material, x: int, y: int) -> tuple:
    """Deterministic per-cell brightness variation, for texture.

    Exceptions: EMPTY stays flat (backgrounds shouldn't shimmer) and
    FIRE flickers (fire should).
    """
    if material == Material.EMPTY:
        return PALETTE[Material.EMPTY]

    if material == Material.FIRE:
        return random.choice((
            (255, 160, 64),
            (232, 120, 48),
            (208, 76, 28),
        ))

    r, g, b = PALETTE[material]
    d = ((x * 11 + y * 17) & 7) - 4   # -4..3, stable per cell
    return (max(r + d, 0), max(g + d, 0), max(b + d, 0))