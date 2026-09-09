
#import litemapy
from gen.util import Cost,LENGTH_MAX,HEAT_SPREAD
from litemapy import Region, BlockState, Schematic

class Blocks:
    baseBlock = BlockState("minecraft:green_terracotta")
    upBlock = BlockState("minecraft:oak_slab",type="top")
    wireBlock = BlockState("minecraft:redstone_wire")
    redirBlock = BlockState("minecraft:target")

    torchUp = BlockState("minecraft:redstone_torch",lit="true")

    torchMinusX = BlockState("minecraft:redstone_wall_torch",facing="west")
    torchPlusX = BlockState("minecraft:redstone_wall_torch",facing="east")
    torchMinusZ = BlockState("minecraft:redstone_wall_torch",facing="north")
    torchPlusZ = BlockState("minecraft:redstone_wall_torch",facing="south")

    repeatMinusX = BlockState("minecraft:repeater",facing="east")
    repeatPlusX = BlockState("minecraft:repeater",facing="west")
    repeatMinusZ = BlockState("minecraft:repeater",facing="south")
    repeatPlusZ = BlockState("minecraft:repeater",facing="north")

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
            idy = cp.pop("_id")
            Blocks.__dict__[k] = BlockState(idy,**cp)
    except Exception as e:
        print(e)

class WireWire:
    __slots__ = ("parent","start","end")
    def __init__(self,parent):
        self.parent = parent
        self.reset()

    def reset(self):
        self.start  = self.parent.lane
        self.end    = self.parent.lane

    def update(self,cross):
        self.start = min(self.start,cross.laneVia.lane)
        self.end   = max(self.end  ,cross.laneVia.lane)

    def getRawCost(self):
        return Cost(self.end - self.start,0)


class LaneLane:
    __slots__ = ("parent","start","end")
    def __init__(self,parent):
        self.parent = parent
        self.reset()

    def reset(self):
        self.start  = self.parent.wire
        self.end    = self.parent.wire

    def update(self,cross):
        self.start = min(self.start,cross.wireVia.lane)
        self.end   = max(self.end  ,cross.wireVia.lane)

    def getRawCost(self):
        return Cost(self.end - self.start,0)

class WireLane:
    __slots__ = ("parent","layer","lane","wire","inlet","outlet","child")
    def __init__(self,parent,layer,lane):
        self.parent = parent
        self.lane   = lane
        self.layer  = layer
        self.wire   = 0
        self.inlet  = None
        self.outlet = None
        self.child  = None

    def setInlet(self,let):
        self.inlet  = let

    def setOutlet(self,let):
        self.outlet = let

    def setChildWire(self,wir):
        self.child  = wir

    def getRawCost(self):
        return Cost(abs(self.parent.wire - self.child.wire),0)


