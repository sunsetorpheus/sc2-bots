from sc2.position import Point2
from sc2.units import Units

from kauyon.protoss.common import ATTACK_SUPPLY, RETREAT_RATIO

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

        if not self._attacking:
            if army_supply >= attack_supply:
                # Reached critical mass — move out.
                self._attacking = True
            else:
                # Hold at the rally point between the two most recent expansions.
                rally = self._rally_point(home, enemy)
                for unit in army:
                    if unit.distance_to(rally) > 5:
                        unit.move(rally)
        else:
            if army_supply < attack_supply * retreat_ratio:
                # Army wiped below retreat threshold — fall back and rebuild.
                self._attacking = False
                self._scan_index = 0
                for unit in army:
                    unit.move(home)
            else:
                self._push(army, enemy)

    def _push(self, army: Units, enemy: Point2) -> None:
        # Attack nearest visible enemy structure first — this handles cases where
        # the enemy has expanded or moved base.
        enemy_structures = self.ai.enemy_structures
        if enemy_structures:
            target = enemy_structures.closest_to(army.center)
            for unit in army:
                unit.attack(target)
            return

        # No visible enemy structures — scan expansion locations across the map
        # in order (enemy-side first) until a base is found.
        if self._scan_locations:
            target = self._scan_locations[self._scan_index]
            army_center = army.center

            # If army has arrived at current scan location, advance to the next one.
            if army_center.distance_to(target) < _SCAN_ARRIVAL_DISTANCE:
                self._scan_index = (self._scan_index + 1) % len(self._scan_locations)
                target = self._scan_locations[self._scan_index]

            for unit in army:
                unit.attack(target)
            return

        # Fallback — no scan locations available, push toward enemy start.
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
