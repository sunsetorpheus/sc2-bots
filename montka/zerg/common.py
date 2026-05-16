from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

DRONE_MAX = 70
ATTACK_SUPPLY = 120

ROACH_ARMY_COMP = {
    UnitTypeId.ROACH: {"proportion": 0.7, "priority": 0},
    UnitTypeId.RAVAGER: {"proportion": 0.2, "priority": 1},
    UnitTypeId.ZERGLING: {"proportion": 0.1, "priority": 2},
}

ROACH_UPGRADES = [
    UpgradeId.GLIALRECONSTITUTION,
    UpgradeId.ZERGMISSILEWEAPONSLEVEL1,
    UpgradeId.ZERGGROUNDARMORSLEVEL1,
    UpgradeId.ZERGMISSILEWEAPONSLEVEL2,
    UpgradeId.ZERGGROUNDARMORSLEVEL2,
    UpgradeId.ZERGMISSILEWEAPONSLEVEL3,
    UpgradeId.ZERGGROUNDARMORSLEVEL3,
]
