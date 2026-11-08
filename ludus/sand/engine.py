"""Falling-sand update rules v3. Pure Python, no Qt, no I/O.

One physical law governs descent: a mobile material can enter a cell
held by a strictly less-dense mobile material. Powders additionally
never move laterally through anything (piles stay piles), and liquids
displace lighter liquids laterally too — which is what lets encased
water shove oil aside and level out, the v2 gap.

Viscosity throttles lateral flow per material; steam bubbles up
through liquids by the same density law (rising = displacing heavier
material downward).

Sweeps: pass 1 bottom-up (powders, liquids), pass 2 top-down (gases,
fire). Fire ticks in place with a fuel-clock in grid meta.
"""

import random

from ludus.sand.grid import Grid
from ludus.sand.materials import DENSITY, IMMOVABLE, VISCOSITY, Material

FIRE_LIFE = 40            # frames a flame survives without fresh fuel
IGNITE_CHANCE = 0.08      # per-frame chance fire spreads into adjacent wood
CONDENSE_CHANCE = 0.01    # steam turning back into water
DISSIPATE_CHANCE = 0.005  # steam fading away entirely
BUBBLE_CHANCE = 0.4       # steam ascending through a liquid cell

LIQUIDS = (Material.WATER, Material.OIL)
POWDERS = (Material.SAND,)
NEIGHBORS = ((0, -1), (0, 1), (-1, 0), (1, 0))

class SandEngine:
    def __init__(self, grid: Grid):
        self.grid = grid
        self._left_first = True

    def step(self) -> None:
        g = self.grid
        self._left_first = not self._left_first
        xs = (range(g.width) if self._left_first
              else range(g.width - 1, -1, -1))

        # Pass 1: bottom-up. Solids and liquids fall and settle.
        for y in range(g.height - 2, -1, -1):
            for x in xs:
                m = g.get(x, y)
                if m in POWDERS:
                    self._update_powder(x, y)
                elif m in LIQUIDS:
                    self._update_liquid(x, y, m)

        # Pass 2: top-down. Gases move up; fire ticks in place.
        for y in range(g.height - 1):
            for x in xs:
                m = g.get(x, y)
                if m == Material.FIRE:
                    self._update_fire(x, y)
                elif m == Material.STEAM:
                    self._update_steam(x, y)

    # -- rules --------------------------------------------------------------

    def _update_powder(self, x: int, y: int) -> None:
        m = self.grid.get(x, y)
        if self._try_move(m, x, y, x, y + 1, lateral=False):
            return
        d = random.choice((-1, 1))
        for dx in (d, -d):
            if self._try_move(m, x, y, x + dx, y + 1, lateral=False):
                return

    def _update_liquid(self, x: int, y: int, m: Material) -> None:
        # Gravity first: down, then diagonals.
        if self._try_move(m, x, y, x, y + 1, lateral=False):
            return
        d = random.choice((-1, 1))
        for dx in (d, -d):
            if self._try_move(m, x, y, x + dx, y + 1, lateral=False):
                return
        # Lateral flow, throttled by viscosity. Displacing a lighter
        # liquid sideways is legal — encased water thus levels under oil.
        if random.random() >= 1.0 / VISCOSITY[m]:
            return
        if self._try_move(m, x, y, x + d, y, lateral=True):
            return
        if self._try_move(m, x, y, x - d, y, lateral=True):
            return

    def _update_fire(self, x: int, y: int) -> None:
        g = self.grid
        # Water douses fire outright, leaving steam behind.
        for dx, dy in NEIGHBORS:
            if g.in_bounds(x + dx, y + dy) and \
               g.get(x + dx, y + dy) == Material.WATER:
                g.set(x, y, Material.STEAM)
                g.set_meta(x, y, 0)
                return
        # Fire eats wood: each flammable neighbor may ignite.
        for dx, dy in NEIGHBORS:
            if not g.in_bounds(x + dx, y + dy):
                continue
            if g.get(x + dx, y + dy) == Material.WOOD and \
               random.random() < IGNITE_CHANCE:
                g.set(x + dx, y + dy, Material.FIRE)
                g.set_meta(x + dx, y + dy, FIRE_LIFE)
        # Fuel clock. Life out, flame out.
        life = g.get_meta(x, y)
        if life <= 1:
            g.set(x, y, Material.EMPTY)
        else:
            g.set_meta(x, y, life - 1)

    def _update_steam(self, x: int, y: int) -> None:
        g = self.grid
        if random.random() < CONDENSE_CHANCE:
            g.set(x, y, Material.WATER)     # indoor rain
            return
        if random.random() < DISSIPATE_CHANCE:
            g.set(x, y, Material.EMPTY)
            return
        # Rise into emptiness, straight up preferred.
        if self._try_move(Material.STEAM, x, y, x, y - 1, lateral=False):
            return
        # Buoyancy: bubble up through heavier liquid.
        if g.in_bounds(x, y - 1) and g.get(x, y - 1) in LIQUIDS and \
           random.random() < BUBBLE_CHANCE:
            self._swap(x, y, x, y - 1)
            return
        d = random.choice((-1, 1))
        for dx in (d, -d):
            if self._try_move(Material.STEAM, x, y, x + dx, y - 1, lateral=False):
                return

    # -- helpers ------------------------------------------------------------

    def _try_move(self, mover: Material,
                  x: int, y: int, tx: int, ty: int, lateral: bool) -> bool:
        """Move `mover` from (x,y) into (tx,ty) if physics allows. No-op
        for out-of-bounds or disallowed targets."""
        g = self.grid
        if not g.in_bounds(tx, ty):
            return False
        occupant = g.get(tx, ty)

        if occupant == mover:
            return False

        if mover in POWDERS:
            # Powders sink through strictly lighter LIQUIDS, vertically
            # only — never sideways, never through other powders.
            ok = (not lateral and occupant in LIQUIDS and
                  DENSITY[mover] > DENSITY[occupant])
        elif mover in LIQUIDS:
            # Liquids displace strictly lighter liquids, vertically or
            # laterally (lateral arrivals are viscosity-gated upstream).
            ok = occupant in LIQUIDS and DENSITY[mover] > DENSITY[occupant]
        else:   # steam: handled via dedicated paths above
            ok = occupant == Material.EMPTY

        if occupant == Material.EMPTY:
            ok = True
        if not ok:
            return False
        self._swap(x, y, tx, ty)
        return True

    def _swap(self, ax: int, ay: int, bx: int, by: int) -> None:
        g = self.grid
        a = g.get(ax, ay)
        ma = g.get_meta(ax, ay)
        g.set(ax, ay, g.get(bx, by))
        g.set_meta(ax, ay, g.get_meta(bx, by))
        g.set(bx, by, a)
        g.set_meta(bx, by, ma)