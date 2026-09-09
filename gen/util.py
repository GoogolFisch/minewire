

LENGTH_MAX = 999_999
HEAT_SPREAD = 10

class Cost:
    __slots__ = ("length","errors")
    def __init__(self,leng=0,errs=0):
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
        if(type(other) == Cost):
            return Cost(self.length + other.length,self.errors + other.errors)
        if(type(other) == int):
            return Cost(self.length + other,self.errors)

    def __sub__(self,other):
        if(type(other) == Cost):
            return Cost(self.length - other.length,self.errors - other.errors)
        if(type(other) == int):
            return Cost(self.length - other,self.errors)

    def __mul__(self,other):
        if(type(other) == int):
            return Cost(self.length * other,self.errors * other)
