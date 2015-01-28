from pandac.PandaModules import VBase3, BitMask32
GameTime = 120
NumBarrels = 4
BarrelStartingPositions = (VBase3(-58.767, -11.994, 1.227),
 VBase3(-62.939, -12.030, 1.227),
 VBase3(-63.161, -5.343, 1.227),
 VBase3(-58.906, -5.140, 1.227))
ToonStartingPositions = (VBase3(-47.130, -7.911, -1.812),
 VBase3(-61.209, -18.443, -1.975),
 VBase3(-73.595, -9.132, -1.975),
 VBase3(107.604, 1.243, 4.575))
CogStartingPositions = (VBase3(29.649, -108.295, 2.525),
 VBase3(33.235, -84.334, 2.525),
 VBase3(-40.032, -71.041, 0.025),
 VBase3(-85.560, -73.772, 0.025),
 VBase3(-103.590, -48.323, -0.022),
 VBase3(-129.524, -5.237, 0.025),
 VBase3(-110.532, 50.293, 0.025),
 VBase3(-54.219, 65.769, 0.025),
 VBase3(25.103, 79.364, 2.525),
 VBase3(14.955, 85.893, 2.525),
 VBase3(-8.592, -16.053, 0.025),
 VBase3(-8.137, 1.978, 0.025))
CogReturnPositions = (VBase3(113.103, 1.026, 4.575),
 VBase3(113.103, 1.026, 4.575),
 VBase3(113.103, 1.026, 4.575),
 VBase3(113.103, 1.026, 4.575),
 VBase3(113.103, 1.026, 4.575),
 VBase3(113.103, 1.026, 4.575),
 VBase3(113.103, 1.026, 4.575),
 VBase3(113.103, 1.026, 4.575),
 VBase3(113.103, 1.026, 4.575),
 VBase3(113.103, 1.026, 4.575))
StageHalfWidth = 25
StageHalfHeight = 18
NoGoal = 0
BarrelGoal = 1
ToonGoal = 2
RunAwayGoal = 3
InvalidGoalId = -1
GoalStr = {NoGoal: 'NoGoal',
 BarrelGoal: 'BarrelGoal',
 ToonGoal: 'ToonGoal',
 RunAwayGoal: 'RunAwayGoal',
 InvalidGoalId: 'InvalidGoa'}
BarrelBitmask = BitMask32(512)
BarrelOnGround = -1
NoBarrelCarried = -1
LyingDownDuration = 2.0
MAX_SCORE = 20
MIN_SCORE = 3

def calcScore(t):
    range = MAX_SCORE - MIN_SCORE
    score = range * (float(t) / GameTime) + MIN_SCORE
    return int(score + 0.5)


def getMaxScore():
    result = calcScore(GameTime)
    return result


NumCogsTable = [{2000: 5,
  1000: 5,
  5000: 5,
  4000: 5,
  3000: 5,
  9000: 5},
 {2000: 7,
  1000: 7,
  5000: 7,
  4000: 7,
  3000: 7,
  9000: 7},
 {2000: 9,
  1000: 9,
  5000: 9,
  4000: 9,
  3000: 9,
  9000: 9},
 {2000: 11,
  1000: 11,
  5000: 11,
  4000: 11,
  3000: 11,
  9000: 11}]
CogSpeedTable = [{2000: 6.0,
  1000: 6.4,
  5000: 6.8,
  4000: 7.2,
  3000: 7.6,
  9000: 8.0},
 {2000: 6.0,
  1000: 6.4,
  5000: 6.8,
  4000: 7.2,
  3000: 7.6,
  9000: 8.0},
 {2000: 6.0,
  1000: 6.4,
  5000: 6.8,
  4000: 7.2,
  3000: 7.6,
  9000: 8.0},
 {2000: 6.0,
  1000: 6.4,
  5000: 6.8,
  4000: 7.2,
  3000: 7.6,
  9000: 8.0}]
ToonSpeed = 9.0
PerfectBonus = [8,
 6,
 4,
 2]

def calculateCogs(numPlayers, safezone):
    result = 5
    if numPlayers <= len(NumCogsTable):
        if safezone in NumCogsTable[numPlayers - 1]:
            result = NumCogsTable[numPlayers - 1][safezone]
    return result


def calculateCogSpeed(numPlayers, safezone):
    result = 6.0
    if numPlayers <= len(NumCogsTable):
        if safezone in CogSpeedTable[numPlayers - 1]:
            result = CogSpeedTable[numPlayers - 1][safezone]
    return result