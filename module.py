
import random
import uuid

LENGTH_MAX = 999_999
HEAT_SPREAD = 10

def __PrintError  (*d,**da):print("\x1b[0;31m",*d,"\x1b[0m",**da)
def __PrintWarning(*d,**da):print("\x1b[0;33m",*d,"\x1b[0m",**da)

def getRandName():
    return f"-{uuid.uuid4()}"
def getRandNameSmall():
    return f"-{uuid.uuid4()}"[:9]

def parseAssignSet(token,remap:dict)->None:
    for assignToken in token.lst[0].lst:
        assData = assignToken.lst[1].data
        remap[assignToken.lst[0].data] = remap.get(assData,assData)
    return None

class Connection:
    __slots__ = ("token","wire","lane","dirLane","invert")
    def __init__(self,token,wire,lane,dirLane=True,invert=False):
        self.token   = token
        self.wire    = wire
        self.lane    = lane
        self.dirLane = dirLane
        self.invert  = invert

    def delete(self) -> Connection:
        if(self.dirLane):
            # MAY REMOVE TRY
            try:
                self.wire.outLets.remove(self)
                self.lane.inLets.remove(self)
            except Exception as e:
                __PrintError(e)
                __PrintError(self.wire)
                __PrintError(self.lane)
                __PrintError(self.token.showWhere())
                raise e
        else:
            if(self.wire. inLet is self):self.wire. inLet = None
            if(self.lane.outLet is self):self.lane.outLet = None
        return self

    def insert(self,debug=False):
        if(self.dirLane):
            if(self not in self.wire.outLets):
                self.wire.outLets.append(self)
            if(self not in self.lane.inLets ):
                self.lane.inLets .append(self)
        else:
            self.wire.inLet  = self
            self.lane.outLet = self

    def __str__(self):
        dat = f"<Connection:{' ~'[self.invert]}{"wl"[self.dirLane]} {self.wire.name}>"
        return dat

class Wire:
    __slots__ = ("layer","name","isIO","token",
                 "inLet","outLets")
    def __init__(self,name,token):
        self.token   = token
        self.name    = name
        self.inLet   = None
        self.outLets = []
        self.isIO = False

    def addInto(self,let:Connection):
        self.inLet = let

    def addOutOf(self,let:Connection):
        self.outLets.append(let)

    def __str__(self):
        return f"<Wire:{self.name}>"

class Lane:
    __slots__ = ("inLets","token","outLet")
    def __init__(self,token):
        self.inLets = []
        self.outLet = None
        self.token = token

    def addInto(self,let:Connection):
        self.inLets.append(let)

    def addOutOf(self,let:Connection):
        self.outLet = let

    def __str__(self):
        return f"<Lane:{self.outLet},{"|".join([str(x) for x in self.inLets])}>"

