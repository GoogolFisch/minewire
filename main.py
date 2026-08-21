#!/usr/bin/env python3



import sys
import logic



def main():
    fName = "./example/D-latch.mwire"
    with open(fName,"r")as fptr:
        fData = fptr.read()
    #fn = sys.argv[1]
    tokens, modules = logic.Logic.parseLogic(fData)
    #for m in modules: print(m)
    mainModule = logic.component.Module.lookup["main"]
    mainModule.parseFunctionList()
    #for m in modules: print(m)
    print(mainModule)
    #tokens = component.Logic.parseLogic("nto = ~(sto|set)\n")



if __name__ == "__main__":main()
