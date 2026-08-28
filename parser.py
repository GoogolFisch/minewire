
class Token:
    __slots__ = ("typ","data","invert","used",
                 "args","lst",
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
        self.args    = []
        self.lst     = []
        self.used    = False
        self.invert  = False

    def update(self,token):
        if(token.tStart < self.tStart):
            self.tStart = token.tStart
        if(token.tEnd > self.tEnd):
            self.tEnd = token.tEnd

    def __str__(self):
        dat = self.data
        if(self.invert):dat = "~" + dat
        if(len(self.args) > 0):
            dat += f"[{','.join([str(x) for x in self.args])}]"
        if(len(self.lst) > 0):
            dat += f"({','.join([str(x) for x in self.lst])})"
        return dat

    def isWire(self) -> bool:
        if(self.typ == "word"):return True
        if(self.typ == ":"):return True
        return False

    def getWireName(self) -> str:
        if(self.typ == ':'):
            return ':'.join([x.getWireName() for x in self.lst])
        return self.data

    def getCount(self) -> int:
        if(self.typ != ':'):return 1
        number = self.lst[-1].data
        if(not number.isnum()):return 1
        return int(number)

    def showWhere(self) -> str:
        return (
            f"{self.context.fileName}:" +
            f"{self.tLine}:{self.tColumn}\n" +
            f"{self.context.fileContent[self.tStart:self.tEnd]}\n" +
            f"{self.__str__()}"
        )

    def copyContext(self,t:Token):
        self.tLine   = t.tLine
        self.tColumn = t.tColumn
        self.tStart  = t.tStart
        self.tEnd    = t.tEnd

    @staticmethod
    def ensureInLst(token:Token)->Token:
        if(token.typ == ","):return token
        t = Token(",",",",token.context)
        t.copyContext(token)
        t.lst.append(token)
        return t



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

    def tryLexTillEOL(self) -> Token:
        while(self.index < len(self.fileContent)):
            if(self.fileContent[self.index] == '\n'):
                break
            self.index += 1
        tok = Token(self.fileContent[self.lastIndex:self.index],"raw",self)
        self.tokenList.append(tok)
        return True

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

    @staticmethod
    def _isCharOfWord(char) -> bool:
        return char.isalnum() or char in '-_'

    def tryLexName(self) -> Token:
        if(not Parser._isCharOfWord(self.fileContent[self.index])):
            return False
        while(self.index < len(self.fileContent)):
            if(not Parser._isCharOfWord(self.fileContent[self.index])):
                break
            self.index += 1
            self.column += 1
        tok = Token(self.fileContent[self.lastIndex:self.index],"word",self)
        self.tokenList.append(tok)
        return True

    def tryLexNumSeperator(self) -> Token:
        if(self.fileContent[self.index] != ":"):return False
        self.index += 1
        tok = Token(":",":",self)
        self.tokenList.append(tok)
        return True

    def tryLexSymbol(self) -> Token:
        symbolChar = ",|&()~=@"
        char = self.fileContent[self.index]
        if(char not in symbolChar):
            return False
        self.index += 1
        tok = Token(char,char,self)
        self.tokenList.append(tok)
        return True

    def tokenize(self):
        self.index  = 0
        self.line   = 1
        self.column = 1
        while self.index < len(self.fileContent):
            self.lastIndex  = self.index
            self.lastLine   = self.line
            self.lastColumn = self.column
            if(self.tryLexWhiteSpace()):continue
            if(self.tryLexComment   ()):continue
            if(self.tryLexNumSeperator()):
                if(not self.tryLexName()):
                    print("(2026-08-27T10:28:44) Error! " +
                          "after numSeperator was a wrong thing")
                continue
            if(self.tryLexSymbol()):continue
            #
            t = self.tryLexName()
            if(t):
                lastToken = self.tokenList[-1]
                if(lastToken.data == "import"):
                    self.tryLexWhiteSpace()
                    self.tryLexTillEOL()
                    continue
                continue
            print("(2026-08-26T20:46:22) Char not matching any Symbol! ",
                  self.fileContent[self.index])
        #print("\n".join([str(x) for x in self.tokenList]))

    def findNextToken(self,offset = 0,limit=-1) -> Token:
        if(limit == -1):limit = len(self.tokenList)
        self.index += offset
        while self.index < limit:
            if(not self.tokenList[self.index].used):
                return self.tokenList[self.index]
            self.index += 1
        return None


    def tryParseSubExpr(self,token,limit=-1):
        if(token.typ != "("):return False # )
        token.used = True
        self.index += 1
        self.parseInner()
        tEnding = self.findNextToken(limit=limit)
        if(tEnding is None):
            print(f"(2026-08-27T14:35:04) EOF, couldn't finish\n{token.showWhere()}\nreached...")
            return
        if(tEnding.typ != ')'):
            print(
                    "(2026-08-27T13:05:08) Expected \")\", but found\n",
                    tEnding.showWhere()
            )
        tEnding.used = True
        return True

    def parseBiMergeOperand(self,operand,begin=0,upper=-1):
        self.index = begin
        lastToken = None
        while self.index < upper:
            t = self.findNextToken(limit=upper)
            if(t is None):break
            if(t.typ == operand and len(t.lst) == 0):
                if(lastToken.typ == operand):
                    lastToken.update(t)
                    t.used = True
                    t = lastToken
                else:
                    t.lst.append(lastToken)
                    t.update(lastToken)
                    lastToken.used = True
                tNext = self.findNextToken(offset=1,limit=upper)
                if(tNext is None):
                    print("(2026-08-27T15:22:47) Error, expected next token!\n",
                          t.showWhere())
                t.lst.append(tNext)
                t.update(tNext)
                tNext.used = True
            self.index += 1
            lastToken = t
        #end

    def parseRepeat(self,token,limit=-1):
        if(len(token.lst) != 0):return
        stepBack = self.index
        tBRange = self.findNextToken(offset=1,limit=limit)
        self.tryParseSubExpr(tBRange)
        self.index = stepBack
        tRange = self.findNextToken(offset=1,limit=limit)
        token.update(tRange)
        tRange.used = True
        token.args.append(tRange)
        #
        tBLst = self.findNextToken(offset=1,limit=limit)
        self.tryParseSubExpr(tBLst)
        stepLimit = self.index
        self.index = stepBack + 1
        while self.index < stepLimit:
            tRep = self.findNextToken(offset=0,limit=stepLimit)
            if(tRep is None):break
            token.update(tRep)
            tRep.used = True
            token.lst.append(tRep)

    def parseSet(self,token,limit=-1):
        if(len(token.lst) != 0):return
        stepBack = self.index
        tBegin = self.findNextToken(offset=1,limit=limit)
        self.tryParseSubExpr(tBegin)
        self.index = stepBack
        tAssign = self.findNextToken(offset=1,limit=limit)
        token.update(tAssign)
        tAssign.used = True
        token.lst.append(Token.ensureInLst(tAssign))

    def parseInner(self):
        storeIdx = self.index
        upper = len(self.tokenList)
        while self.index < upper:
            t = self.findNextToken(limit=upper)
            if(t is None):break
            elif(t.typ == "word" and t.data == "repeat"):
                self.parseRepeat(t,limit=upper)
            elif(t.typ == "word" and t.data == "set"):
                self.parseSet(t,limit=upper)
            elif(t.typ == '('):
                 self.tryParseSubExpr(t,limit=upper)
            if(t.typ == ')'):
                upper = self.index
                break
            self.index += 1
        #
        self.parseBiMergeOperand(":",storeIdx,upper)
        self.index = storeIdx
        while self.index < upper:
            t = self.findNextToken(limit=upper)
            if(t is None):break
            if(t.typ == '~'):
                t.used = True
                tInvert = self.findNextToken(offset=1,limit=upper)
                tInvert.update(t)
                tInvert.invert = not tInvert.invert
            self.index += 1
        self.parseBiMergeOperand("&",storeIdx,upper)
        self.parseBiMergeOperand("|",storeIdx,upper)
        self.parseBiMergeOperand("=",storeIdx,upper)
        self.parseBiMergeOperand(",",storeIdx,upper)
        self.index = storeIdx
        while self.index < upper:
            t = self.findNextToken(limit=upper)
            if(t is None):break
            if(t.typ == '@' and len(t.args) == 0):
                tName = self.findNextToken(offset=1,limit=upper)
                t.update(tName)
                tName.used = True
                t.args.append(tName)
                #
                tIntoWire = self.findNextToken(offset=1,limit=upper)
                t.update(tIntoWire)
                tIntoWire.used = True
                t.args.append(Token.ensureInLst(tIntoWire))
                #
                tOutOfWire = self.findNextToken(offset=1,limit=upper)
                t.update(tOutOfWire)
                tOutOfWire.used = True
                t.args.append(Token.ensureInLst(tOutOfWire))
            self.index += 1
        #self.index = upper

    def parseModule(self,t:Token) -> bool:
        tName = self.findNextToken(offset=1)
        tName.used = True
        t.args.append(tName)
        #
        tBArgs = self.index
        self.tryParseSubExpr(self.findNextToken(offset=1))
        self.index = tBArgs
        tArgsIn = Token.ensureInLst(self.findNextToken())
        tArgsIn.used = True
        t.args.append(tArgsIn)
        #
        tBArgs = self.index
        self.tryParseSubExpr(self.findNextToken(offset=1))
        self.index = tBArgs
        tArgsOut = Token.ensureInLst(self.findNextToken())
        tArgsOut.used = True
        t.args.append(tArgsOut)
        #
        tBProg = self.index
        self.tryParseSubExpr(self.findNextToken(offset=1))
        upper = self.index
        self.index = tBArgs
        while self.index < upper:
            tok = self.findNextToken(limit=upper)
            if(tok is None):break
            t.lst.append(tok)
            tok.used = True

    def parsing(self):
        self.index = 0
        while self.index < len(self.tokenList):
            t = self.findNextToken()
            if(t is None):break
            elif(t.data == "import"):
                tName = self.findNextToken(offset=1)
                child = Parser(tName.data)
            elif(t.data == "component" or t.data == "module"):
                self.parseModule(t)
            elif(t.typ == "word" and t.data == "set"):
                self.parseSet(t)
            self.index += 1
        return
        for x in self.tokenList:
            if(x.used):continue
            print(x.showWhere())
