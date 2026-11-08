"""Engine unit tests — headless, no Qt required.

These verify the rules the HUD lets you eyeball: gravity, conservation,
sinking, immobility, leveling. Run from the repo root:
    python -m pytest tests/ -q
"""

from ludus.sand.engine import SandEngine
from ludus.sand.grid import Grid
from ludus.sand.materials import Material


def make_world(width=11, height=11):
    """Fresh grid with a wall floor, plus its engine."""
    g = Grid(width, height)
    for x in range(width):
        g.set(x, height - 1, Material.WALL)
    return g, SandEngine(g)


def count(g, material):
    return sum(
        1 for y in range(g.height) for x in range(g.width)
        if g.get(x, y) == material
    )


def test_gravity_pulls_sand_down():
    g, e = make_world()
    g.set(5, 0, Material.SAND)
    for _ in range(20):
        e.step()
    assert g.get(5, 9) == Material.SAND          # rested on the floor


def test_sand_count_is_conserved():
    g, e = make_world()
    for x in range(0, 11, 2):
        g.set(x, 0, Material.SAND)
    before = count(g, Material.SAND)
    for _ in range(200):
        e.step()
    assert count(g, Material.SAND) == before     # nothing created or destroyed


def test_sand_sinks_through_water():
    # Tube sealed by wall columns; water column with sand dropped on top.
    g, e = make_world(width=3)
    g.set(0, 0, Material.WALL); g.set(2, 0, Material.WALL)
    for y in range(4, 10):
        g.set(0, y, Material.WALL); g.set(2, y, Material.WALL)
        g.set(1, y, Material.WATER)
    water_before = count(g, Material.WATER)
    g.set(1, 0, Material.SAND)
    for _ in range(60):
        e.step()
    assert g.get(1, 9) == Material.SAND          # sank to the tube's bottom
    assert count(g, Material.WATER) == water_before


def test_walls_never_move():
    g, e = make_world()
    g.set(5, 5, Material.WALL)
    for _ in range(20):
        e.step()
    assert g.get(5, 5) == Material.WALL


def test_water_levels_out():
    # Uneven water in a sealed basin seeks its level, within tolerance.
    g, e = make_world(width=7)
    for y in range(10):
        g.set(0, y, Material.WALL); g.set(6, y, Material.WALL)
    for y in range(6, 10):
        for x in range(1, 5):                   # fill the left side only
            g.set(x, y, Material.WATER)
    for _ in range(400):
        e.step()
    levels = [
        sum(1 for y in range(10) if g.get(x, y) == Material.WATER)
        for x in range(1, 6)
    ]
    assert max(levels) - min(levels) <= 2        # roughly leveled