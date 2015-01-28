from pandac.PandaModules import *
from direct.distributed.DistributedObject import DistributedObject
from direct.interval.IntervalGlobal import *

from toontown.safezone.DistributedBoat import DistributedBoat


class DistributedCannonGameBoat(DistributedBoat):
    def __init__(self, cr):
        DistributedBoat.__init__(self, cr)

        self.minigame = None
        self.tower = loader.loadModel('phase_4/models/minigames/toon_cannon_water_tower')
        self.tower.setScale(0.3)

    def generate(self):
        DistributedObject.generate(self)

    def delete(self):
        DistributedBoat.delete(self)

        self.tower.removeNode()

    def setupTracks(self):
        self.boat.unstash()

        dockSound = base.loadSfx('phase_6/audio/sfx/SZ_DD_dockcreak.ogg')
        foghornSound = base.loadSfx('phase_5/audio/sfx/SZ_DD_foghorn.ogg')
        bellSound = base.loadSfx('phase_6/audio/sfx/SZ_DD_shipbell.ogg')

        self.eastWestMopath.loadFile('phase_6/paths/dd-e-w')
        self.eastWestMopathInterval = MopathInterval(self.eastWestMopath, self.boat)

        ewBoatTrack = ParallelEndTogether(
            Parallel(self.eastWestMopathInterval, SoundInterval(bellSound, node=self.boat)),
            SoundInterval(foghornSound, node=self.boat), name='ew-boat')

        self.westEastMopath.loadFile('phase_6/paths/dd-w-e')
        self.westEastMopathInterval = MopathInterval(self.westEastMopath, self.boat)

        weBoatTrack = ParallelEndTogether(
            Parallel(self.westEastMopathInterval, SoundInterval(bellSound, node=self.boat)),
            SoundInterval(foghornSound, node=self.boat), name='we-boat')

        eastPier = self.minigame.ground.find('**/east_pier')
        ePierHpr = VBase3(90, -44.2601, 0)
        ePierTargetHpr = VBase3(90, 0.25, 0)
        westPier = self.minigame.ground.find('**/west_pier')
        wPierHpr = VBase3(-90, -44.2601, 0)
        wPierTargetHpr = VBase3(-90, 0.25, 0)

        ePierDownTrack = Parallel(LerpHprInterval(eastPier, self.PIER_TIME, ePierHpr, ePierTargetHpr),
                                  SoundInterval(dockSound, node=eastPier), name='e-pier-down')
        ePierUpTrack = Parallel(LerpHprInterval(eastPier, self.PIER_TIME, ePierTargetHpr, ePierHpr),
                                SoundInterval(dockSound, node=eastPier), name='e-pier-up')
        wPierDownTrack = Parallel(LerpHprInterval(westPier, self.PIER_TIME, wPierHpr, wPierTargetHpr),
                                  SoundInterval(dockSound, node=westPier), name='w-pier-down')
        wPierUpTrack = Parallel(LerpHprInterval(westPier, self.PIER_TIME, wPierTargetHpr, wPierHpr),
                                SoundInterval(dockSound, node=westPier), name='w-pier-up')

        self.ewTrack = ParallelEndTogether(Parallel(ewBoatTrack, ePierDownTrack), wPierUpTrack, name='ew-track')
        self.weTrack = ParallelEndTogether(Parallel(weBoatTrack, wPierDownTrack), ePierUpTrack, name='we-track')

    def setMinigameId(self, minigameId):
        self.minigame = self.cr.doId2do.get(minigameId)

        self.boat = self.minigame.ground.find('**/donalds_boat')
        self.setupTracks()

        self.tower.reparentTo(self.boat)
        self.minigame.setTower(self.tower)
