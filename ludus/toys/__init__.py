"""Importing toy modules triggers @toy registration."""

from ludus.registry import toy  # noqa: F401
from ludus.toys.placeholder import (  # noqa: F401
    BuddyToy,
    WindTunnelToy,
    TbdToy,
)
from ludus.toys.sand import SandToy  # noqa: F401

# Seven reserved slots, claimed until real toys earn them.
for _ in range(7):
    toy(type("TbdSlot", (TbdToy,), {}))