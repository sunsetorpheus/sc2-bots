"""Per-unit micro modules.

Each module declares the unit types it handles. plan.on_step iterates the
MICRO list each frame, filters the army to matching units, and calls run().
Add a new unit's micro by creating a file here and appending it to MICRO.
"""
from .stalker import StalkerMicro

# Order doesn't matter — each entry filters to its own unit types.
MICRO = [StalkerMicro()]
