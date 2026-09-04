#!/usr/bin/env python3

import sys
import parser
import module
from jsonc_parser.parser import JsoncParser
import importlib

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
    print(settings)
    p = parser.Parser(settings["input"])
    p.tokenize()
    p.parsing()
    topLevel = p.getActiveList()
    #p.debugPrint()
    module.executeTokenList(topLevel)
    mainMod = module.Module.lookup["main"]
    mainMod.generate()
    while(mainMod.reduceConnections()):pass
    print(mainMod)
    generator = importlib.import_module("gen." + settings["type"])
    #generator = #__import__("./gen/" + settings["type"])
    generator.main(settings,mainMod)

if __name__ == "__main__":main()
