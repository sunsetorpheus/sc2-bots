"""
Reference build — NOT registered in BUILDS, so it never runs in a game.

Copy this file to a real build (e.g. `stalker_allin.py`) and:
  1. Edit the values you want to differ from the defaults.
  2. Delete keys you DON'T need to change — omitted keys fall back to
     common.py defaults automatically.
  3. Register the build in __init__.py by adding it to BUILDS.

Every key listed below is optional except `army_comp`, `upgrades`, and
`upgrade_structures` (which default to empty and would produce no army).
The default value for each is shown next to it.
"""
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from kauyon.protoss.build import Build
from kauyon.protoss.common import (
    ATTACK_ABORT_ENEMY_COUNT,
    ATTACK_ABORT_SUPPLY_RATIO,
    ATTACK_SUPPLY,
    EXPAND_AT_HARVESTERS,
    EXPAND_MAX,
    EXPAND_SAVE_MINERALS,
    GAS_AT_HARVESTERS,
    GATEWAY_MAX,
    GATEWAY_PER_BASE,
    MAX_PENDING_NEXUS,
    OPENERS,
    PRE_THIRD_GATEWAY_CAP,
    PROBE_MAX,
)


def _config() -> dict:
    return {
        # ---------------------------------------------------------------
        # Required-ish: what to make and what to research.
        # Omit these and the bot will mine but build no army.
        # ---------------------------------------------------------------

        # Unit composition. SpawnController reads this every frame.
        # proportion: relative share of supply. priority: lower = built first.
        "army_comp": {
            UnitTypeId.STALKER: {"proportion": 1.0, "priority": 0},
        },

        # Upgrades, researched in list order. UpgradeController walks through
        # them; it won't tech up on its own (auto_tech_up is off), so make
        # sure upgrade_structures provides the buildings these need.
        "upgrades": [
            UpgradeId.WARPGATERESEARCH,
            UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1,
        ],

        # Tech buildings to queue once the 3rd Nexus is COMPLETE.
        # Forge unlocks ground weapons/armor L1. Twilight Council unlocks
        # L2/L3 (plus Blink, Charge). Robotics Bay unlocks Colossus range.
        "upgrade_structures": [
            UnitTypeId.FORGE,
        ],

        # ---------------------------------------------------------------
        # Opener.
        # ---------------------------------------------------------------

        # Ordered list of structures to build first. Each step waits for
        # the previous to exist (or be pending) before starting. Once
        # every structure in the list is present, engine logic takes over
        # (gateway scaling, upgrade structures, etc).
        # Default: standard macro Protoss opener (Pylon → Gateway → Cyber).
        # Cannon rush: [PYLON, FORGE, PHOTONCANNON]
        # Pure Zealot: [PYLON, GATEWAY]  (skip Cyber, no Stalker tech)
        # Tech-focused: [PYLON, GATEWAY, CYBERNETICSCORE, ROBOTICSFACILITY]
        "openers": OPENERS,

        # ---------------------------------------------------------------
        # Production caps.
        # ---------------------------------------------------------------

        # Worker hard cap. Default: PROBE_MAX = 75.
        # Cheese build: 25. Mega-macro: 80.
        "probe_max": PROBE_MAX,

        # Hard base cap. Default: EXPAND_MAX = 99 (effectively unlimited).
        # All-in: 2. Map-aware: 4.
        "expand_max": EXPAND_MAX,

        # Gateways per ready base, capped at gateway_max. Default: 4.
        # Robo-heavy: 2. Pure gateway: 5.
        "gateway_per_base": GATEWAY_PER_BASE,

        # Hard gateway cap. Default: 16.
        # Tech build: 8. Mass-gate: 20.
        "gateway_max": GATEWAY_MAX,

        # Gateway cap BEFORE the 3rd Nexus completes. Default: 3.
        # 2-base all-in: 5 or 6. Tech-rush: 2.
        "pre_third_gateway_cap": PRE_THIRD_GATEWAY_CAP,

        # ---------------------------------------------------------------
        # Expansion timing.
        # ---------------------------------------------------------------

        # Bump desired base count once any Nexus has at least this many
        # assigned harvesters. Default: 14 (≈6 workers before full
        # saturation). Greedy: 10. Defensive: 18.
        "expand_at_harvesters": EXPAND_AT_HARVESTERS,

        # Number of Nexuses that may be building simultaneously. Default: 1.
        # Macro on safe maps: 2 (double-expand).
        "max_pending_nexus": MAX_PENDING_NEXUS,

        # While saving for a Nexus, halt army/structure spending only when
        # minerals are below this. Above it, both can run. Default: 525
        # (= 400 Nexus + 125 Stalker headroom). Lower forces a harder save.
        "expand_save_minerals": EXPAND_SAVE_MINERALS,

        # ---------------------------------------------------------------
        # Gas timing.
        # ---------------------------------------------------------------

        # Non-main bases build assimilators once they reach this many
        # assigned harvesters. Default: 4 (early gas for Stalker production).
        # Gas-hungry comp (storm, voidray): 2. Mineral-heavy (zealot): 8.
        "gas_at_harvesters": GAS_AT_HARVESTERS,

        # ---------------------------------------------------------------
        # Attack timing.
        # ---------------------------------------------------------------

        # Supply needed before the first attack wave. Default: 100.
        # All-in: 40-60. Mega-macro: 150-180.
        "attack_supply": ATTACK_SUPPLY,

        # Abort the push and retreat home when army_supply drops below
        # attack_supply * this ratio. Default: 0.10 (retreat at 10%).
        # All-in / commit: 0.0 (never retreat).
        "attack_abort_supply_ratio": ATTACK_ABORT_SUPPLY_RATIO,

        # Abort the push when this many enemy units are near a townhall.
        # Default: 5. Commit-to-push builds: 999 (disable).
        "attack_abort_enemy_count": ATTACK_ABORT_ENEMY_COUNT,
    }


# NOTE: This build is NOT added to BUILDS in __init__.py, so it won't be
# selected during a game. It exists purely as a reference template.
build = Build(
    name="_example",
    fn=_config,
    weight=0,
    good_against=[Race.Terran, Race.Zerg, Race.Protoss],
    tags=["reference"],
)
