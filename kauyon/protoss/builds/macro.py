from sc2.ids.unit_typeid import UnitTypeId


def macro_build() -> dict:
    # Default macro build — all economy/timing values fall back to common.py defaults.
    # Add keys here only when you want to diverge from those defaults.
    #
    # army_comp must always be set — if absent, SpawnController is never added and gates idle.
    return {
        # Pure Stalker army for now — flexible, mobile, good against all races.
        "army_comp": {
            UnitTypeId.STALKER: {"proportion": 1.0, "priority": 0},
        },
    }
