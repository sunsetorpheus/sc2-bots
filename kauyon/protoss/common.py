from sc2.ids.unit_typeid import UnitTypeId

# Maximum number of probes to maintain across all bases.
# Kau'yon keeps expanding throughout the game but caps probe production at this number.
PROBE_MAX = 85

# Harvester count on a base that triggers the next expansion.
# Build files can override "expand_at_harvesters" in config.
EXPAND_AT_HARVESTERS = 16

# Hard cap on total bases regardless of saturation.
# Build files can override "expand_max" in config.
EXPAND_MAX = 8

# Radius around a Nexus to check for friendly units/structures under attack.
# Build files can override "defense_radius" in config.
DEFENSE_RADIUS = 20

# Maximum Photon Cannons to build per base when under attack. Requires a Forge.
# Build files can override "max_cannons_per_base" in config.
MAX_CANNONS_PER_BASE = 2

# Maximum Shield Batteries to build per base when under attack. Requires a Gateway.
# Build files can override "max_batteries_per_base" in config.
MAX_BATTERIES_PER_BASE = 1

# Army supply threshold to trigger an attack push.
# Bot rallies until this supply is reached, then moves out.
# Build files can override "attack_supply" in config.
ATTACK_SUPPLY = 100

# Fraction of attack supply below which the army retreats home.
# 0.3 = retreat if army drops below 30% of ATTACK_SUPPLY.
# Build files can override "retreat_ratio" in config.
RETREAT_RATIO = 0.3

# Structures to build at each committed base count.
# Keys are base counts; values are lists of (UnitTypeId, count) to reach by that base count.
# All entries for a given base count must be satisfied before the next base count's entries apply.
# Build files can override "build_steps" in config.
BUILD_STEPS = {
    1: [(UnitTypeId.GATEWAY, 1)],
    2: [(UnitTypeId.GATEWAY, 2)],
    3: [(UnitTypeId.FORGE, 2), (UnitTypeId.TWILIGHTCOUNCIL, 1)],
}

# Hard cap on total Gateways regardless of base count.
# Build files can override "gateway_max" in config.
GATEWAY_MAX = 12

# Minimum Nexus energy before firing Chrono Boost.
# Holding to 75 avoids wasting energy on a nearly-finished job.
# Build files can override "chrono_energy_threshold" in config.
CHRONO_ENERGY_THRESHOLD = 50

# Default opener sequence: the structures to build at the start of the game, in order.
# Each entry is a (UnitTypeId, count) tuple — the opener waits until that many of the
# structure exist before moving to the next step.
# Use UnitTypeId.NEXUS as a sentinel to trigger a natural expansion at that point.
# Build files can override "opener" in config to use a different sequence entirely.
DEFAULT_OPENER = [
    (UnitTypeId.PYLON, 1),              # must come first for supply
    (UnitTypeId.GATEWAY, 1),            # required for unit production
    (UnitTypeId.ASSIMILATOR, 1),        # first gas — flows before natural is committed
    (UnitTypeId.NEXUS, 2),              # natural expansion
    (UnitTypeId.CYBERNETICSCORE, 1),    # required for Stalkers, Warpgate, and upgrades
    (UnitTypeId.ASSIMILATOR, 2),        # second gas — after natural is started
]
