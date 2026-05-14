import random
from sc2.data import Race
from sharpy.knowledges import KnowledgeBot
from sharpy.plans import BuildOrder

CHOSEN_RACE = random.choice([Race.Terran, Race.Zerg, Race.Protoss])

class Montka(KnowledgeBot):
    def __init__(self):
        super().__init__("Mon'tka")
        self.race = CHOSEN_RACE

    async def create_plan(self) -> BuildOrder:
        if self.knowledge.my_race == Race.Terran:
            from montka.terran.plan import terran_plan
            return terran_plan(self.knowledge.enemy_race)
        elif self.knowledge.my_race == Race.Zerg:
            from montka.zerg.plan import zerg_plan
            return zerg_plan(self.knowledge.enemy_race)
        else:
            from montka.protoss.plan import protoss_plan
            return protoss_plan(self.knowledge.enemy_race)

def run():
    from sc2.player import Bot
    return Bot(CHOSEN_RACE, Montka())
