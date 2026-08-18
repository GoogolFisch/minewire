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

class CrossLet:
    __slots__ = ("point","dirUp","inverting","name")
    def __init__(self,pt=Point(False,0,0),dir=False,invert=False,name=None):
        self.point     = pt
        self.dirUp     = dir
        self.inverting = invert
        self.name      = name
    def __str__(self):
        doNot = ["---","Not"][self.inverting]
        textDir = ["Down","Up"][self.dirUp]
        return f"{self.point.y}:{self.point.x} {doNot} {textDir} {self.name}"

class Module:
    lookup = {}
    __slots__ = ("token","namedWires")
    def __init__(self,dat):
        self.token = dat
        Module.lookup[dat.lst[0]] = self
        self._parseWireName()
    def _parseWireName(self):
        pass




