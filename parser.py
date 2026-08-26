
class Token:
    __slots__ = ("typ","data","lst","invert","used",
                 "tStart","tEnd","tLine","tColumn","context"
                 )
    def __init__(self,data,typ,context):
        self.typ     = typ
        self.data    = data
        self.tStart  = context.lastIndex
        self.context = context
        self.tEnd    = context.index
        self.tLine   = context.lastLine
        self.tColumn = context.lastColumn
        ##
        self.lst     = []
        self.used    = False
        self.invert  = False
    def __str__(self):
        dat = self.data
        if(self.invert):dat = "~" + dat
        if(len(self.lst) > 0):
            dat += f"({','.join([str(x) for x in self.lst])})"
        return dat
    def isWire(self):
        if(self.typ == "word"):return True
        if(self.typ == ":"):return True
        return False


class Parser:
    __slots__ = ("fileName","fileContent",
                 "index","line","column",
                 "lastIndex","lastLine","lastColumn",
                 "tokenList"
                 )
    def __init__(self,fileName):
        self.fileName = fileName
        with open(self.fileName,"r")as fptr:
            self.fileContent = fptr.read()
        self.tokenList = []
        self.index     = 0
        self.line      = 0
        self.column    = 0

    def tryLexComment(self) -> Token:
        if(self.fileContent[self.index] != ';'):
            return False
        while(self.index < len(self.fileContent)):
            if(self.fileContent[self.index] == '\n'):
                break
            self.index += 1
        return True

    def tryLexWhiteSpace(self) -> Token:
        if(ord(self.fileContent[self.index]) > 32):
            return False
        while(self.index < len(self.fileContent)):
            if(ord(self.fileContent[self.index]) > 32):
                break
            if(self.fileContent[self.index] == '\n'):
                self.line += 1
                self.column = 0
            self.index += 1
            self.column += 1
        return True

    def tryLexName(self) -> Token:
        wordChar = "@ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        wordChar += wordChar.lower()
        wordChar += "0123456789_-"
        if(self.fileContent[self.index] not in wordChar):
            return False
        while(self.index < len(self.fileContent)):
            if(self.fileContent[self.index] not in wordChar):
                break
            self.index += 1
            self.column += 1
        tok = Token(self.fileContent[self.lastIndex:self.index],"word",self)
        self.tokenList.append(tok)
        return True


    def tokenize(self):
        while self.index < len(self.fileContent):
            self.lastIndex  = self.index
            self.lastLine   = self.line
            self.lastColumn = self.column
            if(self.tryLexWhiteSpace()):continue
            if(self.tryLexComment   ()):continue



