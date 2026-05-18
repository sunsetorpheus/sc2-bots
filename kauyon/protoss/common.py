from sc2.ids.unit_typeid import UnitTypeId

# Maximum number of probes to maintain across all bases.
# Kau'yon keeps expanding throughout the game but caps probe production at this number.
PROBE_MAX = 75

# Harvester count on a base that triggers both the next expansion and gas at that base.
# 14 means once a base has 14 mineral workers, take the next base and build its gases.
# Build files can override "expand_at_harvesters" in config.
EXPAND_AT_HARVESTERS = 14

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

# Number of Gateways to build per committed base.
# 2 per base is the standard macro-efficient ratio for a Protoss economy-first style.
# Build files can override "gateway_per_base" in config.
GATEWAY_PER_BASE = 2

# Hard cap on total Gateways regardless of base count.
# Build files can override "gateway_max" in config.
GATEWAY_MAX = 16

# Minimum Nexus energy before firing Chrono Boost.
# Holding to 75 avoids wasting energy on a nearly-finished job.
# Build files can override "chrono_energy_threshold" in config.
CHRONO_ENERGY_THRESHOLD = 75

# Default opener sequence: the structures to build at the start of the game, in order.
# Each entry is checked in sequence — if the structure doesn't exist yet, build it and stop.
# Build files can override "opener" in config to use a different sequence entirely.
DEFAULT_OPENER = [
    UnitTypeId.PYLON,           # must come first for supply
    UnitTypeId.GATEWAY,         # required for unit production
    UnitTypeId.CYBERNETICSCORE, # required for Stalkers, Warpgate, and upgrades
]
