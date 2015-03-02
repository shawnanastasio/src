from toontown.suit import Suit
from toontown.town import UKStreet
from toontown.town import TownLoader


class UKTownLoader(TownLoader.TownLoader):
    def __init__(self, hood, parentFSM, doneEvent):
        TownLoader.TownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = UKStreet.UKStreet
        self.musicFile = 'phase_3.5/audio/bgm/Coggish_TTC.ogg'
        self.activityMusicFile = 'phase_3.5/audio/bgm/Coggish_TTC.ogg'
        self.townStorageDNAFile = 'phase_5/dna/storage_TT_town.pdna'

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)
        Suit.loadSuits(1)
        dnaFile = 'phase_5/dna/toontown_central_' + str(self.canonicalBranchZone) + '.pdna'
        self.createHood(dnaFile)

    def unload(self):
        TownLoader.TownLoader.unload(self)
        Suit.unloadSuits(1)

