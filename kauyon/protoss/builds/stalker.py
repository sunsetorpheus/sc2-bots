from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId


def stalker_build() -> dict:
    return {
        # Pure Stalker army — good against all races.
        "army_comp": {
            UnitTypeId.STALKER: {"proportion": 1.0, "priority": 0},
        },
        # Blink is essential for Stalker micro — added on top of default weapon/armor upgrades.
        "upgrades": [UpgradeId.BLINKTECH],
    }
