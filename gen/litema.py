
#import litemapy
try:
    from gen.util import Cost,LENGTH_MAX,HEAT_SPREAD,rangeOver
except:
    from util import Cost,LENGTH_MAX,HEAT_SPREAD,rangeOver

from litemapy import Region, BlockState, Schematic
import random

laneCounter = 0
def monotonicLaneCounter(jump=0):
    global laneCounter
    laneCounter = max(jump,laneCounter)
    laneCounter += 1
    return laneCounter - 1
wireCounter = 0
def monotonicWireCounter(jump=0):
    global wireCounter
    wireCounter = max(jump,wireCounter)
    wireCounter += 1
    return wireCounter - 1


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
    __slots__ = ("parent","layer","lane","wire","inlet","outlet","child",
                 "start","end")
    def __init__(self,parent,layer,lane):
        self.parent = parent
        self.lane   = lane
        self.layer  = layer
        self.wire   = 0
        self.inlet  = None
        self.outlet = None
        self.child  = None
        self.update()

    def update(self,cross=None):
        self.start  = min(self.parent.wire,self.wire)
        self.end    = max(self.parent.wire,self.wire)

    def reset(self,cross=None):self.update(cross)

    def setInlet(self,let):
        self.inlet  = let

    def setOutlet(self,let):
        self.outlet = let

    def setChildWire(self,wir):
        self.child  = wir

    def getRawCost(self):
        return Cost(abs(self.parent.wire - self.child.parent.wire),0)


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
        refPoint = [int(x) for x in splitName]
        while len(refPoint) < 3:
            refPoint.insert(0,-1)
        return refPoint

    def setupInput(self):
        self.inputPoint = WireVia.calcFixedPoint(self.name)
        if(self.inputPoint[-1] == -1):self.inputPoint[-1] = 0
        self.inputPoint[-2] = monotonicLaneCounter(self.inputPoint[-2])
        self.inLane = WireLane(self,
                               layer=self.inputPoint[-1],
                               lane=self.inputPoint[-2])
        self.inWire = WireWire(self.inLane)
        self.inLane.setChildWire(self.inWire)
        self.makeGetLayer(self.inputPoint[-1])

    def setupOutput(self):
        self.outputPoint = WireVia.calcFixedPoint(self.name)
        if(self.outputPoint[-1] == -1):self.outputPoint[-1] = 0
        self.outputPoint[-2] = monotonicWireCounter(self.outputPoint[-2])
        self.outLane = WireLane(self,
                                layer=self.outputPoint[-1],
                                lane=self.outputPoint[-2])
        self.outWire = WireWire(self.outLane)
        self.outLane.setChildWire(self.outWire)
        self.makeGetLayer(self.outputPoint[-1])

    def makeGetLayer(self,layer):
        while(len(self.wireStack) <= layer):
            self.wireStack.append(WireWire(self))
        return self.wireStack[layer]

    def getIfLayer(self,layer):
        if(len(self.wireStack) <= layer):return None
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
            cost += self.inWire.getRawCost()
        if(self.outLane is not None):
            cost += self.outLane.getRawCost()
            self.outWire.reset()
            self.outWire.start = 0
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
        cost += Cost(self.end - self.start,0)
        return cost

    def __str__(self):
        return (f"{self.name} : wire={self.wire},lane={self.lane} " +
                f"{self.start}-{self.end}")


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
        return self.laneStack[layer]

    def reset(self):
        self.start  = LENGTH_MAX
        self.end    = 0

    def getRawCost(self):
        cost = Cost()
        self.reset()
        #
        for cx in self.inLets:
            cx.update()
            self.start = min(self.start,cx.layer)
            self.end   = max(self.end  ,cx.layer)
        if(self.outLet is not None):
            self.outLet.update()
            self.start = min(self.start,self.outLet.layer)
            self.end   = max(self.end  ,self.outLet.layer)
        for w in rangeOver(self):
            cost += self.laneStack[w].getRawCost()
        cost += Cost(self.end - self.start,0)
        return cost

    def __str__(self):
        return (f"wire={self.wire},lane={self.lane} " +
                f"{self.start}-{self.end}")


