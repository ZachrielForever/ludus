# ludus

*A desktop toybox.* Ludus is a tabbed desktop app where each tab is a small,
self-contained interactive playground — physics toys, sandboxes, simulations.
Nothing critical, nothing mission-vital. A place to play.

Latin *ludus*: "play," "game" — and the Roman school where you went to learn.
Both meanings intended.

## Why this exists

Most of my repos exist because something needed doing ([legion](https://github.com/ZachrielForever/legion),
[fleetprobe](https://github.com/ZachrielForever/fleetprobe),
[dominus-tools](https://github.com/ZachrielForever/dominus-tools)).
Ludus exists for the opposite reason: a running, evolving project with no
deadline, where the fun parts of software — simulation math, animation loops,
rendering tricks — get to be the whole point.

It is deliberately a long-running project. Toys get added when they're ready.

## Planned toys

| Toy | Concept | Status |
| --- | --- | --- |
| Falling sand | Cellular automaton sandbox — draw with materials, watch the rules interact | planned |
| Interactive buddy | Verlet ragdoll you can poke, drag, and torment with forces | planned |
| Wind tunnel | Fluid flow around user-drawn or premade shapes, with real math | planned |

Statuses will move from *planned* to *playable* as they ship. More toys join
the table as ideas accumulate.

## Architecture

The shell is a simple tabbed window. Each toy implements a small interface
(`init`, `update(dt)`, `draw`, `handle_input`) and registers itself with the
toy registry — the shell discovers toys, so adding one never means touching
another. Details will be documented as the code lands.

## Status

Scaffolding. Code is coming; the README got here first.
