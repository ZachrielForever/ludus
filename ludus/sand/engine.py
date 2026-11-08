"""Falling-sand update rules. Pure Python, no Qt, no I/O.

Each step sweeps bottom-up so settled sand doesn't fall twice in one
frame. Sweep direction alternates left/right to kill directional bias.
"""

import random

from ludus.sand.grid import Grid
from ludus.sand.materials import Material


class SandEngine:
    def __init__(self, grid: Grid):
        self.grid = grid
        self._left_first = True

    def step(self) -> None:
        g = self.grid
        self._left_first = not self._left_first
        xs = (range(g.width) if self._left_first
              else range(g.width - 1, -1, -1))
        for y in range(g.height - 2, -1, -1):
            for x in xs:
                m = g.get(x, y)
                if m == Material.SAND:
                    self._update_sand(x, y)
                elif m == Material.WATER:
                    self._update_water(x, y)

    # -- rules --------------------------------------------------------------

    def _update_sand(self, x: int, y: int) -> None:
        g = self.grid
        # Straight down, sinking through water.
        if g.get(x, y + 1) in (Material.EMPTY, Material.WATER):
            self._swap(x, y, x, y + 1)
            return
        # Diagonals, random order so piles stay symmetrical.
        d = random.choice((-1, 1))
        for dx in (d, -d):
            if g.in_bounds(x + dx, y + 1) and \
               g.get(x + dx, y + 1) in (Material.EMPTY, Material.WATER):
                self._swap(x, y, x + dx, y + 1)
                return

    def _update_water(self, x: int, y: int) -> None:
        g = self.grid
        if g.get(x, y + 1) == Material.EMPTY:
            self._swap(x, y, x, y + 1)
            return
        d = random.choice((-1, 1))
        for dx in (d, -d):
            if g.in_bounds(x + dx, y + 1) and \
               g.get(x + dx, y + 1) == Material.EMPTY:
                self._swap(x, y, x + dx, y + 1)
                return
        # Sideways spread — this is what makes it read as liquid.
        if g.in_bounds(x + d, y) and g.get(x + d, y) == Material.EMPTY:
            self._swap(x, y, x + d, y)

    def _swap(self, ax: int, ay: int, bx: int, by: int) -> None:
        g = self.grid
        a = g.get(ax, ay)
        g.set(ax, ay, g.get(bx, by))
        g.set(bx, by, a)