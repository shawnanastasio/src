from toontown.safezone.UKSafeZoneLoader import UKSafeZoneLoader
from toontown.town.UKTownLoader import UKTownLoader
from toontown.toonbase import ToontownGlobals
from toontown.hood.ToonHood import ToonHood

class UKHood(ToonHood):
    notify = directNotify.newCategory('UKHood')

    ID = ToontownGlobals.Unknown
    TOWNLOADER_CLASS = UKTownLoader
    SAFEZONELOADER_CLASS = UKSafeZoneLoader
    STORAGE_DNA = 'phase_4/dna/storage_TT.pdna'
    SKY_FILE = 'phase_3.5/models/props/BR_sky'
    TITLE_COLOR = (1.0, 0.5, 0.4, 1.0)