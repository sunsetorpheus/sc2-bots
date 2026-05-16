from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from montka.terran.build import Build
from montka.terran.common import BIO_ARMY_COMP, BIO_UPGRADES, SCV_MAX, ATTACK_SUPPLY

BARRACKS_TARGET = 5
EXPAND_TO = 3


def _config() -> dict:
    return {
        "army_comp": BIO_ARMY_COMP,
        "upgrades": BIO_UPGRADES,
        "barracks_target": BARRACKS_TARGET,
        "scv_max": SCV_MAX,
        "attack_supply": ATTACK_SUPPLY,
        "expand_to": EXPAND_TO,
    }


build = Build(
    name="bio",
    fn=_config,
    weight=3,
    good_against=[Race.Zerg, Race.Protoss],
    tags=["aggressive", "bio"],
)
