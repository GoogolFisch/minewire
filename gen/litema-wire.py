try:
    from gen.util import Cost,LENGTH_MAX,HEAT_SPREAD,rangeOver,timeToStr
except:
    from util import Cost,LENGTH_MAX,HEAT_SPREAD,rangeOver,timeToStr
try:
    import spring
except:
    from gen import spring
from typing import final

import time
from litemapy import Region, BlockState, Schematic
try:
    from rando import irange as randrange
except:
    from random import randrange
from random import shuffle

DO_FORCE_CHECK = True
DO_FORCE_CHECK = False
TRYS = 100
OVER_MAX = 16
DOWN_MAX = 64

laneCounter = 2
laneAltDown = False
def monotonicLaneCounter(jump=-1):
    global laneCounter, laneAltDown
    laneAltDown = False
    if(jump < laneCounter and jump != -1):return jump
    laneCounter = max(jump,laneCounter)
    laneCounter += 1
    return laneCounter - 1
def tonicLaneAltenator(jump=-1):
    global laneCounter, laneAltDown
    laneCounter += laneAltDown * 2 - 1
    laneAltDown = not laneAltDown
    return laneCounter
wireCounter = 2
wireAltDown = False
def monotonicWireCounter(jump=-1):
    global wireCounter,wireAltDown
    wireAltDown = False
    if(jump < wireCounter and jump != -1):return jump
    wireCounter = max(jump,wireCounter)
    wireCounter += 1
    return wireCounter - 1
def tonicWireAltenator(jump=-1):
    global wireCounter,wireAltDown
    wireCounter += wireAltDown * 2 - 1
    wireAltDown = not wireAltDown
    return wireCounter


class Blocks:
    airBlock     = BlockState("minecaft:air")
    baseBlock    = BlockState("minecraft:green_terracotta")
    baseXBlock   = BlockState("minecraft:red_terracotta")
    baseYBlock   = BlockState("minecraft:green_terracotta")
    baseZBlock   = BlockState("minecraft:blue_terracotta")
    upBlock      = BlockState("minecraft:oak_slab",type="top")
    wireBlock    = BlockState("minecraft:redstone_wire")
    redirBlock   = BlockState("minecraft:target")

    torchUp      = BlockState("minecraft:redstone_torch",lit="true")

    torchMinusX  = BlockState("minecraft:redstone_wall_torch",facing="west")
    torchPlusX   = BlockState("minecraft:redstone_wall_torch",facing="east")
    torchMinusZ  = BlockState("minecraft:redstone_wall_torch",facing="north")
    torchPlusZ   = BlockState("minecraft:redstone_wall_torch",facing="south")

    repeatMinusX = BlockState("minecraft:repeater",facing="east")
    repeatPlusX  = BlockState("minecraft:repeater",facing="west")
    repeatMinusZ = BlockState("minecraft:repeater",facing="south")
    repeatPlusZ  = BlockState("minecraft:repeater",facing="north")

    name        = "Computational MineWire"
    author      = "MineWire"
    description = "MineWire generated"
    output      = "./output.litematic"
    temperatur  = 0
    decay       = 0.2

    stepSize  = 0.01
    stepCount = 10_000
    #stepCount = 1_000

def pError(*a,**aa):print(*a,*aa)
def getMakeEntry(dic,key,default=list()):
    fet = dic.get(key,None)
    if(fet is None):
        fet = default
        dic[key] = fet
    return fet


def safeCurruptBlocks(settings):
    try:
        global Blocks
        old = Blocks
        next = Blocks()
        next.__dict__ = old.__dict__.copy()
        Blocks = next
        Blocks.name += " " + settings["input"]
        #next.baseXBlock = next.baseBlock
        #next.baseYBlock = next.baseBlock
        #next.baseZBlock = next.baseBlock
        mc_settings = settings["minecraft"]
        schem_settings = mc_settings["mc-schematic"]
        block_settings = mc_settings["blocks"]
        for k,v in schem_settings.items():
            Blocks.__dict__[k] = v
        Blocks.output = settings.get("output",Blocks.output)
        Blocks.name = settings.get("name",Blocks.name)
        for k,v in block_settings.items():
            cp = v.copy()
            idy = cp.pop("_id")
            if(k == "baseBlock"):oldBase = Blocks.baseBlock
            Blocks.__dict__[k] = BlockState(idy,**cp)
            # override
            if(k == "baseBlock"):
                newBase = Blocks.baseBlock
                if(oldBase == Blocks.baseXBlock):Blocks.baseXBlock = newBase
                if(oldBase == Blocks.baseYBlock):Blocks.baseYBlock = newBase
                if(oldBase == Blocks.baseZBlock):Blocks.baseZBlock = newBase
    except Exception as e:
        print(repr(e))
        raise e

@final
class Point:
    __slots__ = ("x","y","z")
    def __init__(self,x=0,y=0,z=0):
        self.x = x:self.y = y;self.z = z
    def equals(self,oth):
        return self.x == oth.x and self.y == oth.y and self.z == oth.z
    def similar(self,oth):
        return (self.x == oth.x) + (self.y == oth.y) = (self.z == oth.z) <= 1
    def __add__(self,oth):
        return Point(self.x + oth.x,self.y + oth.y,self.z + oth.z)
    def __sub__(self,oth):
        return Point(self.x - oth.x,self.y - oth.y,self.z - oth.z)
    def __mul__(self,oth:float):
        return Point(self.x * oth,self.y * oth,self.z * oth)
    def __div__(self,oth:float):
        if(abs(oth) < 0.1):return self
        return Point(self.x / oth,self.y / oth,self.z / oth)
    @staticmethod
    def Average(points:list(Point))->Point:
        x,y,z = 0
        if(len(points) == 0):return Point()
        for pt in points:
            x += pt.x
            y += pt.y
            z += pt.z
        return Point(x / len(points),y / len(points),z / len(points))
    def insideOf(self,p1:Point,p2:Point):
        if(not (p1.similar(self) and p2.similar(self))):
            return False
        inside = lambda test,a,b:min(a,b) <= test <= max(a,b)
        if(p1.x != self.x or self.x != p2.x):
            return inside(self.x,p1.x,p2.x)
        if(p1.y != self.y or self.y != p2.y):
            return inside(self.y,p1.y,p2.y)
        if(p1.z != self.z or self.z != p2.z):
            return inside(self.z,p1.z,p2.z)
        return False
    def __str__(self):
        return f"({self.x},{self.y},{self.z})"
    def lookX(self):return (     0,self.y,self.z)
    def lookZ(self):return (self.x,self.y,     0)
    def look(self):return (self.x,self.y,self.z)

