import uuid
def getRandName():
    return f"-{uuid.uuid4()}"
def getRandNameSmall():
    return f"-{uuid.uuid4()}"[:9]

LENGTH_MAX = 9999

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
    __slots__ = ("name","lane","refs",
                 "start","end","fixedPoint",
                 )
    def __init__(self,name):
        self.name  = name
        self.lane  = 0
        self.start = 0
        self.end   = 0
        self.refs  = []
        # wireLane,connectionLane
        self.fixedPoint = None
    def reset(self):
        self.start = LENGTH_MAX
        self.end   = 0
        if(self.fixedPoint is not None):
            self.update(self.fixedPoint[1])
    def update(self,lane):
        self.start = min(lane,self.start)
        self.end   = max(lane,self.end  )
    def __str__(self):
        return f"{self.name}-<{self.start},{self.end}>"

class CrossLet:
    __slots__ = ("wire","conn","dirUp","inverting","name")
    def __init__(self,wire,dirUp=True,invert=False):
        self.wire      = wire
        self.dirUp     = dirUp
        self.inverting = invert
        self.conn      = None
        self.wire.refs.append(self)
    def __str__(self):
        doNot = ["","Not"][self.inverting]
        textDir = ["Down","Up"][self.dirUp]
        return f"{doNot} {textDir} {self.wire.name}"
class Connection:
    __slots__ = ("inLet","outLet","lane","start","end")
    def __init__(self,inLet:list(CrossLet),outLet:list(CrossLet)):
        self.lane   = 0
        self.inLet  = inLet
        self.outLet = outLet
        for cx in inLet :cx.conn = self
        for cx in outLet:cx.conn = self
    def reset(self):
        self.start = LENGTH_MAX
        self.end   = 0
    def update(self,lane):
        self.start = min(lane,self.start)
        self.end   = max(lane,self.end  )
    def __str__(self):
        return (f"({' | '.join([str(x) for x in self.inLet])})->" +
                f"({' | '.join([str(x) for x in self.outLet])})")
#class LogicConnection:
#    __slots__ = ("crosses")

