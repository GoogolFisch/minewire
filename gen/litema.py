
#import litemapy
from gen.util import Cost,LENGTH_MAX,HEAT_SPREAD
from litemapy import Region, BlockState, Schematic

class Blocks:
    baseBlock = BlockState("minecraft:green_terracotta")
    upBlock = BlockState("minecraft:oak_slab",type="top")
    wireBlock = BlockState("minecraft:redstone_wire")
    redirBlock = BlockState("minecraft:target")

    torchUp = BlockState("minecraft:redstone_torch",lit="true")

    torchMinusX = BlockState("minecraft:redstone_wall_torch",
                            facing="west",lit="true")
    torchPlusX = BlockState("minecraft:redstone_wall_torch",
                            facing="east",lit="true")

    repeatMinusX = BlockState("minecraft:repeater",
                            delay="1",facing="east",locked="false",powered="false")
    repeatPlusX = BlockState("minecraft:repeater",
                            delay="1",facing="west",locked="false",powered="false")
    repeatMinusZ = BlockState("minecraft:repeater",
                            delay="1",facing="south",locked="false",powered="false")
    repeatPlusZ = BlockState("minecraft:repeater",
                            delay="1",facing="north",locked="false",powered="false")

    data = {
            "name"       :"Computational MineWire",
            "author"     :"MineWire",
            "description":"MineWire generated",
            "output"     :"./output.litematic"
    }

def safeCurruptBlocks(settings):
    try:
        global Blocks
        old = Blocks
        next = Blocks()
        next.__dict__ = old.__dict__.copy()
        next.baseXBlock = next.baseBlock
        next.baseYBlock = next.baseBlock
        next.baseZBlock = next.baseBlock
        Blocks = next
        mc_settings = settings["minecraft"]
        schem_settings = mc_settings["mc-schematic"]
        block_settings = mc_settings["blocks"]
        for k,v in schem_settings.items():
            Blocks.data[k] = v
        Blocks.data["output"] = settings.get("type",Blocks.data["output"])
        for k,v in block_settings.items():
            cp = v.copy()
            cp.pop("_id")
            Blocks.__dict__[k] = BlockState(v["_id"],**cp)
    except Exception as e:
        print(e)

class WireWire:
    __slots__ = ("parent","layer","start","end")
    def __init__(self,parent,layer):
        self.parent = parent
        self.layer  = layer
        self.start  = LENGTH_MAX
        self.end    = 0
class LaneLane:
    __slots__ = ("parent","layer","start","end")
    def __init__(self,parent,layer):
        self.parent = parent
        self.layer  = layer
        self.start  = LENGTH_MAX
        self.end    = 0
class WireLane:
    __slots__ = ("parent","layer","lane","inlet","outlet")
    def __init__(self,parent,layer,lane):
        self.parent = parent
        self.layer  = layer
        self.lane   = lane
        self.wire   = 0
        self.inlet  = None
        self.outlet = None

class WireVia:
    __slots__ = ("name","lane","wire","start","end",
                 "inLet","outLets","isIO",
                 "inputStack","outputStack",
                 "inputPoint","outputPoint")
    def __init__(self,name,ref,isInput=False,isOutput=False):
        self.name    = name
        self.lane    = 0
        self.wire    = 0
        self.start   = LENGTH_MAX
        self.end     = 0
        self.inLet   = None
        self.outLets = []
        self.isIO    = ref.isIO
        self.wireStack   = []
        self.inputPoint  = None
        self.inputStack  = []
        self.outputPoint = None
        self.outputStack = []
        #
        splitName = filter(lambda x:x.isnumeric(),name.split(":")[1:])
        refPoint = [int(x) for x in splitName]
        while len(refPoint) < 3:refPoint.insert(0,0)
        if(self.isInput ):self. inputPoint = refPoint
        if(self.isOutput):self.outputPoint = refPoint
class LaneVia:
    __slots__ = ("lane","wire","start","end","inLets","outLet","laneStack")
    def __init__(self,ref):
        self.lane   = 0
        self.wire   = 0
        self.start  = LENGTH_MAX
        self.end    = 0
        self.inLets = []
        self.outLet = None
        self.laneStack = []
class Connection:
    __slots__ = ("wireVia","laneVia","wire","lane","invert","dirLane")
    def __init__(self,wire,lane,dirLane,invert,ref):
        self.wireVia = wire
        self.laneVia = lane
        self.wire    = None
        self.lane    = None
        self.invert  = invert
        self.dirLane = dirLane
        if(self.dirLane):
            self.wire.outLets.append(self)
            self.lane.inLets .append(self)
        else:
            self.wire.inLet  = self
            self.lane.outLet = self

class Module:
    __slots__ = ("wires","lanes","cross")
    def __init__(self,wires,lanes,cross,ref):
        self.wires = wires
        self.lanes = lanes
        self.cross = cross

def main(settings,module):
    safeCurruptBlocks(settings)
    m = module.carbonCopy(Module,WireVia,LaneVia,Connection)