class Module:
    lookup = dict()
    __slots__ = ("name","token","wires","lanes","cross",
                 "inputWires","outputWires","inputName","outputName",
                 "remap","isGenerating","hasGenerated")
    def __init__(self,name,token,remap = {}):
        Module.lookup[name] = self
        self.lanes  = []
        self.wires  = []
        self.token  = token
        self.name   = name
        self.cross  = []
        self.isGenerating = False
        self.hasGenerated = False
        self.remap = remap
        self.inputWires  = []
        self.outputWires = []
        self.inputName   = []
        self.outputName  = []

    def findWireByName(self,nam) -> Wire:
        for w in self.wires:
            if(w.name == nam):
                return w
        return None

    def maybeAddWire(self,nam,token) -> Wire:
        wir = self.findWireByName(nam)
        if(wir is not None):
            return wir
        wir = Wire(nam,token)
        self.wires.append(wir)
        return wir

    def setupIOWire(self,remap:dict):
        for tok in self.token.args[1].lst:
            name = tok.getWireName(remap)
            self.inputName.append(name)
            if(tok.data == ":"):
                splt = name.split(":")
                cnt = int(splt[-1])
                nam = ":".join(splt[:-1])
                for c in range(cnt):
                    wir = self.maybeAddWire(f"{nam}:{c}",tok)
                    wir.isIO = True
                    self.inputWires.append(wir)
            else:
                wir = self.maybeAddWire(name,tok)
                wir.isIO = True
                self.inputWires.append(wir)
        for tok in self.token.args[2].lst:
            name = tok.getWireName(remap)
            self.outputName.append(name)
            if(tok.data == ":"):
                splt = name.split(":")
                cnt = int(splt[-1])
                nam = ":".join(splt[:-1])
                for c in range(cnt):
                    wir = self.maybeAddWire(f"{nam}:{c}",tok)
                    wir.isIO = True
                    self.outputWires.append(wir)
            else:
                wir = self.maybeAddWire(name,tok)
                wir.isIO = True
                self.outputWires.append(wir)
    # def setupIOWire

    def generate(self,callee=None):
        if(self.hasGenerated):return
        if(self.isGenerating):
            if(callee is not None):
                __PrintError(callee.token.showWhere())
            raise Exception(f"cyclic Dependency! for \n{self.token.showWhere()}")
        self.setupIOWire(self.remap)
        self.isGenerating = True
        for tok in self.token.lst:
            self.parseToken(tok,self.remap)
        self.hasGenerated = True

    def parseToken(self,token,remap={}) -> Wire:
        if(token.typ == "word" and token.data == "set"):
            return parseAssignSet(token,remap)
        if(token.typ == "word" and token.data == "repeat"):
            return self.parseRepeat(token,remap)
        if(token.isWire()):
            w = self.maybeAddWire(token.getWireName(remap),token)
            if(token.invert):
                ilan = Lane(token)
                wout = self.maybeAddWire(getRandName(),token)
                self.lanes.append(ilan)
                cx = Connection(token,w,ilan,True,True)
                self.cross.append(cx)
                cx.insert()
                cx = Connection(token,wout,ilan,False,False)
                self.cross.append(cx)
                cx.insert()
                return wout
            return w
        """if(token.typ == "word"):
            return self.maybeAddWire(remap.get(token.data,token.data),token)
        if(token.typ == ":"):
            wName = ":".join([remap.get(x.data,x.data) for x in token.lst])
            return self.maybeAddWire(wName,token)
        """
        if(token.typ == "="):
            return self.parseWireSet(token,remap)
        if(token.typ == "&" or token.typ == "|"):
            return self.parseOperationLane(token,remap)
        if(token.typ == "@"):
            return self.parseSubModule(token,remap)

    def parseOperationLane(self,token,remap:dict) -> Wire:
        lan = Lane(token)
        inverting = token.typ == "&"
        self.lanes.append(lan)
        outWire = self.maybeAddWire(getRandName(),token)
        for subToken in token.lst:
            fetchWire = self.parseToken(subToken,remap)
            subInvert = inverting != subToken.invert
            let = Connection(subToken,fetchWire,lan,True,subInvert)
            let.insert()
            self.cross.append(let)
        #
        subInvert = inverting != token.invert
        let = Connection(token,outWire,lan,False,subInvert)
        let.insert()
        self.cross.append(let)
        return outWire

    def parseWireSet(self,token,remap:dict) -> Wire:
        baseWir = self.maybeAddWire(token.lst[0].getWireName(remap),token)
        gotWire = self.parseToken(token.lst[1],remap)
        """
        for oLed in gotWire.outLets:
            baseWir.addOutOf(oLed)
            oLed.wire = baseWir
        baseWir.addInto(gotWire.inLet)
        gotWire.inLet.wire = baseWir
        self.wires.remove(gotWire)
        """
        lan = Lane(token)
        self.lanes.append(lan)
        #
        cx = Connection(token,gotWire,lan)
        self.cross.append(cx)
        cx.insert(True)
        cx = Connection(token,baseWir,lan,False)
        self.cross.append(cx)
        cx.insert(True)
        return baseWir

    def parseRepeat(self,token,remap:dict) -> None:
        remap = remap.copy()
        iterator = token.args[0]
        try:
            varName  = iterator.lst[0].data
            iStart   = iterator.lst[1].data
            iStop    = iterator.lst[2].data
            varStart = int(remap.get(iStart,iStart))
            varStop  = int(remap.get(iStop ,iStop ))
        except Exception as e:
            __PrintError(remap)
            __PrintError(e)
            raise Exception(f"Error with {token.showWhere()}")
        for count in range(varStart,varStop):
            remap[varName] = str(count)
            for subToken in token.lst:
                self.parseToken(subToken,remap)
        return None

    def parseSubModule(self,token,remap:dict) -> None:
        oMod = Module.lookup.get(token.args[0].data)
        if(oMod is None):
            __PrintError(self.token.showWhere())
            raise Exception(f"Not found module of name {token.args[0].data}")
        oMod.generate(self)
        mapping = oMod.createTranslation(token,remap,token.lst[0].lst,token.lst[1].lst)
        #"""
        for oLan in oMod.lanes:
            mLan = Lane(token)
            self.lanes.append(mLan)
            for cx in oLan.inLets:
                cWire = self.maybeAddWire(mapping[cx.wire.name],token)
                let = Connection(cx.token,cWire,mLan,cx.dirLane,cx.invert)
                self.cross.append(let)
                let.insert()
            cx = oLan.outLet
            cWire = self.maybeAddWire(mapping[cx.wire.name],token)
            let = Connection(cx.token,cWire,mLan,cx.dirLane,cx.invert)
            self.cross.append(let)
            let.insert()
            #outLet.append(CrossLet(cWire,cx.dirUp,cx.inverting))
            #self.connections.append(Connection(inLets,outLet))
        #"""
        return None

    def createTranslation(self,token,remap,inWire,outWire):
        if(len(inWire) != len(self.inputName)):
            raise Exception("Not the same input ammount as in definition\n" + 
                            f"{self}\n{token.showWhere()}")
        if(len(outWire) != len(self.outputName)):
            raise Exception("Not the same output ammount as in definition\n" + 
                            f"{self}\n{token.showWhere()}")
        translation = {}
        for toWire,nameWire in zip(inWire,self.inputName):
            if(":" in nameWire):
                # TODO
                splt = nameWire.split(":")
                count = int(splt[-1])
                prefix = ":".join(splt[:-1])
                for c in range(count):
                    translation[f"{prefix}:{c}"] = f"{toWire.getWireName(remap)}:{c}"
            else:
                translation[nameWire] = toWire.getWireName(remap)
        for toWire,nameWire in zip(outWire,self.outputName):
            if(":" in nameWire):
                # TODO
                splt = nameWire.split(":")
                count = int(splt[-1])
                prefix = ":".join(splt[:-1])
                for c in range(count):
                    translation[f"{prefix}:{c}"] = f"{toWire.getWireName(remap)}:{c}"
            else:
                translation[nameWire] = toWire.getWireName(remap)
        # hidden wires
        for wir in self.wires:
            if(wir.name not in translation):
                if(len(wir.name) > 30):
                    translation[wir.name] = getRandName()
                    continue
                    #translation[wir.name] = wir.name
                #translation[wir.name] = f"{self.name}@{wir.name}{getRandNameSmall()}"
                translation[wir.name] = f"{wir.name}@{self.name}{getRandNameSmall()}"
        return translation

    def reduceConnections(self) -> bool:
        didChange = False
        for wir in self.wires:
            if(wir.isIO):continue
            if(wir.inLet is None):
                raise Exception(f"Found wire with zero inlets! {wir.name}\n" +
                                f"{wir.token.showWhere()}")
            if(len(wir.outLets) == 0):
                __PrintWarning(f"removing wire {wir.name}")
                lanR = wir.inLet.lane
                for cx in lanR.inLets:
                    self.cross.remove(cx)
                    cx.delete()
                self.lanes.remove(lanR)
                self.wires.remove(wir)
                continue
        for lan in self.lanes:
            #if(lan.isIO):continue
            if(len(lan.inLets) == 0):
                raise Exception("This has gone to an invalid state, pleas fix!\n" +
                                f"{lan.token.showWhere()}")
            if(len(lan.inLets) == 1):
                invert = lan.inLets[0].invert != lan.outLet.invert
                print(f"{lan}\n" + 
                      f"{lan.token.showWhere()}")
                print(f"{lan.inLets[0].wire.inLet.lane}")
                if(not lan.inLets[0].wire.isIO):
                    didChange = True
                    owir = lan.inLets[0].wire
                    owir.inLet.wire = lan.outLet.wire
                    owir.inLet.invert = owir.inLet.invert != invert
                    #owir.inLet.wire.inLet = owir.inLet
                    self.cross.remove(lan.inLets[0].delete())
                    self.cross.remove(lan.outLet.delete())
                    self.lanes.remove(lan)
                    self.wires.remove(owir)
                elif(not lan.outLet.wire.isIO):
                    didChange = True
                    owir = lan.outLet.wire
                    for cx in owir.outLets:
                        cx.wire = lan.inLets[0].wire
                        cx.wire.outLets.append(cx)
                        cx.invert = cx.invert != invert
                    self.cross.remove(lan.inLets[0].delete())
                    self.cross.remove(lan.outLet.delete())
                    self.lanes.remove(lan)
                    self.wires.remove(owir)
            for lan2 in self.lanes:
                if(lan is lan2):continue
                usedWires = lan2.inLets.copy()
                for w in lan.inLets:
                    if(w not in usedWires):
                        usedWires = None
                        break
                    usedWires.remove(w)
                if(usedWires is None or len(usedWires) > 0):
                    continue
                print("We have some similar wires!")

    def __str__(self):
        dat = f"<Module: {self.name}\n"
        dat += f"wires:{' | '.join([x.name for x in self.wires])}\n"
        dat += f"lanes:{'\n'.join([' - ' + str(x) for x in self.lanes])}\n"
        dat += ">"
        return dat

    def carbonCopy(self,
                   newModule:type,newWire      :type,
                   newLane  :type,newConnection:type):
        """
        """
        wireMap = {}
        laneMap = {}
        corsList = []
        wireList = []
        laneList = []
        return None


def executeTokenList(tokenList:list[Token]):
    remap = {}
    for token in tokenList:
        if(token.typ == "word" and token.data == "set"):
            parseAssignSet(token,remap)
        if(token.typ == "word" and token.data in ["module","component"]):
            mod = Module(token.args[0].data,token,remap.copy())



