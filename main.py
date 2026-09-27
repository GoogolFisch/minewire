#!/usr/bin/env python3

import sys
import parser
import module
from jsonc_parser.parser import JsoncParser
import importlib
import time

settings = {}
if __name__ == "__main__":
    settings = JsoncParser.parse_file("./settings.jsonc")
    idx = 1
    while idx < len(sys.argv):
        arg = sys.argv[idx]
        if(arg == '-o'):
            idx += 1
            settings["output"] = sys.argv[idx]
        elif(arg == "-t"):
            idx += 1
            settings["type"] = sys.argv[idx]
        else:
            settings["input"] = arg
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


if __name__ == "__main__":main()
