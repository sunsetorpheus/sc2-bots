from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sc2.units import Units

from montka.protoss.micro.base import UnitMicro


# Blink when HP + shields drop below this fraction of max HP + shields.
_BLINK_THRESHOLD = 0.5


class StalkerMicro:
    unit_types = {UnitTypeId.STALKER}

    def run(self, plan, units: Units) -> None:
        ai = plan.ai

        # Only use Blink if it has been fully researched.
        blink_ready = ai.already_pending_upgrade(UpgradeId.BLINKTECH) == 1

        for stalker in units:
            if blink_ready and self._should_blink(stalker):
                self._blink_away(ai, stalker)

    def _should_blink(self, stalker: Unit) -> bool:
        # Trigger blink when combined HP + shields fall below 50% of max.
        max_health = stalker.health_max + stalker.shield_max
        current_health = stalker.health + stalker.shield
        if max_health == 0:
            return False
        return (current_health / max_health) < _BLINK_THRESHOLD

    def _blink_away(self, ai, stalker: Unit) -> None:
        # Blink away from the closest enemy unit — puts distance between the
        # stalker and its attacker so shields can regenerate before re-engaging.
        if not ai.enemy_units:
            return

        # Only blink if the ability is actually available (not on cooldown).
        if AbilityId.EFFECT_BLINK_STALKER not in stalker.abilities:
            return

        closest_enemy = ai.enemy_units.closest_to(stalker)
        # Blink to a point directly away from the closest enemy.
        blink_target = stalker.position.towards(closest_enemy.position, -8)
        stalker(AbilityId.EFFECT_BLINK_STALKER, blink_target)


# Satisfy the UnitMicro protocol check.
_: UnitMicro = StalkerMicro()