class Module:
    lookup = {}
    __slots__ = ("lock","name",
                 "connections",
                 "token","tIn","tOut","tExpr",
                 "functionWires",
                 "interfaceWire","namedWires")
    def __init__(self,dat,tIn,tOut,tExpr):
        self.name  = dat.lst[0].data
        self.lock  = False
        self.token = dat
        self.tIn   = tIn
        self.tOut  = tOut
        self.tExpr = tExpr
        self.connections   = []
        self.namedWires    = []
        self.interfaceWire = []
        self.functionWires = []
        Module.lookup[self.name] = self
        self._parseWireName()
    def __str__(self):
        return (f"{self.name}:" +
                f"({",".join([i.data for i in self.interfaceWire])})," +
                f"[{'.'.join([str(x) for x in self.connections])}]"
                )
    def _parseWireName(self):
        for wr in self.tIn.lst:
            self.functionWires.append(wr.data)
            parts = wr.data.split(":")
            if(len(parts) > 1):
                count = int(parts[-1])
                for c in range(count):
                    self.interfaceWire.append(f"{parts[0]}:{c}")
            else:
                self.interfaceWire.append(wr)
        for wr in self.tOut.lst:
            self.functionWires.append(wr.data)
            parts = wr.data.split(":")
            if(len(parts) > 1):
                count = int(parts[-1])
                for c in range(count):
                    self.interfaceWire.append(f"{parts[0]}:{c}")
            else:
                self.interfaceWire.append(wr)
        #
    def maybeAddWire(self,nam)->Wire:
        for w in self.namedWires:
            if(w.name == nam):
                return w
        wir = Wire(nam)#,len(self.namedWires))
        for ifwToken in self.interfaceWire:
            if(ifwToken.data == nam):
                wir.fixedPoint = (-1,0)
        self.namedWires.append(wir)
        return wir
    def parseExpr(self,e)->Wire:
        if(e.typ == "word"): return self.maybeAddWire(e.data)
        if(e.typ == "0"): return self.maybeAddWire(e.data)
        if(e.typ == "1"): return self.maybeAddWire(e.data)
        if(e.typ == "|" or e.typ == "&"):
            no = e.typ == "&"
            no2 = no != e.invert
            #print(e,no)
            w = Wire(getRandName())
            c = Connection([],[CrossLet(w,False,invert=no2)])
            for subE in e.lst:
                no2 = no
                no2 = no != subE.invert
                oExpr = self.parseExpr(subE)
                c.inLet.append(CrossLet(oExpr,invert=no2))
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
                w.name = e.lst[0].data
            if(e.typ == "word"):
                refName = e.data
                if(refName[0] == '@'):refName = refName[1:]
                m = Module.lookup[refName]
                m.parseFunctionList()
                translation = m.namespaceTranslation(e.lst)
                for conn in m.connections:
                    inLets = []
                    for cx in conn.inLet:
                        cWire = self.maybeAddWire(translation[cx.wire.name])
                        inLets.append(CrossLet(cWire,cx.dirUp,cx.inverting))
                    outLets = []
                    for cx in conn.outLet:
                        cWire = self.maybeAddWire(translation[cx.wire.name])
                        outLets.append(CrossLet(cWire,cx.dirUp,cx.inverting))
                    self.connections.append(Connection(inLets,outLets))
                # TODO
        self.optimisation()
    def namespaceTranslation(self,nameWire:list(str))->dict:
        if(len(nameWire) != len(self.functionWires)):
            print(f"(2026-08-21T13:00:23) {nameWire} -> "+ 
                  f"{self.functionWires} in {self.name}")
            return
        translation = {}
        for nw,f in zip(nameWire,self.functionWires):
            #print(nw.data,f)
            if(":" in f):
                splt = f.split(":")
                cnt = int(splt[1])
                nam = splt[0]
                for i in range(cnt):
                    translation[f"{nam}:{i}"] = f"{nw.data}:{i}"
            else:
                translation[f] = str(nw.data)
        # hidden wires
        for wir in self.namedWires:
            if(wir.name not in translation):
                if(len(wir.name) > 30):
                    translation[wir.name] = getRandName()
                    #translation[wir.name] = wir.name
                else:
                    #translation[wir.name] = f"{self.name}@{wir.name}{getRandNameSmall()}"
                    translation[wir.name] = f"{wir.name}@{self.name}{getRandNameSmall()}"
        #print(translation)
        return translation
    def length(self):
        akku = 0
        for w in self.namedWires: w.reset()
        #for w in self.interfaceWire:
        #    w.update(0)
        for conn in self.connections:
            conn.reset()
            for cx in conn.inLet:
                cx.wire.update(conn.lane)
                conn.update(cx.wire.lane)
            for cx in conn.outLet:
                cx.wire.update(conn.lane)
                conn.update(cx.wire.lane)
            if(conn.start > conn.end):
                print("(2026-08-20T19:46:08) low high error")
                continue
            akku += conn.end - conn.start
        for conn in self.connections:
            for c2 in self.connections:
                if(conn is c2):continue
                if(conn.end > c2.start and conn.start < c2.end):
                    akku += LENGTH_MAX
        for w in self.namedWires:
            for w2 in self.namedWires:
                if(w is w2):continue
                if(w2.end > w.start and w2.start < w.end):
                    akku += LENGTH_MAX
            if(w.start > w.end):
                print("(2026-08-20T19:47:23) low high error")
                continue
            akku += w.end - w.start
        return akku
    def layoutOptimisation(self):
        for i,w in enumerate(self.namedWires): w.lane = i + 1
        for i,c in enumerate(self.connections): c.lane = i + 1
        self.length()
    def optimisation(self):
        didChange = True
        while didChange:
            neededWires = self.interfaceWire.copy()
            #neededWires.append(self.)
            didChange = False
            #print(self.connections,flush=True)
            for conn in reversed(self.connections):
                for cx in reversed(conn.inLet):
                    if(cx.wire not in neededWires):
                        neededWires.append(cx.wire)
                    if(cx.wire.name == "0"):
                        conn.inLet.remove(cx)
                        didChange = True
                        if(cx.inverting):
                            self.connections.remove(conn)
                            break
                    if(cx.wire.name == "1"):
                        conn.inLet.remove(cx)
                        didChange = True
                        if(not cx.inverting):
                            self.connections.remove(conn)
                            break
                #for cx in conn.inLet
            #for conn in self.connections
            for wir in reversed(self.namedWires):
                if(wir not in neededWires and wir not in self.interfaceWire):
                    self.namedWires.remove(wir)
    #def optimisation()

#class Module




