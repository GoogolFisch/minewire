import random

EMPTY = list()
class Layout:
    LocationMap = dict()

    @staticmethod
    def FindNearLocation(loc:tuple)->list:
        outp = list()
        for x in range(-1,2):
            for y in range(-1,2):
                for z in range(-1,2):
                    outp += Layout.LocationMap.get((x + loc[0],y + loc[1],z + loc[2]),EMPTY)
        return outp

    @staticmethod
    def FindIfExists(obj):
        count = 0
        for k,v in Layout.LocationMap.items():
            if(obj in v):
                print(k,v,obj)
                count += 1
        return count



    __slots__ = ("pos","vec","count")
    def __init__(self,scale = 100):
        self.pos = PosVector.FromUniform(0,scale)
        self.vec = PosVector()
        self.count = 1
        #
        loc = self.toLoc()
        ls = Layout.LocationMap.get(loc,None)
        if(ls is not None): ls.append(self)
        else: Layout.LocationMap[loc] = [self]

    def toLoc(self):
        FAC = 8
        return (int(self.pos.x) // FAC,
                int(self.pos.y) // FAC,
                int(self.pos.z) // FAC)

    def move(self,scale=0.1):
        ls = Layout.LocationMap.get(self.toLoc(),EMPTY)
        if(self not in ls):breakpoint()
        ls.remove(self)
        sc = scale / self.count
        self.pos += self.vec * sc
        if(self.pos.y > 200):
            print(self.pos.y,self.vec.y)
        self.vec.zero()
        self.count = 1
        self.pos.x = max(2,self.pos.x)
        self.pos.y = max(0,self.pos.y)
        self.pos.z = max(2,self.pos.z)
        #
        loc = self.toLoc()
        ls = Layout.LocationMap.get(loc,None)
        if(ls is not None): ls.append(self)
        else: Layout.LocationMap[loc] = [self]

    def avoide(self,other:Layout):
        if(other == self):return
        diff = self.pos - other.pos
        mag = diff.magSq() * 0.75
        if(mag > 0.01):
            self.vec += diff / mag
        else:
            self.vec += PosVector.FromUniform(-1,1)

    def spring(self,other:Layout,sx=1,sy=1,sz=1):
        diff = other.pos - self.pos
        diff.x *= sx
        diff.y *= sy
        diff.z *= sz
        self.vec += diff
        self.count += 1

    def rawSpring(self,rx,ry,rz,sx,sy,sz):
        diff = PosVector(rx,ry,rz) - self.pos
        self.count += 1
        diff.x *= sx
        diff.y *= sy
        diff.z *= sz
        self.vec += diff

    def getX(self):return self.pos.x
    def getY(self):return self.pos.y
    def getZ(self):return self.pos.z
    def __str__(self):
        return f"<{self.pos.x}-{self.pos.y}-{self.pos.z}>"



class PosVector:
    __slots__ = ("x","y","z")
    def __init__(self,x=0,y=0,z=0):
        self.x = x
        self.y = y
        self.z = z

    def FromUniform(s,e) -> PosVector:
        return PosVector(random.uniform(s,e),random.uniform(s,e),random.uniform(s,e))

    def __add__(self,pv):
        np = PosVector()
        np.x = self.x + pv.x
        np.y = self.y + pv.y
        np.z = self.z + pv.z
        return np 

    def __sub__(self,pv):
        np = PosVector()
        np.x = self.x - pv.x
        np.y = self.y - pv.y
        np.z = self.z - pv.z
        return np 

    def __mul__(self,scale = 1):
        np = PosVector()
        np.x = self.x * scale
        np.y = self.y * scale
        np.z = self.z * scale
        return np 

    def __truediv__(self,scale = 1):
        np = PosVector()
        np.x = self.x / scale
        np.y = self.y / scale
        np.z = self.z / scale
        return np 

    def zero(self):
        self.x = 0
        self.y = 0
        self.z = 0

    def magSq(self):
        return max(self.x ** 2,self.y ** 2,self.z ** 2)