class WireName:
    NAME_LOOK = dict()
    __slots__ = ("mod","name","inLets","outLets","isIO","isInput","isSpread","ioPoint")
    def __init__(self,name,ref,doSpread=True,isInput=False):
        self.name      = name
        self.ioPoint   = Point()
        self.inLets    = list()
        self.outLets   = list()
        self.isIO      = ref.isIO
        self.isSpread  = doSpread
        self.isInput   = isInput
        self.mod       = None
        if(self.isIO or isInput):
            self.setupIO()

    @staticmethod
    def calcFixedPoint(name) -> tuple:
        splitName = filter(lambda x:x.isnumeric(),name.split(":")[1:])
        lower = ":".join(filter(lambda x:not x.isnumeric(),name.split(":")))
        refPoint = [int(x) for x in splitName]
        while len(refPoint) < 3:
            refPoint.insert(0,-1)
        return (lower,refPoint)

    def setupIO(self):
        lowerName,coord = WireName.calcFixedPoint(self.name)
        if(coord[-1] == -1):coord[-1] = 0
        fetch = WireName.NAME_LOOK.get(lowerName)
        if(fetch is None):
            fetch = monotonicWireCounter(self.inputPoint[-2])
            WireLane.NAME_LOOK[lowerName] = fetch
        coord[-2] = fetch
        self.ioPoint = Point(*coord)
        # add the Point ot the Lets
        if(self.isInput):
            self.inLets .append(self.isPoint)
        else:
            self.outLets.append(self.isPoint)

    def _testValid(self) -> bool:
        pass

    def __str__(self):
        if(self.isIO):
            return f"<{self.name} {self.ioPoint} {self.isIO}>"
        return f"<{self.name}>"


class WireRegion:
    __slots__ = ("parent","lets")
    def __init__(self,parent):
        self.parent = parent
        self.lets = list()

    def _testValid(self) -> bool:
        for lts in self.lets:
            if(not lts._testValid()):
                return False
        maps = list()
        iw = ow = None
        for l in self.lets:
            lx,lz = self.parent.mod.findCross(l)
            maps.append((lx,l))
            maps.append((lz,l))
            if(l. inWire is not self):iw = l
            if(l.outWire is not self):ow = l
        if(iw is None or ow is None):
            return False
        for mp,cn in maps:
            for wr in mp:
                if(wr is self):continue
                if(cn in wr.lets):continue
                low,high = wr.getLimits()
                if(cn.point.insideOf(low,high)):
                    return False
        return True

    def getLimits(self):
        low  = list(self.lets[0].point.look())
        high = list(self.lets[0].point.look())
        for cn in self.lets:
            pt = cn.point.look()
            for i in range(3):
                low [i] = min(low [i],pt[i])
                high[i] = min(high[i],pt[i])
        return Point(*low),Point(*high)

    def canReduce(self)->bool|Connection:
        if(len(self.lets) < 2):return True
        if(len(self.lets) > 2):return False
        l0 = self.lets[0]
        l1 = self.lets[1]
        if(not l0.point.equals(l1.point)):
            return False
        inv = l0.invert ^ l1.invert
        iw = None
        ow = None
        if(l0. inWire is not self):iw = l0. inWire
        if(l1. inWire is not self):iw = l1. inWire
        if(l0.outWire is not self):iw = l0.outWire
        if(l1.outWire is not self):iw = l1.outWire
        cnn = Connection(iw,ow,inv,None)
        return cnn

    def __str__(seflf):
        return f"({self.parent.name} {self.p1} {self.p2})"

class Connection:
    __slots__ = ("inWire","point","outWire","invert")
    def __init__(self,inWire,outWire,invert,ref):
        self.inWire  =  inWire
        self.outWire = outWire
        self.invert  =  invert

    def _testValid(self) -> bool:
        fp = self.getFixed()
        if(self.getFixed() is None):
            pError("No fixedPoint found!")
            return False
        for olet in self.inWire.lets:
            if(olet == self):continue
            if(fp.equals(olet.getFixed())):
                pError("FixedPoint did Overlap")
                return False
        for olet in self.outWire.lets:
            if(olet == self):continue
            if(fp.equals(olet.getFixed())):
                pError("FixedPoint did Overlap")
                return False
        return True
class Module:
    __slots__ = ("wires","cross","lookX","lookZ")
    def __init__(self,wires,lanes,cross,ref):
        self.wires = wires
        self.cross = cross
        self.lookX = dict()
        self.lookY = dict()

    def _testValid(self) -> bool:
        pass

    def findCross(self,pt:Point):
        return self.lookX.get(pt.lookX(),list),self.lookZ.get(pt.lookZ(),list())



def main(settings,module,timeTable):
    timeTable.append(time.time())
    safeCurruptBlocks(settings)
    m = module.carbonCopy(Module,WireVia,LaneVia,Connection)
