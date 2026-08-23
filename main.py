#!/usr/bin/env python3



import sys
import logic
import schematica


settings = {
        "in":"./example/D-latch.mwire"
        }
def parseSettings(args=sys.argv[1:]):
    for a in args:
        spl = a.split("=")
        settings[spl[0]] = "=".join(spl[1:])
    print(settings)


def main():
    parseSettings()
    fName = settings["in"]
    with open(fName,"r")as fptr:
        fData = fptr.read()
    #fn = sys.argv[1]
    tokens, modules = logic.Logic.parseLogic(fData)
    #for m in modules: print(m)
    mainModule = logic.component.Module.lookup["main"]
    mainModule.parseFunctionList()
    mainModule.optimisation()
    mainModule.layoutOptimisation()
    #for m in modules: print(m)
    print(mainModule)
    schematica.createSchematic(settings,mainModule)
    #tokens = component.Logic.parseLogic("nto = ~(sto|set)\n")



if __name__ == "__main__":main()
