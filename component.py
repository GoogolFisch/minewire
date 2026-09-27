
import random
import uuid

LENGTH_MAX = 999_999
HEAT_SPREAD = 10

def getRandName():
    return f"-{uuid.uuid4()}"
def getRandNameSmall():
    return f"-{uuid.uuid4()}"[:9]

class Cost:
    __slots__ = ("length","errors")
    def __init__(self,leng,errs):
        self.length = leng
        self.errors = errs

    def __str__(self):
        return f"<{self.length}-{self.errors}>"

    def __eq__(self,other):
        return self.length == other.length and self.errors == other.errors

    def __lt__(self,other):
        if(self.errors < other.errors):return True
        if(self.errors > other.errors):return False
        if(self.length < other.length):return True
        return False

    def __gt__(self,other):
        if(self.errors > other.errors):return True
        if(self.errors < other.errors):return False
        if(self.length > other.length):return True
        return False

    def __add__(self,other):
        return Cost(self.length + other.length,self.errors + other.errors)


class Via :
    __slots__ = ("wire","lane","start","end",
                 "token",
                 "wireIn","wiresOut","name")
    def __init__(self,token,name):
        self.token = token
        self.name  = name
        self.wire  = 0
        self.lane  = 0
        self.start = 0
        self.end   = 0
        self.wireIn   = None
        self.wiresOut = []

    def reset(self):
        self.start = LENGTH_MAX
        self.end   = 0

    def update(self,connection):
        pass

    def __str__(self):
        return f"<Via:{self.name}>"


class Connection:
    __slots__ = ("token","viaO","laneO","dirUp","invert")
    def __init__(self,token,via,lane,dirUp=True,invert=False):
        self.token  = token
        self.viaO   = via
        self.laneO  = lane
        self.dirUp  = dirUp
        self.invert = invert

    def __str__(self):
        return f"<Connection:{self.viaO.name}-{self.laneO}>"

class Wire:
    __slots__ = ("layer","viaO","start","end",
                 "inLet","outLets")
    def __init__(self,via):
        self.viaO    = via
        self.layer   = 0
        self.inLet   = None
        self.outLets = []

    def reset(self):
        self.start = LENGTH_MAX
        self.end   = 0

    def update(self,connection):
        pass

    def __str__(self):
        return f"<Wire:{self.viaO.name}-{self.layer}>"

class Lane:
    __slots__ = ("layer","lane","start","end",
                 "inLets","outLet")
    def __init__(self):
        self.layer  = 0
        self.lane   = 0
        self.inLets = []
        self.outLet = None

    def reset(self):
        self.start = LENGTH_MAX
        self.end   = 0

    def update(self,connection):
        pass

    def __str__(self):
        return f"<Lane:{self.lane}-{self.layer}"

class Module:
    lookup = dict()
    __slots__ = ("name")
    def __init__(self,name,token):
        Module.lookup[name] = self
        self.name = name


