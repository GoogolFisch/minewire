import random

class Layout:
    __slots__ = ("pos","vec")
    def __init__(self,scale = 100):
        self.pos = PosVector.FromUniform(0,scale)
        self.vec = PosVector()

    def move(self,scale=0.1):
        self.pos += self.vec * scale
        self.vec.zero()
        self.pos.x = max(2,self.pos.x)
        self.pos.y = max(0,self.pos.y)
        self.pos.z = max(2,self.pos.z)

    def avoide(self,other:Layout):
        if(other == self):return
        diff = self.pos - other.pos
        mag = diff.magSq() * 0.75
        if(mag > 0.01):
            self.vec += diff / diff.magSq()
        else:
            self.vec += PosVector.FromUniform(-1,1)

    def spring(self,other:Layout,sx=1,sy=1,sz=1):
        diff = other.pos - self.pos
        diff.x *= sx
        diff.y *= sy
        diff.z *= sz
        self.vec += diff

    def rawSpring(self,rx,ry,rz,sx,sy,sz):
        diff = PosVector(rx,ry,rz) - self.pos
        diff.x *= sx
        diff.y *= sy
        diff.z *= sz
        self.vec += diff

    def getX(self):return pos.x
    def getY(self):return pos.y
    def getZ(self):return pos.z



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

    def __div__(self,scale = 1):
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
        return self.x ** 2 + self.y ** 2 + self.z ** 2
