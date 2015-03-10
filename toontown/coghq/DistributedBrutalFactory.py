from toontown.coghq.DistributedFactory import DistributedFactory


class DistributedBrutalFactory(DistributedFactory):
    notify = directNotify.newCategory('DistributedBrutalFactory')
    
    def getFloorOuchLevel(self):
        return 8
