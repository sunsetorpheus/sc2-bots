import random
from sc2 import Race
from sharpy.knowledges import SkeletonBot
from sharpy.plans import BuildOrder

CHOSEN_RACE = random.choice([Race.Terran, Race.Zerg, Race.Protoss])

class SunsetOrpheus(SkeletonBot):
    def __init__(self):
        super().__init__("SunsetOrpheus")
        self.race = CHOSEN_RACE

    async def create_plan(self) -> BuildOrder:
        if self.knowledge.my_race == Race.Terran:
            return self.terran_plan()
        elif self.knowledge.my_race == Race.Zerg:
            return self.zerg_plan()
        else:
            return self.protoss_plan()

    def terran_plan(self) -> BuildOrder:
        from sharpy.plans.terran import TerranBasicPlan
        return TerranBasicPlan()

    def zerg_plan(self) -> BuildOrder:
        from sharpy.plans.zerg import ZergBasicPlan
        return ZergBasicPlan()

    def protoss_plan(self) -> BuildOrder:
        from sharpy.plans.protoss import ProtossBasicPlan
        return ProtossBasicPlan()

def run():
    from sc2.player import Bot
    return Bot(CHOSEN_RACE, SunsetOrpheus())