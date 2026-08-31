
import random
import uuid

LENGTH_MAX = 999_999
HEAT_SPREAD = 10

def getRandName():
    return f"-{uuid.uuid4()}"
def getRandNameSmall():
    return f"-{uuid.uuid4()}"[:9]

class Connection:
    __slots__ = ("token","wire","lane","dirUp","invert")
    def __init__(self,token,wire,lane,dirUp=True,invert=False):
        self.token  = token
        self.wire   = wire
        self.lane   = lane
        self.dirUp  = dirUp
        self.invert = invert

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

    def __str__(self):
        return f"<Lane:{self.lane}-{self.layer}"

class Module:
    lookup = dict()
    __slots__ = ("name","tokens","wires","lanes","cross")
    def __init__(self,name,token):
        Module.lookup[name] = self
        self.name   = name
        self.tokens = token

    def findWireByName(self,nam) -> Wire:
        for w in self.wires:
            if(w.name == nam):
                return w
        return None

    def maybeAddWire(self,nam) -> Wire:
        wir = self.findWireByName(nam)
        if(wir is None):
            return wir
        wir = Wire(nam)
        return wir

    def parseToken(self,token,remap) -> Wire:
        if(token.typ == "word" and token.data == "set"):
            for assignToken in token.lst:
                remap[assignToken.lst[0].data] = assignToken.lst[1].data
            return None
        if(token.typ == "word" and token.data == "repeat"):
            remap = remap.copy()
            try:
                varName = token.args[0]
                varStart = int(token.args[1])
                varStop = int(token.args[2])
            except Exception as e:
                print(e)
                print(f"Error with {token.showWhere()}")
            for count in range(varStart,varStop):
                remap[varName] = count
                for subToken in token.lst:
                    self.parseToken(subToken,remap)
            return None
        if(token.typ == "word" and token.data == "="):
            baseWir = self.maybeAddWire(token.lst[0])
            gotWire = self.parseToken(token.lst[1],remap)
            for oLed in gotWire.outLets:
                baseWir.addOutOf(oLed)
                oLed.wire = baseWir
            baseWir.addInto(gotWire.inLet)
            gotWire.inLet = gotWire
            self.wires.remove(gotWire)
            return baseWir
        if(token.typ == "word"):
            return self.maybeAddWire(token.data)
        if(token.typ == "&"):
            lan = Lane()
            self.lanes.append(lan)
            outWire = self.maybeAddWire(getRandName())
            return outWire
        if(token.typ == "&"):
            lan = Lane()
            self.lanes.append(lan)
            outWire = self.maybeAddWire(getRandName())
            return outWire


