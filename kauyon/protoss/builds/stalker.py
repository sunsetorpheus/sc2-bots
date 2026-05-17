from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from kauyon.protoss.build import Build
from kauyon.protoss.common import ATTACK_SUPPLY, GATEWAY_MAX, GATEWAY_PER_BASE, PROBE_MAX

# Pure Stalker — uniform composition keeps SpawnController simple and
# benefits maximally from Blink (once researched) and ground weapon upgrades.
ARMY_COMP = {
    UnitTypeId.STALKER: {"proportion": 1.0, "priority": 0},
}

# Warp Gate first so gates convert before the army scales.
# Blink early — pairs with the StalkerMicro Blink-retreat behavior so low-HP
# Stalkers can disengage. Needs Twilight Council (in UPGRADE_STRUCTURES).
# Weapons before armor — Stalker DPS gain is higher than EHP gain at equal levels.
UPGRADES = [
    UpgradeId.WARPGATERESEARCH,
    UpgradeId.BLINKTECH,
    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1,
    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2,
    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3,
    UpgradeId.PROTOSSGROUNDARMORSLEVEL1,
    UpgradeId.PROTOSSGROUNDARMORSLEVEL2,
    UpgradeId.PROTOSSGROUNDARMORSLEVEL3,
]

# Forge unlocks ground weapons/armor L1.
# Twilight Council unlocks L2/L3 of both (and Blink, if added later).
# Both gated to "3rd Nexus ready" by plan._add_structures.
UPGRADE_STRUCTURES = [UnitTypeId.FORGE, UnitTypeId.TWILIGHTCOUNCIL]


def _config() -> dict:
    return {
        "army_comp": ARMY_COMP,
        "upgrades": UPGRADES,
        "upgrade_structures": UPGRADE_STRUCTURES,
        "gateway_per_base": GATEWAY_PER_BASE,
        "gateway_max": GATEWAY_MAX,
        "probe_max": PROBE_MAX,
        "attack_supply": ATTACK_SUPPLY,
    }



build = Build(
    name="stalker",
    fn=_config,
    weight=3,
    good_against=[Race.Terran, Race.Zerg],
    tags=["gateway"],
)
