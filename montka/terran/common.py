from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

SCV_MAX = 70
ATTACK_SUPPLY = 26

BIO_ARMY_COMP = {
    UnitTypeId.MARINE: {"proportion": 0.5, "priority": 1},
    UnitTypeId.MARAUDER: {"proportion": 0.35, "priority": 0},
    UnitTypeId.MEDIVAC: {"proportion": 0.15, "priority": 2},
}

BIO_UPGRADES = [
    UpgradeId.STIMPACK,
    UpgradeId.SHIELDWALL,
    UpgradeId.PUNISHERGRENADES,
    UpgradeId.TERRANINFANTRYWEAPONSLEVEL1,
    UpgradeId.TERRANINFANTRYWEAPONSLEVEL2,
    UpgradeId.TERRANINFANTRYWEAPONSLEVEL3,
    UpgradeId.TERRANINFANTRYARMORSLEVEL1,
    UpgradeId.TERRANINFANTRYARMORSLEVEL2,
    UpgradeId.TERRANINFANTRYARMORSLEVEL3,
]
