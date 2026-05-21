from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from kauyon.protoss.common import BUILD_STEPS


def macro_build() -> dict:
    # Default macro build — all economy/timing values fall back to common.py defaults.
    # Add keys here only when you want to diverge from those defaults.
    #
    # army_comp must always be set — if absent, SpawnController is never added and gates idle.
    return {
        # Observer (count=1) and Sentry (count=2) are built first as fixed-count support units.
        # Stalkers fill the rest via proportion — they use SpawnController's normal warp-in logic.
        "army_comp": {
            UnitTypeId.OBSERVER: {"count": 1, "priority": 0},
            UnitTypeId.SENTRY:   {"count": 2, "priority": 1},
            UnitTypeId.STALKER:  {"proportion": 1.0, "priority": 2},
        },
        # Blink is essential for Stalker micro — requires Twilight Council.
        "upgrades": [UpgradeId.BLINKTECH],
        # Add a Robotics Facility at 2 bases so Observers can be produced.
        "build_steps": {
            **BUILD_STEPS,
            2: [*BUILD_STEPS.get(2, []), (UnitTypeId.ROBOTICSFACILITY, 1)],
        },
    }
