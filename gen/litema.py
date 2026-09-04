
#import litemapy
from litemapy import Region, BlockState, Schematic

class Blocks:
    baseBlock = BlockState("minecraft:green_terracotta")
    upBlock = BlockState("minecraft:oak_slab",type="top")
    wireBlock = BlockState("minecraft:redstone_wire")
    redirBlock = BlockState("minecraft:target")

    torchUp = BlockState("minecraft:redstone_torch",lit="true")

    torchMinusX = BlockState("minecraft:redstone_wall_torch",
                            facing="west",lit="true")
    torchPlusX = BlockState("minecraft:redstone_wall_torch",
                            facing="east",lit="true")

    repeatMinusX = BlockState("minecraft:repeater",
                            delay="1",facing="east",locked="false",powered="false")
    repeatPlusX = BlockState("minecraft:repeater",
                            delay="1",facing="west",locked="false",powered="false")
    repeatMinusZ = BlockState("minecraft:repeater",
                            delay="1",facing="south",locked="false",powered="false")
    repeatPlusZ = BlockState("minecraft:repeater",
                            delay="1",facing="north",locked="false",powered="false")

    data = {
            "name"       :"Computational MineWire",
            "author"     :"MineWire",
            "description":"MineWire generated",
            "output"     :"./output.litematic"
    }

def safeCurruptBlocks():
    global Blocks
    old = Blocks
    next = Blocks()
    next.__dict__ = old.__dict__.copy()
    Blocks = next

def main(settings,module):
    safeCurruptBlocks()
    mc_settings = settings["minecraft"]
    schem_settings = mc_settings["mc-schematic"]
    block_settings = mc_settings["blocks"]
    Blocks.__dict__ = Blocks.__dict__.copy()
    for k,v in schem_settings.items():
        Blocks.data[k] = v
    for k,v in block_settings.items():
        cp = v.copy()
        cp.pop("_id")
        Blocks.__dict__[k] = BlockState(v["_id"],**cp)

