from toontown.minigame.DistributedCannonGameBoatAI import DistributedCannonGameBoatAI
from DistributedMinigameAI import *
from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.task import Task
import CannonGameGlobals


class DistributedCannonGameAI(DistributedMinigameAI):
    def __init__(self, air, minigameId):
        DistributedMinigameAI.__init__(self, air, minigameId)

        self.gameFSM = ClassicFSM.ClassicFSM('DistributedCannonGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['play']), State.State('play', self.enterPlay, self.exitPlay, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
        self.addChildGameFSM(self.gameFSM)
        self.boat = DistributedCannonGameBoatAI(self.air)

    def delete(self):
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    def setGameReady(self):
        DistributedMinigameAI.setGameReady(self)

        self.boat.setMinigameId(self.doId)
        self.boat.generateWithRequired(self.zoneId)
        self.boat.start()

    def setGameStart(self, timestamp):
        DistributedMinigameAI.setGameStart(self, timestamp)

        self.gameFSM.request('play')

    def setGameAbort(self):
        if self.gameFSM.getCurrentState():
            self.gameFSM.request('cleanup')

        DistributedMinigameAI.setGameAbort(self)

    def gameOver(self):
        self.gameFSM.request('cleanup')

        DistributedMinigameAI.gameOver(self)

    def enterInactive(self):
        pass

    def exitInactive(self):
        pass

    def enterPlay(self):
        if not config.GetBool('endless-cannon-game', 0):
            taskMgr.doMethodLater(CannonGameGlobals.GameTime, self.timerExpired, self.taskName('gameTimer'))

    def timerExpired(self, task):
        self.gameOver()
        return Task.done

    def __playing(self):
        if not hasattr(self, 'gameFSM'):
            return False
        if self.gameFSM.getCurrentState() == None:
            return False
        return self.gameFSM.getCurrentState().getName() == 'play'

    def _checkCannonRange(self, zRot, angle, avId):
        outOfRange = 0
        if zRot < CannonGameGlobals.CANNON_ROTATION_MIN or zRot > CannonGameGlobals.CANNON_ROTATION_MAX:
            self.air.writeServerEvent('suspicious', avId, 'Cannon game z-rotation out of range: %s' % zRot)
            self.notify.warning('av %s cannon z-rotation out of range: %s' % (avId, zRot))
            outOfRange = 1
        if angle < CannonGameGlobals.CANNON_ANGLE_MIN or angle > CannonGameGlobals.CANNON_ANGLE_MAX:
            self.air.writeServerEvent('suspicious', avId, 'Cannon game vertical angle out of range: %s' % angle)
            self.notify.warning('av %s cannon vertical angle out of range: %s' % (avId, angle))
            outOfRange = 1
        return outOfRange

    def setCannonPosition(self, zRot, angle):
        if not self.__playing():
            self.notify.debug('ignoring setCannonPosition message')
            return
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('setCannonPosition: ' + str(avId) + ': zRot=' + str(zRot) + ', angle=' + str(angle))
        if self._checkCannonRange(zRot, angle, avId):
            return
        self.sendUpdate('updateCannonPosition', [avId, zRot, angle])

    def setCannonLit(self, zRot, angle):
        if not self.__playing():
            self.notify.debug('ignoring setCannonLit message')
            return
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('setCannonLit: ' + str(avId) + ': zRot=' + str(zRot) + ', angle=' + str(angle))
        if self._checkCannonRange(zRot, angle, avId):
            return
        fireTime = self.getCurrentGameTime() + CannonGameGlobals.FUSE_TIME
        self.sendUpdate('setCannonWillFire', [avId,
         fireTime,
         zRot,
         angle])

    def setToonWillLandInWater(self, landTime):
        if not self.__playing():
            self.notify.debug('ignoring setToonWillLandInWater message')
            return
        senderAvId = self.air.getAvatarIdFromSender()
        score = CannonGameGlobals.calcScore(landTime)
        for avId in self.avIdList:
            self.scoreDict[avId] = score

        self.notify.debug('setToonWillLandInWater: time=%s, score=%s' % (landTime, score))
        taskMgr.remove(self.taskName('gameTimer'))
        delay = max(0, landTime - self.getCurrentGameTime())
        taskMgr.doMethodLater(delay, self.toonLandedInWater, self.taskName('game-over'))
        self.sendUpdate('announceToonWillLandInWater', [senderAvId, landTime])

    def toonLandedInWater(self, task):
        self.notify.debug('toonLandedInWater')
        if self.__playing():
            self.gameOver()
        return Task.done

    def exitPlay(self):
        taskMgr.remove(self.taskName('gameTimer'))
        taskMgr.remove(self.taskName('game-over'))

    def enterCleanup(self):
        self.gameFSM.request('inactive')
        self.boat.requestDelete()

    def exitCleanup(self):
        pass