class Connection:
    __slots__ = ("wireVia","laneVia","layer","invert","dirLane")
    def __init__(self,wire,lane,dirLane,invert,ref):
        self.wireVia = wire
        self.laneVia = lane
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
        wire = self.wireVia.makeGetLayer(self.layer)
        lane = self.laneVia.makeGetLayer(self.layer)
        wire.update(self)
        lane.update(self)



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
            if(wv is wireV):continue
            intersect = wireV.start <= wv.end and wv.start <= wireV.end
            if(not intersect):continue
            diff = abs(wireV.lane - wv.lane)
            diff += abs(wireV.wire - wv.wire)
            if(diff < 2):
                collisions.append((wv,None))
                continue
            for sw in rangeOver(wireV):
                subW = wireV.wireStack[sw]
                othW = wv.getIfLayer(sw)
                if(othW is None):continue
                if(subW.start <= othW.end and othW.start <= subW.end):
                    collisions.append((wv,othW))
                    break
            if(wv.inLane is not None):
                owir = wv.inWire
                lay = wv.inLane.layer
                fwir = wireV.getIfLayer(lay)
                if(fwir is not None):
                    if(fwir.start <= owir.end and owir.start <= fwir.end):
                        collisions.append((wv,owir))
                        continue
            if(wv.outLane is not None):
                owir = wv.outWire
                lay = wv.outLane.layer
                fwir = wireV.getIfLayer(lay)
                if(fwir is not None):
                    if(fwir.start <= owir.end and owir.start <= fwir.end):
                        collisions.append((wv,owir))
                        continue
        for lv in self.lanes:
            if(lv is wireV):continue
            intersect = wireV.start <= lv.end and lv.start <= wireV.end
            if(not intersect):continue
            diff = abs(wireV.lane - lv.lane)
            diff += abs(wireV.wire - lv.wire)
            if(diff < 2):
                collisions.append((lv,None))
                continue
        if(wireV.inLane is not None):
            collisions += self.laneCollide(wireV.inLane,wireV.inLane.layer)
        if(wireV.outLane is not None):
            collisions += self.laneCollide(wireV.outLane,wireV.outLane.layer)
        return collisions

    def laneVCollide(self,laneV:WireVia) -> list:
        collisions = []
        for wv in self.wires:
            if(wv is laneV):continue
            intersect = laneV.start <= wv.end and wv.start <= laneV.end
            if(not intersect):continue
            diff = abs(laneV.lane - wv.lane)
            diff += abs(laneV.wire - wv.wire)
            if(diff < 2):
                collisions.append((wv,None))
                continue
            if(wv.inLane is not None):
                olan = wv.inLane
                lay = olan.layer
                flan = laneV.getIfLayer(lay)
                if(flan is not None):
                    if(flan.start <= olan.end and olan.start <= flan.end):
                        collisions.append((wv,olan))
                        continue
            if(wv.outLane is not None):
                olan = wv.outLane
                lay = olan.layer
                flan = laneV.getIfLayer(lay)
                if(flan is not None):
                    if(flan.start <= olan.end and olan.start <= flan.end):
                        collisions.append((wv,olan))
                        continue
        for lv in self.lanes:
            if(lv is laneV):continue
            intersect = laneV.start <= lv.end and lv.start <= laneV.end
            if(not intersect):continue
            diff = abs(laneV.lane - lv.lane)
            diff += abs(laneV.wire - lv.wire)
            if(diff < 2):
                collisions.append((lv,None))
                continue
            for sl in rangeOver(laneV):
                subL = laneV.laneStack[sl]
                othL = wv.getIfLayer(sl)
                if(othL is None):continue
                if(subL.start <= othL.end and othL.start <= subL.end):
                    collisions.append((lv,othL))
                    break
        #collisions += self.wireCollide(laneV.inWire,wireV.inLane.layer)
        #collisions += self.laneCollide(laneV.inLane,wireV.inLane.layer)
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
            if(wv is parent):continue
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
            if(lv is parent):continue
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

    def getCostDiffLaneV(self,laneV):
        cost = Cost()
        cost += laneV.getRawCost()
        cost += laneV.outLet.wireVia.getRawCost()
        ol = laneV.outLet
        if (ol is not    None): cost += ol.laneVia.getRawCost()
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

    def getTotalCost(self):
        cost = Cost()
        for w in self.wires:
            cost += w.getRawCost()
            cl = self.wireVCollide(w)
            cost += Cost(0,len(cl))
        for l in self.lanes:
            cost += l.getRawCost()
            cl = self.laneVCollide(l)
            cost += Cost(0,len(cl))
        return cost


    def tryCompactLaneV(self,temp:float,lv):
        baseC = self.getCostDiffLaneV(lv)
        TRYS = 100
        oldW = lv.wire
        oldL = lv.lane
        for _ in range(TRYS):
            lv.wire = random.randrange(0,oldW + 4)
            lv.lane = random.randrange(0,oldL + 4)
            newC = self.getCostDiffLaneV(lv)
            if newC.testLt(temp,baseC):return True
        lv.wire = oldW
        for lan in range(oldL + 5):
            lv.lane = lan
            newC = self.getCostDiffLaneV(lv)
            if newC.testLt(temp,baseC):return True
        lv.lane = oldL
        for wir in range(oldW + 5):
            lv.wire = wir
            newC = self.getCostDiffLaneV(lv)
            if newC.testLt(temp,baseC):return True
        lv.wire = oldW
        lv.lane = oldL
        self.getCostDiffLaneV(lv)
        return False

    def tryCompactWireV(self,temp:float,wv):
        baseC = self.getCostDiffWireV(wv)
        TRYS = 100
        oldW = wv.wire
        oldL = wv.lane
        for _ in range(TRYS):
            wv.wire = random.randrange(0,oldW + 4)
            wv.lane = random.randrange(0,oldL + 4)
            newC = self.getCostDiffWireV(wv)
            if newC.testLt(temp,baseC):return True
        wv.wire = oldW
        for lan in range(oldL + 5):
            wv.lane = lan
            newC = self.getCostDiffWireV(wv)
            if newC.testLt(temp,baseC):return True
        wv.lane = oldL
        for wir in range(oldW + 5):
            wv.wire = wir
            newC = self.getCostDiffWireV(wv)
            if newC.testLt(temp,baseC):return True
        wv.wire = oldW
        wv.lane = oldL
        self.getCostDiffWireV(wv)
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
            cx.layer = random.randrange(0,16)
            cx.update()

    def compact(self,temp:float) -> bool:
        prev = self.getTotalCost()
        didChange = False
        for lv in self.lanes:
            ch = self.tryCompactLaneV(temp,lv)
            didChange |= ch
            if(ch):
                next = self.getTotalCost()
                print(f"{prev} -> {next}")
                prev = next
        for wv in self.wires:
            ch = self.tryCompactWireV(temp,wv)
            didChange |= ch
            if(ch):
                next = self.getTotalCost()
                print(f"{prev} -> {next}")
                prev = next
        for cx in self.cross:
            pass

        return didChange


    def write(self) -> tuple:
        maxX,maxY,maxZ = 0,0,0
        for cx in self.cross:
            maxY = max(maxY,cx.layer)
            maxX = max(maxX,cx.wireVia.lane)
            maxZ = max(maxX,cx.laneVia.wire)
        print("lanes:")
        for o in self.lanes: print(f"- {o}")
        print("wires:")
        for o in self.wires: print(f"- {o}")
        return ((maxX,maxY,maxZ),self.getTotalCost())





