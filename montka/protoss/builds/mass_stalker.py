from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId


def mass_stalker_build() -> dict:
    # Mont'ka aggressive Stalker build — same unit comp as Kau'yon but no Observer/Sentry.
    # Attacks earlier at lower supply with no Robo tech detour.
    return {
        # Pure Stalker army — no support units to delay the attack wave.
        "army_comp": {
            UnitTypeId.STALKER: {"proportion": 1.0, "priority": 0},
        },
        # Blink is essential for Stalker micro — requires Twilight Council.
        "upgrades": [UpgradeId.BLINKTECH],
        # Twilight Council at 2 bases unlocks Blink research.
        "build_steps": {
            1: [(UnitTypeId.GATEWAY, 1)],
            2: [(UnitTypeId.GATEWAY, 4), (UnitTypeId.TWILIGHTCOUNCIL, 1)],
        },
    }
