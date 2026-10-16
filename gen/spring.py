
import random

class Vector:
    __slots__ = ("x","y","z")
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

    def _getBucket(self):
        V = 4
        return (int(self.x // V),int(self.y // V),int(self.z // V))
    def _getNeighbourBucket(self):
        l = list()
        D = [-1,0,1]
        b = self._getBucket()
        for dx in D:
            for dy in D:
                for dz in D:
                    l.append((b[0] + dx,b[1] + dy,b[2] + dz))
        return l

    def _addDiffL(self,base,other):
        self.x += (base.x - other.x) * 1
        self.y += (base.y - other.y) * 3
        self.z += (base.z - other.z) * 22

    def _addDiffW(self,base,other): 
        self.x += (base.x - other.x) * 22
        self.y += (base.y - other.y) * 3
        self.z += (base.z - other.z) * 1

    def _addAvoide(self,b,o):
        if(b == o):return
        diff = max((b.x - o.x) ** 2,(b.y - o.y) ** 2,(b.z - o.z) ** 2)
        diff *= 0.75
        if(diff < 0.01):
            V = 0.01
            self.x += random.uniform(-V,V)
            self.y += random.uniform(-V,V)
            self.z += random.uniform(-V,V)
        else:
            inv = 1 / diff
            self.x += inv * (o.x - b.x)
            self.y += inv * (o.y - b.y)
            self.z += inv * (o.z - b.z)


class SpringObj:
    __slots__ = ("pos","vel","count","parent")
    def __init__(self):
        self.parent = None
        self.vel = Vector()
        self.pos = Vector()
        self.pos.x = random.uniform(0,100)
        self.pos.y = random.uniform(0,100)
        self.pos.z = random.uniform(0,100)
    def getPosition(self):
        return (self.pos.x,self.pos.y,self.pos.z)
    def setPosition(self,x,y,z):
        self.pos.x = x
        self.pos.y = y
        self.pos.z = z
    def getX(self):return self.pos.x
    def getY(self):return self.pos.y
    def getZ(self):return self.pos.z

    def _update(self,step):
        self.pos.x += self.vel.x * step
        self.pos.y += self.vel.y * step
        self.pos.z += self.vel.z * step
        if(self.pos.x < 1):self.pos.x = 1
        if(self.pos.y < 0):self.pos.x = 0
        if(self.pos.z < 1):self.pos.x = 1
        self.vel.x = 0
        self.vel.y = 0
        self.vel.z = 0



class SpringNet:
    __slots__ = ("hmap","arr","staticArr","laneArrs","wireArrs")
    def __init__(self):
        self.hmap = dict()
        self.arr = list()
        self.staticArr = list()
        self.laneArrs = list()
        self.wireArrs = list()
    def update(self,step):
        for la in self.laneArrs:
            for cl in la:
                for c2 in la:
                    c2.vel._addDiffL(cl.pos,c2.pos)
        for wa in self.laneArrs:
            for cw in wa:
                for c2 in wa:
                    c2.vel._addDiffW(cw.pos,c2.pos)
        L = list()
        for c in self.arr:
            for b in c.pos._getNeighbourBucket():
                nei = self.hmap.get(b,L)
                for nx in nei:
                    c.vel._addAvoide(c.pos,nc.pos)
        for x in self.arr:
            x._update(step)
    def _makeSpring(self,arr,target,map):
        attr = list()
        arr.append(attr)
        if(target[0] != -1):
            so = SpringObj()
            so.pos = target
            self.staticArr.append(so)
            attr.append(so)
        for k in map:
            k.parent = self
            attr.append(k)
    def makeSpringWire(self,*map,target=(-1,-1,-1)):
        self._makeSpring(self.wireArrs,target,map)
    def makeSpringLane(self,*map,target=(-1,-1,-1)):
        self._makeSpring(self.laneArrs,target,map)

