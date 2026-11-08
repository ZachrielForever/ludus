"""Toy registry.

Toys are discovered, never hand-wired. A toy is any PySide6 QWidget
subclass decorated with @toy, providing:
  TITLE          — str, shown on the tab label
  update_step(dt) — called ~60x/sec while its tab is visible
"""

_registry = []


def toy(cls):
    """Class decorator: register this widget as a toy."""
    _registry.append(cls)
    return cls


def all_toys():
    return list(_registry)