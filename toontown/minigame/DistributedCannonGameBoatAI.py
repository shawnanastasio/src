from toontown.safezone.DistributedBoatAI import DistributedBoatAI


class DistributedCannonGameBoatAI(DistributedBoatAI):
    def __init__(self, air):
        DistributedBoatAI.__init__(self, air)

        self.minigameId = 0

    def setMinigameId(self, minigameId):
        self.minigameId = minigameId

    def getMinigameId(self):
        return self.minigameId
