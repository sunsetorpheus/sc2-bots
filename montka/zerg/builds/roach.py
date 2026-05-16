from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from montka.zerg.build import Build
from montka.zerg.common import ROACH_ARMY_COMP, ROACH_UPGRADES, DRONE_MAX, ATTACK_SUPPLY

EXPAND_TO = 4


def _config() -> dict:
    return {
        "army_comp": ROACH_ARMY_COMP,
        "upgrades": ROACH_UPGRADES,
        "drone_max": DRONE_MAX,
        "attack_supply": ATTACK_SUPPLY,
        "expand_to": EXPAND_TO,
    }


build = Build(
    name="roach",
    fn=_config,
    weight=3,
    good_against=[Race.Terran, Race.Protoss],
    tags=["economic", "roach"],
)
