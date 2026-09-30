#!/usr/bin/env python3

import sys
import parser
import module
from jsonc_parser.parser import JsoncParser
import importlib
import time
from helper import helper

settings = {}
def putSetting(setting,key,argv,idx):
    setting[key] = argv[idx + 1]
    return idx + 1

if __name__ == "__main__":
    settings = JsoncParser.parse_file("./settings.jsonc")
    idx = 1
    while idx < len(sys.argv):
        arg = sys.argv[idx]
        if  (arg == '-o'   ):idx = putSetting(settings,"output",sys.argv,idx)
        elif(arg == "-name"):idx = putSetting(settings,"name"  ,sys.argv,idx)
        elif(arg == "-t"   ):idx = putSetting(settings,"type"  ,sys.argv,idx)
        elif(arg[0] == "-"):pass
        else:settings["input"] = arg
        idx += 1



def main():
    timeTable = []
    timeTable.append(time.time())
    print(settings)
    p = parser.Parser(settings["input"])
    p.tokenize()
    p.parsing()
    topLevel = p.getActiveList()
    #p.debugPrint()
    module.executeTokenList(topLevel)
    mainMod = module.Module.lookup["main"]
    mainMod.generate()
    timeTable.append(time.time())
    while(mainMod.reduceConnections()):pass
    timeTable.append(time.time())
    print(mainMod)
    generator = importlib.import_module("gen." + settings["type"])
    #generator = #__import__("./gen/" + settings["type"])
    generator.main(settings,mainMod,timeTable)
    timeTable.append(time.time())
    print(" - ".join([str(timeTable[x + 1] - timeTable[x]) for x in range(len(timeTable) - 1)]))

def testRemove(lst,*args) -> None | str:
    for i in args:
        if i in lst:
            lst.remove(i)
            return i
    return None

if __name__ == "__main__":
    cpArgs = sys.argv.copy()
    found = testRemove(cpArgs,"-h","-help","--help")
    if(found):
        exit(helper(settings,cpArgs,found))
    exit(main())
