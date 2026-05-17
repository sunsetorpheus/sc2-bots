from typing import TYPE_CHECKING

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units

from ares.behaviors.combat.individual import UseAbility

from kauyon.protoss.common import BLINK_RETREAT_HEALTH_PCT

if TYPE_CHECKING:
    from kauyon.protoss.plan import ProtossPlan


class StalkerMicro:
    """Stalker-specific micro.

    Currently: Blink retreat. When a Stalker's combined HP+shield ratio
    falls below blink_retreat_health_pct AND its position is unsafe AND
    Blink is off cooldown, blink to the nearest safe spot.

    Blink availability is gated by `AbilityId.EFFECT_BLINK_STALKER in
    unit.abilities`, which ares' UseAbility also double-checks — so this
    is a no-op until Blink is researched.

    Threshold of 0.0 (or anything that no unit reaches) effectively
    disables the behavior.
    """

    unit_types = {UnitTypeId.STALKER}

    def run(self, plan: "ProtossPlan", units: Units) -> None:
        threshold: float = plan._config.get("blink_retreat_health_pct", BLINK_RETREAT_HEALTH_PCT)
        if threshold <= 0.0:
            return

        ai = plan.ai
        grid = ai.mediator.get_ground_grid

        for stalker in units:
            if not self._needs_blink_retreat(stalker, threshold, ai, grid):
                continue
            safe_spot = ai.mediator.find_closest_safe_spot(
                from_pos=stalker.position, grid=grid
            )
            ai.register_behavior(UseAbility(
                ability=AbilityId.EFFECT_BLINK_STALKER,
                unit=stalker,
                target=safe_spot,
            ))

    @staticmethod
    def _needs_blink_retreat(unit: Unit, threshold: float, ai, grid) -> bool:
        # `unit.abilities` already reflects research + cooldown state.
        if AbilityId.EFFECT_BLINK_STALKER not in unit.abilities:
            return False
        ratio = (unit.health + unit.shield) / (unit.health_max + unit.shield_max)
        if ratio > threshold:
            return False
        return not ai.mediator.is_position_safe(grid=grid, position=unit.position)
