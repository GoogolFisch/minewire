
import sys
import logic



def main():
    fName = "./example/D-latch.mwire"
    with open(fName,"r")as fptr:
        fData = fptr.read()
    #fn = sys.argv[1]
    tokens = logic.Logic.parseLogic(fData)
    #tokens = component.Logic.parseLogic("nto = ~(sto|set)\n")



if __name__ == "__main__":main()
