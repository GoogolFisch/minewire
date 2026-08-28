
import random
import uuid

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
                 "wireIn","wiresOut","name")
    def __init__(self,name):
        self.name  = name
        self.wire  = 0
        self.lane  = 0
        self.start = 0
        self.end   = 0
        self.wireIn   = None
        self.wiresOut = []

class Connection:
    __slots__ = ("viaO","laneO","dirUp","invert")
    def __init__(self,via,lane,dirUp=True,invert=False):
        self.viaO   = via
        self.laneO  = lane
        self.dirUp  = dirUp
        self.invert = invert

class Wire:
    __slots__ = ("layer","viaO","start","end",
                 "inLet","outLets")
    def __init__(self,via):
        self.viaO    = via
        self.layer   = 0
        self.inLet   = None
        self.outLets = []

class Lane:
    __slots__ = ("layer","lane","start","end",
                 "inLets","outLet")
    def __init__(self):
        self.layer  = 0
        self.lane   = 0
        self.inLets = []
        self.outLet = None

class Module
