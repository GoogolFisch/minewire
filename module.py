
import random
import uuid

LENGTH_MAX = 999_999
HEAT_SPREAD = 10

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

    def __str__(self):
        return f"<Connection:>"

class Wire:
    __slots__ = ("layer","name",
                 "inLet","outLets")
    def __init__(self,name):
        self.name    = name
        self.inLet   = None
        self.outLets = []

    def addInto(self,let):
        self.inLet = let

    def addOutOf(self,let):
        self.outLets.append(let)

    def __str__(self):
        return f"<Wire:{self.viaO.name}>"

class Lane:
    __slots__ = ("layer","inLets","outLet")
    def __init__(self):
        self.inLets = []
        self.outLet = None

    def addInto(self,let):
        self.inLets.append(let)

    def addOutOf(self,let):
        self.outLet = let

    def __str__(self):
        return f"<Lane:{self.lane}-{self.layer}"

class Module:
    lookup = dict()
    __slots__ = ("name","token","wires","lanes","cross",
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

    def findWireByName(self,nam) -> Wire:
        for w in self.wires:
            if(w.name == nam):
                return w
        return None

    def maybeAddWire(self,nam) -> Wire:
        wir = self.findWireByName(nam)
        print(nam)
        if(wir is None):
            return wir
        wir = Wire(nam)
        self.wires.append(wir)
        return wir

    def generate(self,callee=None):
        if(self.hasGenerated):return
        if(self.isGenerating):
            if(callee is not None):
                print(callee.token.showWhere())
            raise Exception(f"cyclic Dependency! for \n{self.token.showWhere()}")
        self.isGenerating = True
        print(self.name)
        for tok in self.token.lst:
            print("-",tok)
            self.parseToken(tok,self.remap)
        self.hasGenerated = True

    def parseToken(self,token,remap={}) -> Wire:
        if(token.typ == "word" and token.data == "set"):
            return parseAssignSet(token,remap)
        if(token.typ == "word" and token.data == "repeat"):
            return self.parseRepeat(token,remap)
        if(token.typ == "word" and token.data == "="):
            return self.parseWireSet(token,remap)
        if(token.typ == "word"):
            print("(2026-09-02T14:34:30)",token)
            return self.maybeAddWire(remap.get(token.data,token.data))
        if(token.typ == ":"):
            print("(2026-09-02T14:34:37)",token)
            wName = ":".join([remap.get(x.data,x.data) for x in token.lst])
            return self.maybeAddWire(wName)
        if(token.typ == "&" or token.typ == "|"):
            return self.parseOperationLane(token,remap)
        if(token.typ == "@"):
            return self.parseSubModule(token,remap)

    def parseOperationLane(self,token,remap:dict) -> Wire:
        lan = Lane()
        inverting = token.typ == "&"
        self.lanes.append(lan)
        outWire = self.maybeAddWire(getRandName())
        for subToken in token.lst:
            fetchWire = self.parseToken(subToken,remap)
            subInvert = inverting != subToken.invert
            let = Connection(subToken,fetchWire,lan,True,subInvert)
            fetchWire.addOutOf(let)
            lan.addInto(let)
            self.cross.append(let)
        #
        subInvert = inverting != token.invert
        let = Connection(token,outWire,lan,False,subInvert)
        fetchWire.addInto(let)
        lan.addOutOf(let)
        self.cross.append(let)
        return outWire

    def parseWireSet(self,token,remap:dict) -> Wire:
        baseWir = self.maybeAddWire(token.lst[0])
        gotWire = self.parseToken(token.lst[1],remap)
        for oLed in gotWire.outLets:
            baseWir.addOutOf(oLed)
            oLed.wire = baseWir
        baseWir.addInto(gotWire.inLet)
        gotWire.inLet = gotWire
        self.wires.remove(gotWire)
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
            print(remap)
            print(e)
            raise Exception(f"Error with {token.showWhere()}")
        for count in range(varStart,varStop):
            remap[varName] = count
            for subToken in token.lst:
                self.parseToken(subToken,remap)
        return None

    def parseSubModule(self,token,remap:dict) -> None:
        oMod = Module.lookup.get(token.args[0].data)
        if(oMod is None):
            print(self.token.showWhere())
            raise Exception(f"Not found module of name {token.args[0].data}")
        oMod.generate(self)
        mapping = oMod.createTranslation(token.lst[0],token.lst[1])
        #"""
        for oLan in oMod.lanes:
            mLan = Lane()
            self.lanes.append(mLan)
            for cx in oLan.inLets:
                cWire = self.maybeAddWire(mapping[cx.wire.name])
                let = Connection(cx.token,cWire,mLan,cx.dirLane,cx.invert)
                self.cross.append(let)
                #inLets.append(CrossLet(cWire,cx.dirUp,cx.inverting))
                mLan.addInto(let)
                cWire.addOutOf(let)
            cx = oLan.outLet
            cWire = self.maybeAddWire(mapping[cx.wire.name])
            let = Connection(cx.token,cWire,mLan,cx.dirLane,cx.invert)
            self.cross.append(let)
            mLan.addOutOf(let)
            cWire.addInto(let)
            #outLet.append(CrossLet(cWire,cx.dirUp,cx.inverting))
            self.connections.append(Connection(inLets,outLet))
        #"""
        return None

    def createTranslation(self,inWire,outWire):
        print(self)
        return {}

    def __str__(self):
        dat = f"<Module: {self.name}\n"
        dat += f"wires:{' | '.join([x.name for x in self.wires])}\n"
        dat += f"lanes:{'\n'.join([' - ' + str(x) for x in self.lanes])}\n"
        dat += ">"
        return dat


def executeTokenList(tokenList:list[Token]):
    remap = {}
    for token in tokenList:
        if(token.typ == "word" and token.data == "set"):
            parseAssignSet(token,remap)
        if(token.typ == "word" and token.data in ["module","component"]):
            mod = Module(token.args[0].data,token,remap.copy())



