from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger
from sc2.data import Race
from sc2.dicts.unit_research_abilities import RESEARCH_INFO
from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as UnitID
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit

from ares.behaviors.macro.macro_behavior import MacroBehavior
from ares.behaviors.macro.tech_up import TechUp
from ares.managers.manager_mediator import ManagerMediator

if TYPE_CHECKING:
    from ares import AresBot


@dataclass
class UpgradeController(MacroBehavior):
    """Drop-in replacement for ares UpgradeController.

    Fixes a bug where auto_tech_up_enabled=False caused the loop to stop
    entirely when a required building was missing, skipping all later upgrades.
    Now skips the upgrade and continues to the next one instead.
    """

    upgrade_list: list[UpgradeId]
    base_location: Point2
    auto_tech_up_enabled: bool = True
    prioritize: bool = False

    def execute(self, ai: "AresBot", config: dict, mediator: ManagerMediator) -> bool:
        for upgrade in self.upgrade_list:
            if ai.pending_or_complete_upgrade(upgrade):
                continue

            researched_from_id: UnitID = UPGRADE_RESEARCHED_FROM[upgrade]
            researched_from: list[Unit] = [
                s for s in mediator.get_own_structures_dict[researched_from_id]
            ]

            if not researched_from:
                if not self.auto_tech_up_enabled:
                    continue  # skip — building doesn't exist, move to next upgrade

                teching: bool = TechUp(
                    desired_tech=upgrade, base_location=self.base_location
                ).execute(ai, config, mediator)
                if teching:
                    return True

            else:
                idle: list[Unit] = [
                    s
                    for s in researched_from
                    if s.is_ready
                    and s.is_idle
                    and (not ai.race == Race.Protoss or s.is_powered)
                ]
                if idle:
                    building: Unit = idle[0]
                    research_info: dict = RESEARCH_INFO[researched_from_id][upgrade]
                    ability: AbilityId = research_info["ability"]
                    if ability in building.abilities:
                        if ai.can_afford(upgrade):
                            building.research(upgrade)
                            logger.info(f"{ai.time_formatted}: Researching {upgrade}")
                            return True
                        elif self.prioritize:
                            return True
                    elif required_building := research_info.get("required_building", None):
                        if not self.auto_tech_up_enabled:
                            continue  # skip — required building missing, move to next upgrade

                        return TechUp(
                            desired_tech=required_building,
                            base_location=self.base_location,
                        ).execute(ai, config, mediator)

        return False