def main(settings,module):
    safeCurruptBlocks(settings)
    m = module.carbonCopy(Module,WireVia,LaneVia,Connection)
    m.layout()
    temp = 100
    counter = 0
    #while False and m.compact(temp):
    while m.compact(temp):
        temp *= 0.75
        counter += 1
        print(counter,end="\b"*10,flush=True)
    dim,cost,*_ = m.write()
    print(f"after {counter} steps. Dimension:{dim}")
    print(f"cost:{str(cost)}")

def debugMain():
    class Ds:pass
    isIo = Ds()
    isIo.isIO = True
    safeCurruptBlocks({})

    inW = WireVia("inp",isIo,True,False)
    ouW = WireVia("out",isIo,False,True)
    lan = LaneVia(None)
    c1  = Connection(inW,lan,True,False,None)
    c2  = Connection(ouW,lan,False,True,None)
    m = Module([inW,ouW],[lan],[c1,c2],None)
    m.layout()
    print(m.getTotalCost())
    print("inW",m.getCostDiffWireV(inW))
    print("ouW",m.getCostDiffWireV(ouW))
    print("lan",m.getCostDiffLaneV(lan))
    print(m.getTotalCost())

    temp = 100
    counter = 0
    """
    #while False and m.compact(temp):
    while m.compact(temp):
        temp *= 0.75
        counter += 1
        print(counter,end="\b"*10,flush=True)
    # """
    dim,cost,*_ = m.write()
    print(f"after {counter} steps. Dimension:{dim}")
    print(f"cost:{str(cost)}")

if __name__ == "__main__":debugMain()

