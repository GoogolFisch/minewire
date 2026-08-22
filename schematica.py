
from litemapy import Region, BlockState, Schematic

class Blocks:
    baseBlock = BlockState("minecraft:green_terracotta")
    upBlock = BlockState("minecraft:oak_slab",type="top")
    wireBlock = BlockState("minecraft:redstone_wire")
    redirBlock = BlockState("minecraft:target")

    torchUp = BlockState("minecraft:redstone_torch",lit="true")

    torchMinuxX = BlockState("minecraft:redstone_wall_torch",
                            facing="west",lit="true")
    torchPlusX = BlockState("minecraft:redstone_wall_torch",
                            facing="east",lit="true")

    repeatMinuxX = BlockState("minecraft:repeater",
                            delay="1",facing="east",locked="false",powered="false")
    repeatPlusX = BlockState("minecraft:repeater",
                            delay="1",facing="west",locked="false",powered="false")
    repeatMinuxZ = BlockState("minecraft:repeater",
                            delay="1",facing="south",locked="false",powered="false")
    repeatPlusZ = BlockState("minecraft:repeater",
                            delay="1",facing="north",locked="false",powered="false")

#direction & 1 = 0 => in +X direction
#direction & 2 = 0 => in +Z direction
def buildNotTower(region,x,z,direction=0):
    if(direction & 1):dx = x * 3 + 1
    else             :dx = x * 3 - 1
    if(direction & 2):dz = z * 3 + 1
    else             :dz = z * 3 - 1
    region[dx,1,dz] = Blocks.redirBlock
    region[dx,2,dz] = Blocks.torchUp
    region[dx,3,dz] = Blocks.baseBlock
def buildIndTower(region,x,z,direction=0):
    if(direction & 1):dx = x * 3 + 1
    else             :dx = x * 3 - 1
    dz = z * 3
    region[dx,1,dz] = Blocks.baseBlock
    region[dx,2,dz] = Blocks.baseBlock
    region[ x,2,dz] = Blocks.upBlock
def buildNotDown(region,x,z,direction=0):
    if(direction & 1):dx = x * 3 + 1
    else             :dx = x * 3 - 1
    if(direction & 2):dz = z * 3 + 1
    else             :dz = z * 3 - 1
    region[dx,1,dz] = Blocks.redirBlock
    region[dx,2,dz] = Blocks.torchUp
    region[dx,3,dz] = Blocks.baseBlock
def buildIndDown(region,x,z,direction=0):
    if(direction & 1):dx = x * 3 + 1
    else             :dx = x * 3 - 1
    dz = z * 3
    region[dx,1,dz] = Blocks.baseBlock
    region[dx,2,dz] = Blocks.baseBlock
    region[ x,2,dz] = Blocks.upBlock


def setupSettings(settings):
    joining = {
            "Save"       :"./output.litematic",
            "Name"       :"Computational Stuff",
            "Author"     :"MineWire",
            "Description":"MineWire",
    }
    for k,v in joining.items():
        if(k not in settings):settings[k] = v

def placeGridWires(region,size):
    for x in range(-1,size):
        for z in range((size + 2) // 3):
            region[x    ,0,z * 3] = Blocks.baseBlock
            region[x    ,1,z * 3] = Blocks.wireBlock
            region[z * 3,2,x    ] = Blocks.baseBlock
            region[z * 3,3,x    ] = Blocks.wireBlock

def createSchematic(settings,module):
    setupSettings(settings)
    region = Region(-2,0,-2,100,6,100)
    schematic = reg.as_schematic(name=settings["Name"],
                                 author=settings["Author"],
                                 description=settings["Description"])

    schematic.save(settings["Save"])




def main():
    settings = {}
    setupSettings(settings)
    size = 100
    region = Region(0,0,0,size,6,size)
    schematic = region.as_schematic(name=settings["Name"],
                                 author=settings["Author"],
                                 description=settings["Description"])
    placeGridWires(region,size)
    #
    schematic.save(settings["Save"])

if __name__ == "__main__":main()
