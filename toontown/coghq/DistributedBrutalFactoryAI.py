from toontown.coghq.DistributedFactoryAI import DistributedFactoryAI
from toontown.toon import NPCToons

import random


class DistributedBrutalFactoryAI(DistributedFactoryAI):
    notify = directNotify.newCategory('DistributedBrutalFactoryAI')

    POSSIBLE_SOS = NPCToons.npcFriendsMinMaxStars(3, 3)

    def setVictors(self, victorIds):
        DistributedFactoryAI.setVictors(self, victorIds)

        activeVictors = [self.air.doId2do.get(victorId) for victorId in victorIds if self.air.doId2do.get(victorId) is not None]
        
        npcId = random.choice(self.POSSIBLE_SOS)
        npcName = NPCToons.getNPCName(npcId)
        
        for victor in activeVictors:
            victor.attemptAddNPCFriend(npcId)
            victor.d_setSystemMessage(0, 'You got a %s SOS card.' % npcName)
