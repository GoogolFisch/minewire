
#import litemapy
try:
    from gen.util import Cost,LENGTH_MAX,HEAT_SPREAD,rangeOver
except:
    from util import Cost,LENGTH_MAX,HEAT_SPREAD,rangeOver

import time
from litemapy import Region, BlockState, Schematic
import random

DO_FORCE_CHECK = False
TRYS = 100
OVER_MAX = 64

laneCounter = 2
def monotonicLaneCounter(jump=-1):
    global laneCounter
    if(jump < laneCounter and jump != -1):return jump
    laneCounter = max(jump,laneCounter)
    laneCounter += 1
    return laneCounter - 1
wireCounter = 2
def monotonicWireCounter(jump=-1):
    global wireCounter
    if(jump < wireCounter and jump != -1):return jump
    wireCounter = max(jump,wireCounter)
    wireCounter += 1
    return wireCounter - 1


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

    name        = "Computational MineWire",
    author      = "MineWire",
    description = "MineWire generated",
    output      = "./output.litematic"
    temperatur  = 100
    decay       = 0.2

def safeCurruptBlocks(settings):
    try:
        global Blocks
        old = Blocks
        next = Blocks()
        next.__dict__ = old.__dict__.copy()
        #next.baseXBlock = next.baseBlock
        #next.baseYBlock = next.baseBlock
        #next.baseZBlock = next.baseBlock
        Blocks = next
        mc_settings = settings["minecraft"]
        schem_settings = mc_settings["mc-schematic"]
        block_settings = mc_settings["blocks"]
        for k,v in schem_settings.items():
            Blocks.__dict__[k] = v
        Blocks.output = settings.get("output",Blocks.output)
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
        return Cost(self.end - self.start) * 3 + Cost(self.end + self.start)

    def __str__(self):
        return f"<{self.parent.name}:{self.start}-{self.end}>"


class LaneLane:
    __slots__ = ("parent","start","end")
    def __init__(self,parent):
        self.parent = parent
        self.reset()

    def reset(self):
        self.start  = self.parent.wire
        self.end    = self.parent.wire

    def update(self,cross):
        self.start = min(self.start,cross.wireVia.wire)
        self.end   = max(self.end  ,cross.wireVia.wire)

    def getRawCost(self):
        return Cost(self.end - self.start) * 3 + Cost(self.end + self.start)

    def __str__(self):
        return f"<{self.start}-{self.end}>"

class WireLane:
    namePosition = {}
    __slots__ = ("parent","layer","lane","wire","inlet","outlet","child",
                 "start","end","name")
    def __init__(self,parent,layer,wire):
        self.parent = parent
        self.wire   = wire
        self.layer  = layer
        self.lane   = monotonicLaneCounter()
        self.inlet  = None
        self.outlet = None
        self.child  = None
        self.name   = parent.name + "~"
        self.update()

    def update(self,cross=None):
        self.start  = min(self.parent.wire,self.wire)
        self.end    = max(self.parent.wire,self.wire)
        sw = self.parent.makeGetLayer(self.layer)
        sw.start = min(sw.start,self.lane)
        sw.end   = max(sw.end  ,self.lane)

    def reset(self,cross=None):self.update(cross)

    def setInlet(self,let):
        self.inlet  = let

    def setOutlet(self,let):
        self.outlet = let

    def setChildWire(self,wir):
        self.child  = wir

    def getRawCost(self):
        self.update()
        return Cost(self.end - self.start + self.lane) * 3 + Cost(self.end + self.start + self.lane)

    def __str__(self):
        return f"<{self.parent.name}:{self.layer},{self.lane},{self.wire} {self.start}-{self.end}>"