class WireVia:
    __slots__ = ("name","lane","wire","start","end",
                 "inLet","outLets","isIO","wireStack",
                 "inLane","inWire","outLane","outWire",
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
        self.outputPoint = None
        #
        if(isInput ):self.setupInput()
        if(isOutput):self.setupOutput()

    @staticmethod
    def calcFixedPoint(name) -> tuple:
        splitName = filter(lambda x:x.isnumeric(),name.split(":")[1:])
        refPoint = [int(x) for x in splitName]
        while len(refPoint) < 3:
            refPoint.insert(0,-1)
        return refPoint

    def setupInput(self):
        self.inputPoint = WireVia.calcFixedPoint(self.name)
        self.inLane = WireLane(self,
                               layer=self.inputPoint[-1],
                               lane=self.inputPoint[-2])
        self.inWire = WireWire(self.inLane)

    def setupOutput(self):
        self.outputPoint = WireVia.calcFixedPoint(self.name)
        self.outLane = WireLane(self,
                                layer=self.outputPoint[-1],
                                lane=self.outputPoint[-2])
        self.outWire = WireWire(self.outLane)

    def makeGetLayer(self,layer):
        while(len(self.wireStack) <= layer):
            self.wireStack.append(WireWire(self))
        return self.wireStack[layer]

    def getIfLayer(self,layer):
        if(len(self.wireStack) < layer):return None
        return self.wireStack[layer]

    def reRawCalculateCost(self):
        cost = Cost()
        self.start = LENGTH_MAX
        self.end   = 0
        for w in self.wireStack:
            w.reset()
        if(self.inLane is not None):
            cost += self.inLane.getRawCost()
            self.inWire.reset()
            self.inWire.start = 0
            cost += self.inWire.getRawCost()
        for cx in self.outLets:
            cx.update()
            self.start = min(self.start,cx.layer)
            self.end   = min(self.end  ,cx.layer)
        for w in range(self.start,self.end + 1):
            cost += self.wireStack[w].getRawCost()
        cost += Cost(self.end - self.start,0)
        return cost


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

    def makeGetLayer(self,layer):
        while(len(self.laneStack) <= layer):
            self.laneStack.append(LaneLane(self))
        return self.laneStack[layer]

    def getIfLayer(self,layer):
        if(len(self.laneStack) < layer):return None
        return self.laneStack[layer]



class Connection:
    __slots__ = ("wireVia","laneVia","wire","layer","lane","invert","dirLane")
    def __init__(self,wire,lane,dirLane,invert,ref):
        self.wireVia = wire
        self.laneVia = lane
        self.update()
        self.invert  = invert
        self.dirLane = dirLane
        self.layer   = 0
        if(self.dirLane):
            self.wireVia.outLets.append(self)
            self.laneVia.inLets .append(self)
        else:
            self.wireVia.inLet  = self
            self.laneVia.outLet = self
        self.update()

    def update(self):
        self.wire = self.wireVia.makeGetLayer(0)
        self.lane = self.laneVia.makeGetLayer(0)
        self.wire.update(self)
        self.lane.update(self)

class Module:
    __slots__ = ("wires","lanes","cross")
    def __init__(self,wires,lanes,cross,ref):
        self.wires = wires
        self.lanes = lanes
        self.cross = cross

    def getLanesAt(self,layer:int,lane:int) -> list:
        out = []
        for l in self.lanes:
            if(l.lane != lane):continue
            lw = l.getIfLayer(layer)
            if(lw is not None):
                out.append(lw)
        return out

    def getWiresAt(self,layer:int,wire:int) -> list:
        out = []
        for w in self.wires:
            if(w.wire != wire):continue
            ww = w.getIfLayer(layer)
            if(ww is not None):
                out.append(ww)
        return out

    def wireVCollide(self,wireV:WireVia) -> list:
        collisions = []
        for wv in self.wires:
            if(wv is wireV):
                continue
            diff = abs(wireV.lane - wv.lane)
            diff += abs(wireV.wire - wv.wire)
            intersect = wireV.start < wv.end and wv.start < wireV.end
            if(diff < 2 and intersect):
                collisions.append(wv)
                continue


        return collisions

    def wireCollide(self,wire:WireWire,layer:int):
        parent = wire.parent
        vparent = wire.parent
        if(type(parent) == WireLane):
            vparent = parent.parent
        collisions = []
        for wv in self.wires:
            if wv is vparent:continue
            if(wv.start > layer or wv.end < layer):
                continue
            if(wv.inLane is not None):
                if(wv.inWire.start < wire.end and wire.start < wv.inWire.end):
                    collisions.append((wv,wb.inWire))
                    continue
            if(wv.outLane is not None):
                if(wv.outWire.start < wire.end and wire.start < wv.outWire.end):
                    collisions.append((wv,wb.outWire))
                    continue
            if(wv.wire != parent.wire):
                continue
            if(wire.start <= wv.lane <= wire.end):
                collisions.append((wv,None))
                continue
            subW = wv.getIfLayer(layer)
            if(subW is None):continue
            if(subW.start < wire.end and wire.start < subW.end):
                collisions.append((wv,subW))
                continue
        for lv in self.lanes:
            if(wv.start > layer or wv.end < layer):
                continue
            if(wire.start <= lv.lane <= wire.end):
                collisions.append((lv,None))
                continue
        return collisions

    def laneCollide(self,lane:LaneLane,layer:int):
        parent = lane.parent
        collisions = []
        for wv in self.wires:
            if(wv.start > layer or wv.end < layer):
                continue
            if(lane.start <= wv.wire <= lane.end):
                collisions.append((wv,None))
                continue
            if(wv.inLane is not None):
                if(wv.inLane.lane == parent.lane):
                    if(wv.inLane.start < lane.end and lane.start < wv.inLane.end):
                        collisions.append((wv,wb.inLane))
                        continue
            if(wv.outLane is not None):
                if(wv.outLane.lane == parent.lane):
                    if(wv.outLane.start < lane.end and lane.start < wv.outLane.end):
                        collisions.append((wv,wb.outLane))
                        continue
        for lv in self.lanes:
            if(wv.start > layer or wv.end < layer):
                continue
            if(parent.lane != lv.lane):
                continue
                collisions.append((lv,None))
            subL = lv.getIfLayer(layer)
            if(subL is None):continue
            if(subL.start < lane.end and lane.start < subL.end):
                collisions.append((lv,subL))
                continue
        return collisions




def main(settings,module):
    safeCurruptBlocks(settings)
    m = module.carbonCopy(Module,WireVia,LaneVia,Connection)

