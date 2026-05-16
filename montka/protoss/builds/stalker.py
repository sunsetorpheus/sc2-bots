from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from montka.protoss.build import Build

ARMY_COMP = {
    UnitTypeId.STALKER: {"proportion": 1.0, "priority": 0},
}

UPGRADES = [
    UpgradeId.WARPGATERESEARCH,
    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1,
    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2,
    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3,
    UpgradeId.PROTOSSGROUNDARMORSLEVEL1,
    UpgradeId.PROTOSSGROUNDARMORSLEVEL2,
    UpgradeId.PROTOSSGROUNDARMORSLEVEL3,
]

GATEWAY_TARGET = 8
PROBE_MAX = 75
ATTACK_SUPPLY = 190
EXPAND_TO = 3


def _config() -> dict:
    return {
        "army_comp": ARMY_COMP,
        "upgrades": UPGRADES,
        "gateway_target": GATEWAY_TARGET,
        "probe_max": PROBE_MAX,
        "attack_supply": ATTACK_SUPPLY,
        "expand_to": EXPAND_TO,
    }


build = Build(
    name="stalker",
    fn=_config,
    weight=3,
    good_against=[Race.Terran, Race.Zerg],
    tags=["gateway"],
)