class WireVia:
    __slots__ = ("name","lane","wire","start","end",
                 "wStart","wEnd",
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
        self.inLane  = None
        self.outLane = None
        self.inWire  = None
        self.outWire = None
        #
        if(isInput ):self.setupInput()
        if(isOutput):self.setupOutput()
        self.reset()

    @staticmethod
    def calcFixedPoint(name) -> tuple:
        splitName = filter(lambda x:x.isnumeric(),name.split(":")[1:])
        lower = ":".join(filter(lambda x:not x.isnumeric(),name.split(":")))
        refPoint = [int(x) for x in splitName]
        while len(refPoint) < 3:
            refPoint.insert(0,-1)
        return (lower,refPoint)

    def setupInput(self):
        lowerName,self.inputPoint = WireVia.calcFixedPoint(self.name)
        if(self.inputPoint[-1] == -1):self.inputPoint[-1] = 0
        fetch = WireLane.namePosition.get(lowerName)
        if(fetch is None):
            fetch = monotonicWireCounter(self.inputPoint[-2])
            WireLane.namePosition[lowerName] = fetch
        self.inputPoint[-2] = fetch
        self.inLane = WireLane(self,
                               layer=self.inputPoint[-1],
                               wire=self.inputPoint[-2])
        self.inWire = WireWire(self.inLane)
        self.inLane.setChildWire(self.inWire)
        self.makeGetLayer(self.inputPoint[-1])

    def setupOutput(self):
        lowerName,self.outputPoint = WireVia.calcFixedPoint(self.name)
        if(self.outputPoint[-1] == -1):self.outputPoint[-1] = 0
        fetch = WireLane.namePosition.get(lowerName)
        if(fetch is None):
            fetch = monotonicWireCounter(self.outputPoint[-2])
            WireLane.namePosition[lowerName] = fetch
        self.outputPoint[-2] = fetch
        self.outLane = WireLane(self,
                                layer=self.outputPoint[-1],
                                wire=self.outputPoint[-2])
        self.outWire = WireWire(self.outLane)
        self.outLane.setChildWire(self.outWire)
        self.makeGetLayer(self.outputPoint[-1])

    def makeGetLayer(self,layer):
        while(len(self.wireStack) <= layer):
            self.wireStack.append(WireWire(self))
        return self.wireStack[layer]

    def getIfLayer(self,layer):
        if(len(self.wireStack) <= layer):return None
        if(layer > self.end  ):return None
        if(layer < self.start):return None
        return self.wireStack[layer]

    def reset(self):
        self.start = LENGTH_MAX
        self.end   = 0
        if(self.inLane is not None):
            self.start = self.inLane.layer
            self.end   = self.inLane.layer
        if(self.outLane is not None):
            self.start = self.outLane.layer
            self.end   = self.outLane.layer
        for w in self.wireStack:
            w.reset()
        self.wStart = self.lane
        self.wEnd   = self.lane
        for sw in rangeOver(self):
            subW = self.wireStack[sw]
            self.wStart = min(self.wStart,subW.start)
            self.wEnd   = max(self.wEnd  ,subW.end  )

    def getRawCost(self):
        cost = Cost()
        self.reset()
        #
        if(self.inLane is not None):
            cost += self.inLane.getRawCost()
            self.inWire.reset()
            self.inWire.start = 0
            self.inLane.reset()
            cost += self.inWire.getRawCost()
        if(self.outLane is not None):
            cost += self.outLane.getRawCost()
            self.outWire.reset()
            self.outWire.start = 0
            self.outLane.reset()
            cost += self.outWire.getRawCost()
        for cx in self.outLets:
            cx.update()
            self.start = min(self.start,cx.layer)
            self.end   = max(self.end  ,cx.layer)
        if(self.inLet is not None):
            self.inLet.update()
            self.start = min(self.start,self.inLet.layer)
            self.end   = max(self.end  ,self.inLet.layer)
        for w in rangeOver(self):
            cost += self.wireStack[w].getRawCost()
        vCost = Cost(self.end - self.start) * 3 + Cost(self.start + self.end)
        cost += vCost * 3
        return cost

    def _writeTreeBranch(self,reg,layer):
        sw = self.getIfLayer(layer)
        if(sw is None):return
        startl = self.lane
        ly4 = layer * 4
        lw3 = self.wire * 3
        if(self.inLane is not None):
            if(self.inLane.layer == layer):
                startl = self.inLane.lane
        elif(self.inLet is not None):
            if(self.inLet.layer == layer):
                startl = self.inLet.laneVia.lane
        #
        ln = startl + 4
        while ln < sw.end:
            if(ln != self.lane):
                reg[ln * 3,ly4 + 1,lw3] = Blocks.repeatPlusX
            else:
                ln += 1
                continue
            ln += 4
        ln = startl - 4
        while ln > sw.start:
            if(ln != self.lane):
                try:
                    reg[ln * 3,ly4 + 1,lw3] = Blocks.repeatMinusX
                except Exception as e:
                    print(ln * 3,ly4 + 1,lw3)
                    raise e
            else:
                ln -= 1
                continue
            ln -= 4
        return 12


    def writeTree(self,reg):
        startY = self.start
        if(self.inLet is not None):startY = self.inLet.layer
        elif(self.inLane is not None):startY = self.inLane.layer
        for layer in range(self.start,self.end + 1):
            self._writeTreeBranch(reg,layer)
        #if(self.inWire.wire ):pass
        pdir = False
        if(self.inLane is not None):
            if(self.inLane.wire == self.wire):return
            pdir = self.inLane.wire < self.wire
        elif(self.outLane is not None):
            if(self.outLane.wire == self.wire):return
            pdir = self.outLane.wire > self.wire
        else:return
        print("Hello")
        lan = self.inLane or self.outLane
        sign = (lan.wire > self.wire) * 2 - 1
        repSign = pdir and Blocks.repeatPlusZ or Blocks.repeatMinusZ
        dz = lan.parent.wire + sign
        count = 4
        ly4 = lan.layer * 4
        ol3 = lan.lane * 3
        while dz != lan.wire:
            if(count >= 3):
                reg[ol3,ly4 + 3,dz * 3] = repSign
                #print(lan.lane,lan.layer,dz)
                count = 0
            else:count += 1
            dz += sign
        repSign = self.inLane and Blocks.repeatPlusX or Blocks.repeatMinusX
        dx = lan.lane - 1
        count += 1
        while dx > 0:
            if(count >= 3):
                reg[dx * 3,ly4 + 1,lan.wire * 3] = repSign
                #print(dx,lan.layer,lan.wire)
                count = 0
            else:count += 1
            dx -= 1
        if(self.outLane is not None):reg[ol3 + 1,ly4 + 1,self.wire * 3] = Blocks.repeatMinusX
        if(self.inLane  is not None):reg[ol3 + 1,ly4 + 1,self.wire * 3] = Blocks.repeatPlusX



    def write(self,reg):
        wl3 = self.lane * 3
        ww3 = self.wire * 3
        for layer in rangeOver(self):
            try:
                subW = self.getIfLayer(layer)
                for x in range(subW.start * 3,subW.end * 3 + 1):
                    reg[x,layer * 4    ,ww3] = Blocks.baseXBlock
                    reg[x,layer * 4 + 1,ww3] = Blocks.wireBlock
            except Exception as e:
                print(layer,x,ww3,subW.start,subW.end)
                raise e
        olay = self.inLet or self.inLane
        if(olay is not None):
            olay = olay.layer
            for layer in range(olay,self.end):
                reg[wl3    ,layer * 4 + 1,ww3 + 1] = Blocks.redirBlock
                reg[wl3    ,layer * 4 + 2,ww3 + 1] = Blocks.torchUp
                reg[wl3    ,layer * 4 + 3,ww3 + 1] = Blocks.baseYBlock
                reg[wl3    ,layer * 4 + 4,ww3 + 1] = Blocks.torchUp
                reg[wl3    ,layer * 4 + 5,ww3 + 1] = Blocks.baseYBlock
            for layer in range(self.start,olay):
                reg[wl3    ,layer * 4 + 4,ww3 - 1] = Blocks.torchMinusZ
                reg[wl3    ,layer * 4 + 3,ww3 - 1] = Blocks.wireBlock
                reg[wl3    ,layer * 4 + 2,ww3 - 1] = Blocks.baseYBlock
                reg[wl3    ,layer * 4 + 2,ww3    ] = Blocks.torchPlusZ
        ol = self.inLane or self.outLane
        ow = self.inWire or self.outWire
        if(ol is None):
            self.writeTree(reg)
            return
        ol3 = ol.lane * 3
        ow3 = ol.wire * 3
        ly4 = ol.layer * 4
        for z in range(ol.start * 3 + 2,ol.end * 3 - 1):
            if(reg[ol3,ly4 + 2,z].id != "minecraft:air"):continue
            reg[ol3,ly4 + 2,z] = Blocks.baseZBlock
            if(reg[ol3,ly4 + 3,z].id != "minecraft:air"):continue
            reg[ol3,ly4 + 3,z] = Blocks.wireBlock
        if(ol.start != ol.end):
            reg[ol3,ly4 + 1,ol.start * 3 + 1] = Blocks.baseBlock
            reg[ol3,ly4 + 2,ol.start * 3 + 1] = Blocks.wireBlock
            reg[ol3,ly4 + 1,ol.end   * 3 - 1] = Blocks.baseBlock
            reg[ol3,ly4 + 2,ol.end   * 3 - 1] = Blocks.wireBlock
        #reg[ow.end * 3,ly4 + 1,ow3] = Blocks.baseBlock
        #reg[ow.end * 3,ly4 + 2,ow3] = Blocks.wireBlock
        for x in range(ow.start * 3,ow.end * 3 + 1):
            if(reg[x,ly4    ,ow3].id != "minecraft:air"):continue
            reg[x,ly4    ,ow3] = Blocks.baseXBlock
            if(reg[x,ly4 + 1,ow3].id != "minecraft:air"):continue
            reg[x,ly4 + 1,ow3] = Blocks.wireBlock
        self.writeTree(reg)

    def __str__(self):
        return (f"<{self.name} : wire={self.wire},lane={self.lane} " +
                f"{self.start}-{self.end}>")

    def showContext(self):
        dat = str(self)
        if(self.inLet is not None):
            dat += f"{self.inLet}:"
        for ol in self.outLets:
            dat += f",{ol}"
        return dat


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
        self.reset()

    def makeGetLayer(self,layer):
        while(len(self.laneStack) <= layer):
            self.laneStack.append(LaneLane(self))
        return self.laneStack[layer]

    def getIfLayer(self,layer):
        if(len(self.laneStack) <= layer):return None
        if(layer > self.end  ):return None
        if(layer < self.start):return None
        return self.laneStack[layer]

    def reset(self):
        self.start  = LENGTH_MAX
        self.end    = 0
        for sl in self.laneStack:
            sl.reset()
        for cx in self.inLets:
            cx.update()
            self.start = min(self.start,cx.layer)
            self.end   = max(self.end  ,cx.layer)
        if(self.outLet is not None):
            self.outLet.update()
            self.start = min(self.start,self.outLet.layer)
            self.end   = max(self.end  ,self.outLet.layer)

    def getRawCost(self):
        cost = Cost()
        self.reset()
        #
        for w in rangeOver(self):
            cost += self.laneStack[w].getRawCost()
        vCost = Cost(self.end - self.start) * 3 + Cost(self.start + self.end)
        cost += vCost * 3
        return cost

    def _writeTreeBranch(self,reg,layer):
        sl = self.getIfLayer(layer)
        if(sl is None):return
        startw = self.wire
        ly4 = layer * 4
        wl3 = self.lane * 3
        if(self.outLet.layer == layer):
            startw = self.outLet.wireVia.wire
        #
        count = 0
        wr = startw + 1
        while wr <= sl.end:
            if(wr != self.wire):
                for cx in self.inLets:
                    if(cx.layer != layer):continue
                    if(cx.wireVia.wire != wr):continue
                    if(cx.invert):continue
                    reg[wl3,ly4 + 3,wr * 3 - 1] = Blocks.repeatMinusZ
                    count = 0
                    break
                else:
                    if(count >= 3):
                        reg[wl3,ly4 + 3,wr * 3] = Blocks.repeatMinusZ
                        count = -1
                    count += 1
            else:
                wr += 1
                continue
            wr += 1
        wr = startw - 1
        while wr >= sl.start:
            if(wr != self.wire):
                for cx in self.inLets:
                    if(cx.layer != layer):continue
                    if(cx.wireVia.wire != wr):continue
                    if(cx.invert):continue
                    reg[wl3,ly4 + 3,wr * 3 + 1] = Blocks.repeatPlusZ
                    count = 0
                    break
                else:
                    if(count >= 3):
                        reg[wl3,ly4 + 3,wr * 3] = Blocks.repeatPlusZ
                        count = -1
                    count += 1
            else:
                wr -= 1
                continue
            wr -= 1
        return 12

    def writeTree(self,reg):
        startY = self.outLet.layer
        for layer in range(self.start,self.end + 1):
            self._writeTreeBranch(reg,layer)

    def write(self,reg):
        ll3 = self.lane * 3
        lw3 = self.wire * 3
        for layer in rangeOver(self):
            ly4 = layer * 4
            subL = self.getIfLayer(layer)
            for z in range(subL.start * 3,subL.end * 3 + 1):
                reg[ll3,ly4 + 2,z] = Blocks.baseZBlock
                reg[ll3,ly4 + 3,z] = Blocks.wireBlock
        olay = self.outLet.layer
        for layer in range(olay,self.end):
            reg[ll3 + 1,layer * 4 + 6,lw3    ] = Blocks.torchPlusX
            reg[ll3 + 1,layer * 4 + 5,lw3    ] = Blocks.wireBlock
            reg[ll3 + 1,layer * 4 + 4,lw3    ] = Blocks.baseYBlock
            reg[ll3    ,layer * 4 + 4,lw3    ] = Blocks.torchMinusX
            reg[ll3    ,layer * 4 + 3,lw3    ] = Blocks.wireBlock
            reg[ll3    ,layer * 4 + 2,lw3    ] = Blocks.baseZBlock
        for layer in range(self.start,olay):
            reg[ll3 - 1,layer * 4 + 3,lw3    ] = Blocks.redirBlock
            reg[ll3 - 1,layer * 4 + 4,lw3    ] = Blocks.torchUp
            reg[ll3 - 1,layer * 4 + 5,lw3    ] = Blocks.baseYBlock
            reg[ll3 - 1,layer * 4 + 6,lw3    ] = Blocks.torchUp
            reg[ll3 - 1,layer * 4 + 7,lw3    ] = Blocks.baseYBlock
        self.writeTree(reg)


    def __str__(self):
        return (f"<wire={self.wire},lane={self.lane} " +
                f"{self.start}-{self.end}>")

    def showContext(self):
        dat = str(self)
        if(self.outLet is not None):
            dat += f"{self.outLet}:"
        for ol in self.inLets:
            dat += f",{ol}"
        return dat


class Connection:
    __slots__ = ("wireVia","laneVia","layer","invert","dirLane","strength")
    def __init__(self,wire,lane,dirLane,invert,ref):
        self.wireVia = wire
        self.laneVia = lane
        self.invert  = invert
        self.dirLane = dirLane
        self.layer   = 0
        self.strength = 0
        if(self.dirLane):
            self.wireVia.outLets.append(self)
            self.laneVia.inLets .append(self)
        else:
            self.wireVia.inLet  = self
            self.laneVia.outLet = self
        self.update()

    def update(self):
        wire = self.wireVia.makeGetLayer(self.layer)
        lane = self.laneVia.makeGetLayer(self.layer)
        wire.update(self)
        lane.update(self)

    def write(self,reg):
        ll3 = self.laneVia.lane * 3
        ly4 = self.layer * 4
        ww3 = self.wireVia.wire * 3
        dx = 1
        dz = 1
        sw = self.wireVia.getIfLayer(self.layer)
        sl = self.laneVia.getIfLayer(self.layer)
        if(sl.end <= self.wireVia.wire):dz = -1
        if(sw.end <= self.laneVia.lane):dx = -1
        if(self.dirLane):
            if(self.invert):
                reg[ll3 + dx,ly4 + 1,ww3 + dz] = Blocks.redirBlock
                reg[ll3 + dx,ly4 + 2,ww3 + dz] = Blocks.torchUp
                reg[ll3 + dx,ly4 + 3,ww3 + dz] = Blocks.baseBlock
            else:
                reg[ll3     ,ly4 + 2,ww3] = Blocks.upBlock
                reg[ll3 + dx,ly4 + 2,ww3] = Blocks.wireBlock
                reg[ll3 + dx,ly4 + 1,ww3] = Blocks.baseBlock
        else:
            if(self.invert):
                if(self.laneVia.lane > sw.start):
                    reg[ll3 - 1,ly4 + 2,ww3] = Blocks.torchMinusX
                if(self.laneVia.lane < sw.end  ):
                    reg[ll3 + 1,ly4 + 2,ww3] = Blocks.torchPlusX
            else:
                if(self.laneVia.lane > sw.start):
                    reg[ll3 - 1,ly4 + 1,ww3] = Blocks.baseBlock
                    reg[ll3 - 1,ly4 + 2,ww3] = Blocks.repeatMinusX
                    if(reg[ll3 - 2,ly4 + 2,ww3].id == "minecraft:air"):
                        reg[ll3 - 2,ly4 + 2,ww3] = Blocks.baseBlock
                if(self.laneVia.lane < sw.end  ):
                    reg[ll3 + 1,ly4 + 1,ww3] = Blocks.baseBlock
                    reg[ll3 + 1,ly4 + 2,ww3] = Blocks.repeatPlusX
                    if(reg[ll3 + 2,ly4 + 2,ww3].id == "minecraft:air"):
                        reg[ll3 + 2,ly4 + 2,ww3] = Blocks.baseBlock

    def __str__(self):
        return f"[{self.wireVia.name}:{self.layer} {["","~"][self.invert]}{"wl"[self.dirLane]}]"



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

    def wireVCollide(self,wireV:WireVia,debug=False) -> list:
        collisions = []
        for wv in self.wires:
            if(wv is wireV):continue
            intersect = wireV.start <= wv.end and wv.start <= wireV.end
            if(not intersect):continue
            diff = abs(wireV.lane - wv.lane)
            diff += abs(wireV.wire - wv.wire)
            if(diff < 2):
                collisions.append(("(2026-09-09T22:20:54)",wireV,wv,None))
                continue
            if(wireV.wire == wv.wire):
                for sw in rangeOver(wireV):
                    subW = wireV.wireStack[sw]
                    othW = wv.getIfLayer(sw)
                    if(othW is None):continue
                    if(subW.start <= othW.end and othW.start <= subW.end):
                        collisions.append(("(2026-09-09T22:21:01)",wireV,wv,othW))
                        break
            owir = wv.inWire or wv.outWire
            olan = wv.inLane or wv.outLane
            if(olan is not None):
                lay = olan.layer
                fwir = wireV.getIfLayer(lay)
                if(fwir is not None and owir.parent.wire == wireV.wire):
                    if(fwir.start <= owir.end and owir.start <= fwir.end):
                        collisions.append(("(2026-09-09T22:21:11)",wireV,fwir,lay,wv,olan,owir))
                        continue
                if(olan.lane == wireV.lane and wireV.start <= olan.layer <= wireV.end):
                    if(olan.start <= wireV.wire <= olan.end):
                        collisions.append(("(2026-09-10T10:27:22)",wireV,wv,olan))
                        continue
        for lv in self.lanes:
            if(lv is wireV):continue
            intersect = wireV.start <= lv.end and lv.start <= wireV.end
            if(not intersect):continue
            diff = abs(wireV.lane - lv.lane)
            diff += abs(wireV.wire - lv.wire)
            if(diff < 2):
                collisions.append(("(2026-09-09T22:21:16)",wireV,lv,None))
                continue
            if(lv.lane == wireV.lane):
                for sl in rangeOver(wireV):
                    subL = lv.getIfLayer(sl)
                    if(subL is None):continue
                    if(subL.start <= wireV.wire <= subL.end):
                        collisions.append(("(2026-09-10T17:13:59)",wireV,lv,sl,subL))
                        break
            if(lv.wire == wireV.wire):
                for sl in rangeOver(lv):
                    subW = wireV.getIfLayer(sl)
                    if(subW is None):continue
                    if(subW.start <= lv.lane <= subW.end):
                        collisions.append(("(2026-09-10T18:54:46)",wireV,lv,sl,subW))
                        break
        if(wireV.inLane is not None):
            if(wireV.inLane.lane == wireV.lane):
                collisions.append(("(2026-09-27T19:02:25)",wireV,wireV.inLane))
            c = self.laneCollide(wireV.inLane,wireV.inLane.layer)
            collisions += c
            #print(c)
        if(wireV.outLane is not None):
            if(wireV.outLane.lane == wireV.lane):
                collisions.append(("(2026-09-27T19:02:25)",wireV,wireV.outLane))
            c = self.laneCollide(wireV.outLane,wireV.outLane.layer)
            collisions += c
            #print(c)
        if(debug and len(collisions) != 0):print(*(collisions[0]))
        return collisions

    def laneVCollide(self,laneV:WireVia,debug=False) -> list:
        collisions = []
        for wv in self.wires:
            if(wv is laneV):continue
            intersect = laneV.start <= wv.end and wv.start <= laneV.end
            if(not intersect):continue
            diff = abs(laneV.lane - wv.lane)
            diff += abs(laneV.wire - wv.wire)
            if(diff < 2):
                collisions.append(("(2026-09-10T09:09:39)",laneV,wv,None))
                continue
            olan = wv.inLane or wv.outLane
            owir = wv.inWire or wv.outWire
            if(olan is not None):
                lay = olan.layer
                flan = laneV.getIfLayer(lay)
                if(flan is not None and olan.lane == laneV.lane):
                    if(flan.start <= olan.end and olan.start <= flan.end):
                        collisions.append(("(2026-09-10T09:09:35)",laneV,wv,olan,lay))
                        continue
                if(flan is not None and olan.wire == laneV.wire):
                    if(owir.start <= laneV.wire <= owir.end):
                        collisions.append(("(2026-09-10T17:30:05)",laneV,wv,owir,lay))
                        continue
            if(wv.wire == laneV.wire):
                for sw in rangeOver(laneV):
                    subW = wv.getIfLayer(sw)
                    if(subW is None):continue
                    if(subW.start <= laneV.lane <= subW.end):
                        collisions.append(("(2026-09-10T17:19:59)",laneV,wv,sw,subW))
                        break
            if(wv.lane == laneV.lane):
                for sw in rangeOver(wv):
                    subL = laneV.getIfLayer(sw)
                    if(subL is None):continue
                    if(subL.start <= wv.wire <= subL.end):
                        collisions.append(("(2026-09-10T17:19:59)",laneV,wv,sw,subL,None))
                        break

        for lv in self.lanes:
            if(lv is laneV):continue
            intersect = laneV.start <= lv.end and lv.start <= laneV.end
            if(not intersect):continue
            diff = abs(laneV.lane - lv.lane)
            diff += abs(laneV.wire - lv.wire)
            if(diff < 2):
                collisions.append(("(2026-09-10T09:09:26)",laneV,lv,None))
                continue
            if(laneV.lane != lv.lane):continue
            for sl in rangeOver(laneV):
                subL = laneV.laneStack[sl]
                othL = lv.getIfLayer(sl)
                if(othL is None):continue
                if(subL.start <= othL.end and othL.start <= subL.end):
                    collisions.append(("(2026-09-10T09:09:21)",laneV,lv,othL))
                    break
        #collisions += self.wireCollide(laneV.inWire,wireV.inLane.layer)
        #collisions += self.laneCollide(laneV.inLane,wireV.inLane.layer)
        if(debug and len(collisions) != 0):print(*(collisions[0]))
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
                    collisions.append(("(2026-09-10T09:10:30)",wv,wb.inWire))
                    continue
            if(wv.outLane is not None):
                if(wv.outWire.start < wire.end and wire.start < wv.outWire.end):
                    collisions.append(("(2026-09-10T09:10:35)",wv,wb.outWire))
                    continue
            if(wv.wire != parent.wire):
                continue
            if(wire.start <= wv.lane <= wire.end):
                collisions.append(("(2026-09-10T09:10:40)",wv,None))
                continue
            subW = wv.getIfLayer(layer)
            if(subW is None):continue
            if(subW.start < wire.end and wire.start < subW.end):
                collisions.append(("(2026-09-10T09:10:43)",wv,subW))
                continue
        for lv in self.lanes:
            if(wv.start > layer or wv.end < layer):
                continue
            if(wire.start <= lv.lane <= wire.end):
                collisions.append(("(2026-09-10T09:10:47)",lv,None))
                continue
        return collisions

    def laneCollide(self,lane:LaneLane,layer:int):
        vparent = lane.parent
        if(type(lane) == LaneLane):parent = lane.parent
        if(type(lane) == WireLane):parent = lane
        collisions = []
        for wv in self.wires:
            if(wv is vparent):continue
            if(wv.start > layer or wv.end < layer):
                continue
            if(parent.lane == wv.lane):
                if(lane.start <= wv.wire <= lane.end):
                    collisions.append(("(2026-09-10T09:10:52)+",lane,layer,
                                       wv,parent.lane,wv.lane,None))
                    continue
            ol = wv.inLane or wv.outLane
            if(ol is not None):
                if(ol.lane == parent.lane and ol.layer == layer):
                    if(ol.start <= lane.end and lane.start <= ol.end):
                        collisions.append(("(2026-09-10T09:10:56)",wv,ol))
                        continue
        for lv in self.lanes:
            if(lv is parent):continue
            if(wv.start > layer or wv.end < layer):
                continue
            if(parent.lane != lv.lane):
                continue
                # collisions.append(("(2026-09-10T09:11:04)",lv,None))
            subL = lv.getIfLayer(layer)
            if(subL is None):continue
            if(subL.start <= lane.end and lane.start <= subL.end):
                collisions.append(("(2026-09-10T09:11:07)",lv,subL))
                continue
        return collisions

    def getCostDiffLaneV(self,laneV):
        cost = Cost()
        cost += laneV.getRawCost()
        ol = laneV.outLet
        if (ol is not    None): cost += ol.wireVia.getRawCost()
        for il in laneV.inLets: cost += il.wireVia.getRawCost()
        for il in laneV.inLets:
            cost += Cost(0,len(self.wireVCollide(il.wireVia)))
        if(ol is not None):
            cost += Cost(0,len(self.wireVCollide(ol.wireVia)))
        cost += Cost(0,len(self.laneVCollide(laneV)))
        return cost

    def getCostDiffWireV(self,wireV):
        cost = Cost()
        cost += wireV.getRawCost()
        il = wireV.inLet
        if (il is not     None): cost += il.laneVia.getRawCost()
        for ol in wireV.outLets: cost += ol.laneVia.getRawCost()
        for ol in wireV.outLets:
            cost += Cost(0,len(self.laneVCollide(ol.laneVia)))
        if(il is not None):
            cost += Cost(0,len(self.laneVCollide(il.laneVia)))
        cost += Cost(0,len(self.wireVCollide(wireV)))
        return cost

    def getCostDiffCross(self,cx):
        cost = self.getCostDiffWireV(cx.wireVia)
        cost += self.getCostDiffLaneV(cx.laneVia)
        return cost

    def getTotalCost(self,debug=False):
        cost = Cost()
        for w in self.wires:
            cost += w.getRawCost()
            cl = self.wireVCollide(w,debug=debug)
            cost += Cost(0,len(cl))
        for l in self.lanes:
            cost += l.getRawCost()
            cl = self.laneVCollide(l,debug=debug)
            cost += Cost(0,len(cl))
        return cost


    def tryCompactLaneV(self,temp:float,lv):
        baseC = self.getCostDiffLaneV(lv)
        oldW = lv.wire
        oldL = lv.lane
        minW = max(     1,oldW - OVER_MAX)
        minL = max(     1,oldL - OVER_MAX)
        maxW = min(999999,oldW + OVER_MAX)
        maxL = min(999999,oldL + OVER_MAX)
        for _ in range(TRYS):
            lv.wire = random.randrange(minW,maxW)
            lv.lane = random.randrange(minL,maxL)
            newC = self.getCostDiffLaneV(lv)
            if newC.testLt(temp,baseC):return True
        lv.wire = oldW
        for lan in range(minL,maxL):
            lv.lane = lan
            newC = self.getCostDiffLaneV(lv)
            if newC.testLt(temp,baseC):return True
        lv.lane = oldL
        for wir in range(minW,maxW):
            lv.wire = wir
            newC = self.getCostDiffLaneV(lv)
            if newC.testLt(temp,baseC):return True
        lv.wire = oldW
        lv.lane = oldL
        self.getCostDiffLaneV(lv)
        return False

    def tryCompactWireV(self,temp:float,wv):
        baseC = self.getCostDiffWireV(wv)
        oldW = wv.wire
        oldL = wv.lane
        minW = max(     1,oldW - OVER_MAX)
        minL = max(     1,oldL - OVER_MAX)
        maxW = min(999999,oldW + OVER_MAX)
        maxL = min(999999,oldL + OVER_MAX)
        for _ in range(TRYS):
            wv.wire = random.randrange(minW,maxW)
            wv.lane = random.randrange(minL,maxL)
            newC = self.getCostDiffWireV(wv)
            if newC.testLt(temp,baseC):return True
        wv.wire = oldW
        for lan in range(minL,maxL):
            wv.lane = lan
            newC = self.getCostDiffWireV(wv)
            if newC.testLt(temp,baseC):return True
        wv.lane = oldL
        for wir in range(minW,maxW):
            wv.wire = wir
            newC = self.getCostDiffWireV(wv)
            if newC.testLt(temp,baseC):return True
        wv.wire = oldW
        wv.lane = oldL
        ol = wv.inLane or wv.outLane
        if(ol is None):
            self.getCostDiffWireV(wv)
            return False
        oldL = ol.lane
        for lan in range(1,wv.lane + 4): # TODO
            ol.lane = lan
            newC = self.getCostDiffWireV(wv)
            if newC.testLt(temp,baseC):return True
        ol.lane = oldL
        return False

    def tryCompactCross(self,temp:float,cx):
        baseC = self.getCostDiffCross(cx)
        wirW = cx.wireVia.wire
        wirL = cx.wireVia.lane
        lanW = cx.laneVia.wire
        lanL = cx.laneVia.lane
        minWW = max(     1,wirW - OVER_MAX)
        minWL = max(     1,wirL - OVER_MAX)
        maxWW = min(999999,wirW + OVER_MAX)
        maxWL = min(999999,wirL + OVER_MAX)
        minLW = max(     1,lanW - OVER_MAX)
        minLL = max(     1,lanL - OVER_MAX)
        maxLW = min(999999,lanW + OVER_MAX)
        maxLL = min(999999,lanL + OVER_MAX)
        oldY = cx.layer
        for _ in range(TRYS):
            cx.wireVia.wire = random.randrange(minWW,maxWW)
            cx.wireVia.lane = random.randrange(minWL,maxWL)
            cx.laneVia.wire = random.randrange(minLW,maxLW)
            cx.laneVia.lane = random.randrange(minLL,maxLL)
            cx.layer        = random.randrange(0,oldY + OVER_MAX)
            newC = self.getCostDiffCross(cx)
            if newC.testLt(temp,baseC):return True
        cx.wireVia.lane = wirL
        cx.laneVia.wire = lanW
        for _ in range(TRYS):
            cx.wireVia.wire = random.randrange(minWW,maxWW)
            cx.laneVia.lane = random.randrange(minLL,maxLL)
            cx.layer        = random.randrange(0,oldY + OVER_MAX)
            newC = self.getCostDiffCross(cx)
            if newC.testLt(temp,baseC):return True
        cx.wireVia.wire = wirW
        cx.laneVia.lane = lanL
        for lay in range(0,oldY + OVER_MAX):
            cx.layer = lay
            newC = self.getCostDiffCross(cx)
            if newC.testLt(temp,baseC):return True
        cx.layer        = oldY
        self.getCostDiffCross(cx)
        return False

    def layout(self):
        countWire = 100
        for wv in self.wires:
            wv.wire = monotonicWireCounter()
            wv.lane = monotonicLaneCounter()
            wv.reset()
        for lv in self.lanes:
            lv.wire = monotonicWireCounter()
            lv.lane = monotonicLaneCounter()
            lv.reset()
        for cx in self.cross:
            #cx.layer = random.randrange(0,4)
            cx.layer = 0
            cx.update()

    def compact(self,temp:float) -> bool:
        if(DO_FORCE_CHECK):prev = self.getTotalCost()
        didChange = False
        if(DO_FORCE_CHECK):print("wires")
        random.shuffle(self.wires)
        for wv in self.wires:
            ch = self.tryCompactWireV(temp,wv)
            didChange |= ch
            if(DO_FORCE_CHECK and ch):
                next = self.getTotalCost()
                if(next.errors > prev.errors):
                    print("(12:55:46)",wv.showContext())
                    if(wv.inLet is not None):
                        print(wv.inLet.laneVia.showContext())
                    for ol in wv.outLets:
                        print(ol.laneVia.showContext())
                    breakpoint()
                    next = self.getTotalCost(True)
                    return False
                print(f"{prev} -> {next}")
                prev = next
        if(DO_FORCE_CHECK):print("lanes")
        random.shuffle(self.lanes)
        for lv in self.lanes:
            ch = self.tryCompactLaneV(temp,lv)
            didChange |= ch
            if(DO_FORCE_CHECK and ch):
                next = self.getTotalCost()
                if(next.errors > prev.errors):
                    print("(12:55:40)",lv.showContext())
                    if(lv.outLet is not None):
                        print(lv.outLet.wireVia.showContext())
                    for ol in lv.inLets:
                        print(ol.laneVia.showContext())
                    breakpoint()
                    next = self.getTotalCost(True)
                    return False
                print(f"{prev} -> {next}")
                prev = next
        if(DO_FORCE_CHECK):print("cross")
        for cx in self.cross:
            ch = self.tryCompactCross(temp,cx)
            didChange |= ch
            if(DO_FORCE_CHECK and ch):
                next = self.getTotalCost()
                if(next.errors > prev.errors):
                    print("(19:16:38)",cx.wireVia.showContext(),
                          cx.laneVia.showContext())
                    breakpoint()
                    next = self.getTotalCost(True)
                    return False
                print(f"{prev} -> {next}")
                prev = next
            pass

        return didChange


    def write(self) -> tuple:
        maxX,maxY,maxZ = 0,0,0
        for l in self.lanes:
            maxZ = max(maxZ,l.wire)
            maxY = max(maxY,l.end)
            maxX = max(maxX,l.lane)
        for w in self.wires:
            maxZ = max(maxZ,w.wire)
            maxY = max(maxY,w.end)
            maxX = max(maxX,w.lane)
            olan = w.inLane or w.outLane
        print("lanes:")
        for o in self.lanes: print(f"- {o}")
        print("wires:")
        for o in self.wires: print(f"- {o}")
        print(maxX,maxY,maxZ)

        #reg = Region(0,0,0,maxX * 3 + 1,maxY * 4 + 4,maxZ * 3 + 1)
        #reg = Region(0,0,0,maxX * 3 + 3,maxY * 4 + 4,maxZ * 3 + 3)
        reg = Region(0,0,0,maxX * 3 + 4,maxY * 4 + 4,maxZ * 3 + 4)
        schem = reg.as_schematic(
                name=Blocks.name,
                author=Blocks.author,
                description=Blocks.description)

        for wv in self.wires:wv.write(reg)
        for lv in self.lanes:lv.write(reg)
        for cx in self.cross:cx.write(reg)

        schem.save(Blocks.output)
        print(Blocks.output)
        return ((maxX,maxY,maxZ),self.getTotalCost())





def main(settings,module,timeTable):
    timeTable.append(time.time())
    safeCurruptBlocks(settings)
    m = module.carbonCopy(Module,WireVia,LaneVia,Connection)
    m.layout()
    m.getTotalCost(1)
    temp  = int  (Blocks.temperatur)
    decay = float(Blocks.decay     )
    counter = 0
    timeTable.append(time.time())
    #while False and m.compact(temp):
    while m.compact(temp):
        temp *= decay
        counter += 1
        print(counter,end="\b"*10,flush=True)
    dim,cost,*_ = m.write()
    print(f"after {counter} steps. Dimension:{dim}")
    print(f"cost:{str(cost)}")
    timeTable.append(time.time())


