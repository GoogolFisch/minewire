
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
    __slots__ = ("name","wires","lanes","cross")
    def __init__(self,name,token):
        Module.lookup[name] = self
        self.name = name


