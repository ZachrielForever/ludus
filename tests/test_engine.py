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
# -- v2 materials -------------------------------------------------------------

def test_oil_floats_on_water():
    g, e = make_world()
    # Basin walls keep the water from spreading away (v1 had no sides —
    # the water leaked out and the oil followed into the vacated space).
    for y in range(6, 10):
        g.set(1, y, Material.WALL)
        g.set(9, y, Material.WALL)
    for y in range(7, 10):
        for x in range(2, 9):
            g.set(x, y, Material.WATER)
    for x in range(4, 7):
        g.set(x, 3, Material.OIL)
    for _ in range(300):
        e.step()
    # The water column stays oil-free: oil rests on the surface, never sinks in.
    for x in range(2, 9):
        for y in range(7, 10):
            assert g.get(x, y) != Material.OIL

def test_water_displaces_oil():
    g, e = make_world()
    for y in range(8, 10):
        for x in range(2, 9):
            g.set(x, y, Material.OIL)
    g.set(5, 5, Material.WATER)
    for _ in range(100):
        e.step()
    # The water ended up below at least one oil cell — it sank through.
    oils_above_water = any(
        g.get(x, y) == Material.OIL and g.get(x, y + 1) == Material.WATER
        for x in range(g.width) for y in range(g.height - 1)
    )
    assert oils_above_water or g.get(5, 9) == Material.WATER

def test_sand_sinks_through_oil():
    g, e = make_world()
    for y in range(6, 10):
        for x in range(2, 9):
            g.set(x, y, Material.OIL)
    g.set(5, 0, Material.SAND)
    for _ in range(80):
        e.step()
    assert g.get(5, 9) == Material.SAND          # reached bottom through oil

def test_wood_is_immobile():
    g, e = make_world()
    g.set(5, 2, Material.WOOD)
    g.set(5, 1, Material.SAND)                   # load on top changes nothing
    for _ in range(50):
        e.step()
    assert g.get(5, 2) == Material.WOOD

def test_fire_consumes_wood_and_dies_out():
    g, e = make_world()
    g.set(5, 5, Material.WOOD)
    g.set(5, 6, Material.WOOD)
    g.set(5, 4, Material.FIRE)
    g.set_meta(5, 4, 40)
    for _ in range(500):
        e.step()
    assert count(g, Material.WOOD) == 0          # the wood is gone
    assert count(g, Material.FIRE) == 0          # and so is the fire, after

def test_water_douses_fire():
    g, e = make_world()
    g.set(4, 9, Material.FIRE)
    g.set_meta(4, 9, 40)
    g.set(5, 9, Material.WATER)   # directly adjacent: no walk, no luck
    g.set(6, 9, Material.WALL)    # seal the water against the fire
    saw_steam = False
    for _ in range(10):
        e.step()
        if count(g, Material.STEAM) > 0:
            saw_steam = True
            break
    assert saw_steam
    assert count(g, Material.FIRE) == 0
    
# -- v3 density physics ------------------------------------------------------

def test_encased_water_levels_under_oil():
    # The v2 gap: water buried in oil stacked like a powder. Under real
    # density displacement it must sink to the bottom of the tank.
    g, e = make_world()
    for y in range(2, 10):
        g.set(2, y, Material.WALL); g.set(8, y, Material.WALL)
    for y in range(3, 10):
        for x in range(3, 8):
            g.set(x, y, Material.OIL)
    g.set(5, 3, Material.WATER)
    for _ in range(600):
        e.step()
    oil_ys = [y for y in range(g.height) for x in range(g.width)
              if g.get(x, y) == Material.OIL]
    water_ys = [y for y in range(g.height) for x in range(g.width)
                if g.get(x, y) == Material.WATER]
    assert water_ys, "injected water vanished"
    assert max(water_ys) >= max(oil_ys)   # water sits at the very bottom

def test_steam_bubbles_up_through_water():
    # Same density law, inverted: gas displaces liquid downward to rise.
    g, e = make_world()
    for y in range(4, 10):
        for x in range(3, 8):
            g.set(x, y, Material.WATER)
    g.set(5, 9, Material.STEAM)
    for _ in range(300):
        e.step()
    for x in range(g.width):
        for y in range(4, 10):
            if g.get(x, y) == Material.STEAM:
                assert False, f"steam still trapped in water at ({x},{y})"    
def test_water_displaces_oil():
    g, e = make_world()
    # Basin walls: v3's lateral displacement lets sunk water crawl out
    # from under an open-sided pool and escape along the floor. Contained,
    # the only exit is equilibrium: water below, oil floating above.
    for y in range(7, 10):
        g.set(1, y, Material.WALL)
        g.set(9, y, Material.WALL)
    for y in range(8, 10):
        for x in range(2, 9):
            g.set(x, y, Material.OIL)
    g.set(5, 5, Material.WATER)
    for _ in range(100):
        e.step()
    water_ys = [y for y in range(g.height) for x in range(g.width)
                if g.get(x, y) == Material.WATER]
    assert water_ys, "injected water vanished"
    assert max(water_ys) == 9        # water sits on the pool floor
    oils_above_water = any(
        g.get(x, y) == Material.OIL and g.get(x, y + 1) == Material.WATER
        for x in range(g.width) for y in range(g.height - 1)
    )
    assert oils_above_water          # oil displaced upward, floating