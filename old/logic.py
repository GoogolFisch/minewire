
import component


class Token:
    __slots__ = ("typ","data","lst","invert","used")
    def __init__(self,data):
        self.used   = False
        self.typ    = "None"
        self.data   = data
        self.lst    = []
        self.invert = False
        if(len(self.data) == 1): self.typ = self.data
        if(self.data in "~&|()=,01"):
            self.typ = self.data
        else:
            #if(self.data.isalnum()):
            self.typ = "word"
    def __str__(self):
        dat = self.data
        if(self.invert):dat = "~" + dat
        if(len(self.lst) > 0):
            dat += f"({','.join([str(x) for x in self.lst])})"
        return dat
    @staticmethod
    def sameWord(base,test):
        if(base in "~&|()=,"):return False
        if(test in "~&|()=,"):return False
        t = ord(test)
        if(t <= 32):
            return False
        b = ord(base)
        return True
    @staticmethod
    def word(dat)->(Token,int):
        typ = dat[0]
        if(ord(typ) <= 32):
            return (None,1)
        i = 1
        #slice
        while i < len(dat):
            if(not Token.sameWord(typ,dat[i])):
                break
            i += 1
        return (Token(dat[:i]),i)
#

class Logic:
    __slots__ = ("oName","lName","lNot")
    def __init__(self,oName,nName,lName,lNot):
        self.oName = oName
        self.nName = nName
        self.lName = lName
        self.lNot  =  lNot

    @staticmethod
    def findNextToken(tokens,idx,end):
        i = idx
        while i < end:
            t = tokens[i]
            if(not t.used):
                break
            i += 1
        return i
    @staticmethod
    def parseBiToken(tokens,operand,start=0,end=-1):
        i = start
        lastToken = None
        while i < end:
            t = tokens[i]
            if(t.typ == operand and len(t.lst) == 0):
                if(lastToken.typ == operand):
                    t.used = True
                    t = lastToken
                else:
                    t.lst.append(lastToken)
                    lastToken.used = True
                i = Logic.findNextToken(tokens,i + 1,end)
                tNext = tokens[i]
                t.lst.append(tNext)
                tNext.used = True
            i = Logic.findNextToken(tokens,i + 1,end)
            lastToken = t
        #
    @staticmethod
    def ensureInList(t)->Token:
        if(t.typ == ','):return t
        l = Token(",")
        l.lst = [t]
        return l
    @staticmethod
    def parseTokenExpr(tokens,start=0,end=-1):
        if(end == -1):
            end = len(tokens)
        lastToken = None
        i = start
        while i < end:
            t = tokens[i]
            if(t.typ == "("):#)
               Logic.parseTokenExpr(tokens,i + 1)
               j = i
               t.used = True
               while True:
                   j = Logic.findNextToken(tokens,j + 1,end)
                   tEnd = tokens[j]
                   if(tEnd.typ == ")"):
                       tEnd.used = True
                       break
            if(t.typ == "(" and lastToken.typ == "word"): #)
               i = Logic.findNextToken(tokens,i + 1,end)
               tNext = tokens[i]
               lastToken.lst = Logic.ensureInList(tNext).lst
               tNext.used = True
               t = lastToken
            if("(" == "(" and t.typ == ")"):#)
                end = i
                break
            i = Logic.findNextToken(tokens,i + 1,end)
            lastToken = t
        i = start
        while i < end:
            t = tokens[i]
            if(t.used):
                i += 1
                continue
            if(t.typ == '~'):
                t.used = True
                i = Logic.findNextToken(tokens,i + 1,end)
                t = tokens[i]
                t.invert = not t.invert
            i = Logic.findNextToken(tokens,i + 1,end)
        Logic.parseBiToken(tokens,"&",start,end)
        Logic.parseBiToken(tokens,"|",start,end)
        Logic.parseBiToken(tokens,",",start,end)
        Logic.parseBiToken(tokens,"=",start,end)
    @staticmethod
    def parseModule(tModu,tName,tIn,tOut,tExpr)->component.Module:
        #tModu.used = True
        tName.used = True
        tIn  .used = True
        tOut .used = True
        for e in tExpr:
            e.used = True
        #tExpr.used = True
        tModu.lst = [tName,tIn,tOut,tExpr]
        mod = component.Module(tModu,tIn,tOut,tExpr)
        return mod
    @staticmethod
    def parseTokenTopLevel(tokens)->list(component.Module):
        i = 0
        modules = []
        end = len(tokens)
        while i < end:
            t = tokens[i]
            if(t.data in ['module','component']):
                tModu = t
                #
                i = Logic.findNextToken(tokens,i + 1,end)
                tName = tokens[i]
                # in wires
                i = Logic.findNextToken(tokens,i + 1,end)
                Logic.parseTokenExpr(tokens,i + 1,end)
                tokens[i].used = True
                i = Logic.findNextToken(tokens,i + 1,end)
                tIn = Logic.ensureInList(tokens[i])
                i = Logic.findNextToken(tokens,i + 1,end)
                tokens[i].used = True
                #
                i = Logic.findNextToken(tokens,i,end)
                Logic.parseTokenExpr(tokens,i + 1,end)
                tokens[i].used = True
                i = Logic.findNextToken(tokens,i + 1,end)
                tOut = Logic.ensureInList(tokens[i])
                i = Logic.findNextToken(tokens,i + 1,end)
                tokens[i].used = True
                #
                i = Logic.findNextToken(tokens,i + 1,end)
                tokens[i].used = True
                Logic.parseTokenExpr(tokens,i + 1,end)
                tExpr = []
                while i < end:
                    i = Logic.findNextToken(tokens,i + 1,end)
                    t = tokens[i]
                    if(t.typ == ")"):
                        t.used = True
                        break
                    tExpr.append(t)
                modules.append(Logic.parseModule(tModu,tName,tIn,tOut,tExpr))
            #
            i = Logic.findNextToken(tokens,i + 1,end)
        return modules
    @staticmethod
    def parseLogic(string):
        tokens = []
        tsString = string
        while len(tsString):
            t,o = Token.word(tsString)
            tsString = tsString[o:]
            if(t is not None):
                tokens.append(t)
        #Logic.parseTokenExpr(tokens)
        m = Logic.parseTokenTopLevel(tokens)
        i = 0
        while i < len(tokens):
            #print(tokens[i])
            i = Logic.findNextToken(tokens,i + 1,len(tokens))
        return (tokens,m)
    #
#class Logic

