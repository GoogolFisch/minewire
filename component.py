import uuid
def getRandName():
    return f"-{uuid.uuid4()}"

class Point:
    # typ = False # False for x dir
    __slots__ = ("typ","x","y")
    def __init__(self,typ,x,y):
        self.typ = typ
        self.x   =   x
        self.y   =   y

    def onRow(self, p2:Point):
        if self.typ != p2.typ:
            return False
        if(self.typ):
            return self.y == p2.y
        return self.x == p2.x
    def __str__(self):
        return f"{self.typ}:{self.y}:{self.x}"

class Wire:
    __slots__ = ("name","start","end")
    def __init__(self,name):
        self.name  = name
        self.start = 0
        self.end = 999
    def __str__(self):
        return f"{self.name}-<{self.start},{self.end}>"

class CrossLet:
    __slots__ = ("wire","dirUp","inverting","name")
    def __init__(self,wire,dirUp=True,invert=False):
        self.wire      = wire
        self.dirUp     = dirUp
        self.inverting = invert
    def __str__(self):
        doNot = ["","Not"][self.inverting]
        textDir = ["Down","Up"][self.dirUp]
        return f"{doNot} {textDir} {self.wire.name}"
class Connection:
    __slots__ = ("inLet","outLet")
    def __init__(self,inLet:list(CrossLet),outLet:list(CrossLet)):
        self.inLet  = inLet
        self.outLet = outLet
    def __str__(self):
        return (f"({' | '.join([str(x) for x in self.inLet])})->" +
                f"({' | '.join([str(x) for x in self.outLet])})")
#class LogicConnection:
#    __slots__ = ("crosses")

class Module:
    lookup = {}
    __slots__ = ("lock","wires","name",
                 "connections",
                 "token","tIn","tOut","tExpr",
                 "interfaceWire","namedWires")
    def __init__(self,dat,tIn,tOut,tExpr):
        self.name  = dat.lst[0].data
        self.lock  = False
        self.token = dat
        self.tIn   = tIn
        self.tOut  = tOut
        self.tExpr = tExpr
        self.connections   = []
        self.wires         = []
        self.namedWires    = []
        self.interfaceWire = []
        Module.lookup[self.name] = self
        self._parseWireName()
    def __str__(self):
        return (f"{self.name}:" +
                f"({",".join([i.data for i in self.interfaceWire])})," +
                f"({self.wires})," +
                f"[{'.'.join([str(x) for x in self.connections])}]"
                )
    def _parseWireName(self):
        for wr in self.tIn.lst:
            parts = wr.data.split(":")
            if(len(parts) > 1):
                count = int(parts[-1])
                for c in range(count):
                    self.interfaceWire.append(f"{parts[0]}:{c}")
            else:
                self.interfaceWire.append(wr)
        for wr in self.tOut.lst:
            parts = wr.data.split(":")
            if(len(parts) > 1):
                count = int(parts[-1])
                for c in range(count):
                    self.interfaceWire.append(f"{parts[0]}:{c}")
            else:
                self.interfaceWire.append(wr)
        #
    def maybeAddWire(self,nam)->Wire:
        for w in self.wires:
            if(w.name == nam):
                return w
        wir = Wire(nam)
        self.namedWires.append(wir)
        return wir
    def parseExpr(self,e)->Wire:
        if(e.typ == "word"):
            return self.maybeAddWire(e)
        if(e.typ == "|" or e.typ == "&"):
            no = e.typ == "&"
            w = Wire(getRandName())
            c = Connection([],[CrossLet(w,False,invert=no)])
            for subE in e.lst:
                oExpr = self.parseExpr(subE)
                c.inLet.append(CrossLet(oExpr,invert=no))
            self.connections.append(c)
            return w
    def parseFunctionList(self):
        if(self.lock):
            print("There is a recursive dependency!")
        self.lock = True
        for e in self.tExpr:
            #if(e.typ != "=" and e.typ != "word"): continue
            if(e.typ == "="):
                #self.maybeAddWire(e.lst[0])
                w = self.parseExpr(e.lst[1])
                w.name = e.lst[0]
            if(e.typ == "word"):
                refName = e.data
                if(refName[0] == '@'):refName = refName[1:]
                m = Module.lookup[refName]
                m.parseFunctionList()
                # TODO
#class Module




