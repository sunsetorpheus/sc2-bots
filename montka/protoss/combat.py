from sc2.position import Point2
from sc2.units import Units

from montka.protoss.common import ATTACK_SUPPLY, RETREAT_RATIO

# How close the army needs to be to a scan target before moving to the next one.
_SCAN_ARRIVAL_DISTANCE = 10


class Combat:
    def __init__(self, ai, config: dict):
        self.ai = ai
        self.config = config
        self._attacking: bool = False
        # Index into the sorted expansion locations list used when scanning for
        # the enemy after their main base is destroyed.
        self._scan_index: int = 0
        # Expansion locations sorted from enemy start outward — checked enemy-side first.
        self._scan_locations: list[Point2] = []
        self._was_rallying: bool = False

    def on_step(self) -> None:
        army_comp: dict = self.config.get("army_comp", {})
        if not army_comp:
            return

        # Gather all ready army units defined in the build's army composition.
        army: Units = self.ai.units(set(army_comp.keys())).ready
        if not army:
            return

        attack_supply: int = self.config.get("attack_supply", ATTACK_SUPPLY)
        retreat_ratio: float = self.config.get("retreat_ratio", RETREAT_RATIO)
        home: Point2 = self.ai.start_location
        enemy: Point2 = self.ai.enemy_start_locations[0]

        # Build scan locations once — all map expansion spots sorted by distance
        # from enemy start so the army checks enemy-side locations first.
        if not self._scan_locations:
            self._scan_locations = sorted(
                self.ai.expansion_locations_list,
                key=lambda p: p.distance_to(enemy),
            )

        self._handle_attack(army, home, enemy, attack_supply, retreat_ratio)

    def _handle_attack(self, army: Units, home: Point2, enemy: Point2, attack_supply: int, retreat_ratio: float) -> None:
        army_supply: float = self.ai.supply_army
        retreat_threshold = attack_supply * retreat_ratio

        if not self._attacking:
            if army_supply >= attack_supply:
                self._attacking = True
                self._was_rallying = False
            else:
                # Skip rally moves while defense is actively handling a base threat —
                # both systems commanding the same units each step causes back-and-forth.
                base_threats = self.ai.enemy_units.filter(
                    lambda u: not u.is_structure
                    and not u.is_mineral_field
                    and not u.is_vespene_geyser
                    and any(u.distance_to(th) < 30 for th in self.ai.townhalls)
                )
                if base_threats:
                    self._was_rallying = False
                    return

                rally = self._rally_point(home, enemy)
                moving = [u for u in army if u.distance_to(rally) > 5]
                self._was_rallying = bool(moving)
                for unit in moving:
                    unit.move(rally)
        else:
            if army_supply < retreat_threshold:
                self._attacking = False
                self._scan_index = 0
                for unit in army:
                    unit.move(home)
            else:
                self._attack(army, enemy)

    def _attack(self, army: Units, enemy: Point2) -> None:
        # Attack-move toward the nearest attackable threat — filter out units the
        # army can detect but not attack (e.g. cloaked Observers). Without this,
        # the army chases unattackable units indefinitely.
        attackable_enemies = self.ai.enemy_units.filter(lambda u: u.can_be_attacked)
        if attackable_enemies or self.ai.enemy_structures:
            target = (
                attackable_enemies.closest_to(army.center)
                if attackable_enemies
                else self.ai.enemy_structures.closest_to(army.center)
            )
            for unit in army:
                unit.attack(target.position)
            return

        # No visible enemies — scan expansion locations enemy-side first, skipping
        # locations the army has already visited and found empty. Once all locations
        # are exhausted, fall back to the enemy start so the army doesn't idle.
        if self._scan_locations:
            checked = 0
            while checked < len(self._scan_locations):
                target = self._scan_locations[self._scan_index]
                arrived = army.center.distance_to(target) < _SCAN_ARRIVAL_DISTANCE
                # A location counts as cleared if the army is there and no enemy
                # structures or units are visible within scan arrival distance.
                enemies_nearby = (
                    self.ai.enemy_units.closer_than(_SCAN_ARRIVAL_DISTANCE, target)
                    or self.ai.enemy_structures.closer_than(_SCAN_ARRIVAL_DISTANCE, target)
                )
                if arrived and not enemies_nearby:
                    # Location confirmed empty — advance and try the next one.
                    self._scan_index = (self._scan_index + 1) % len(self._scan_locations)
                    checked += 1
                    continue
                # Either not arrived yet or enemies are present — move here.
                for unit in army:
                    unit.attack(target)
                return

        # All scan locations exhausted with no enemies found — attack enemy start.
        for unit in army:
            unit.attack(enemy)

    def _rally_point(self, home: Point2, enemy: Point2) -> Point2:
        # Rally at the midpoint of the two most recent expansions, nudged toward
        # the enemy. Most recent = furthest from home in a standard expansion path.
        # Falls back to 15 units toward enemy if no bases exist yet.
        all_bases = list(self.ai.townhalls)
        if not all_bases:
            return home.towards(enemy, 15)

        frontier = sorted(all_bases, key=lambda th: th.distance_to(home), reverse=True)[:2]
        cx = sum(th.position.x for th in frontier) / len(frontier)
        cy = sum(th.position.y for th in frontier) / len(frontier)

        # Nudge toward enemy so army doesn't sit inside the base.
        return Point2((cx, cy)).towards(enemy, 8)
