
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

class SchemGen:
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
        rx = x * 3
        dz = z * 3
        if(direction & 1):dx = rx + 1
        else             :dx = rx - 1
        region[dx,1,dz] = Blocks.baseBlock
        region[dx,2,dz] = Blocks.wireBlock
        region[rx,2,dz] = Blocks.upBlock
    def buildNotDown(region,x,z,direction=0):
        dx = x * 3
        dz = z * 3
        if(direction & 1):
            region[dx + 1,2,dz] = Blocks.torchPlusX
        else             :
            region[dx - 1,2,dz] = Blocks.torchMinusX
    def buildIndDown(region,x,z,direction=0):
        dz = z * 3
        dx = x * 3
        if(direction & 1):
            region[dx + 1,2,dz] = Blocks.repeatPlusX
            region[dx + 1,1,dz] = Blocks.baseBlock
            if(region[dx + 2,2,dz].id == "minecraft:air"):
                region[dx + 2,2,dz] = Blocks.baseBlock
        else             :
            region[dx - 1,2,dz] = Blocks.repeatMinusX
            region[dx - 1,1,dz] = Blocks.baseBlock
            if(region[dx - 2,2,dz].id == "minecraft:air"):
                region[dx - 2,2,dz] = Blocks.baseBlock


    def placeGridWires(region,size):
        for x in range(-1,size):
            for z in range((size + 2) // 3):
                region[x    ,0,z * 3] = Blocks.baseBlock
                region[x    ,1,z * 3] = Blocks.wireBlock
                region[z * 3,2,x    ] = Blocks.baseBlock
                region[z * 3,3,x    ] = Blocks.wireBlock

    def schematicTraceWire(region,wire):
        st = (wire.start  ) * 3
        ed = (wire.end + 1) * 3
        lane = wire.lane * 3
        for x in range(st,ed - 2):
            region[x,0,lane] = Blocks.baseBlock
            region[x,1,lane] = Blocks.wireBlock
    def schematicTraceConn(region,conn):
        st = (conn.start  ) * 3
        ed = (conn.end + 1) * 3
        lane = conn.lane * 3
        for x in range(st,ed - 2):
            region[lane,2,x] = Blocks.baseBlock
            region[lane,3,x] = Blocks.wireBlock
        offset = 0
        outStart = conn.outLet[0].wire.lane
        doRepeat = True
        while doRepeat:
            doRepeat = False
            offset += 1
            pz = (outStart + offset) * 3
            nz = (outStart - offset) * 3
            if(outStart - offset > conn.start):
                doCollide = False
                doRepeat = True
                for cx in conn.inLet:
                    if(cx.wire.lane == outStart - offset and not cx.inverting):
                        doCollide = True
                        break
                else:
                    region[lane,3,nz] = Blocks.repeatPlusZ
                if(doCollide):
                    region[lane,3,nz + 1] = Blocks.repeatPlusZ
            if(outStart + offset < conn.end  ):
                doCollide = False
                doRepeat = True
                for cx in conn.inLet:
                    if(cx.wire.lane == outStart - offset and not cx.inverting):
                        doCollide = True
                        break
                else:
                    region[lane,3,pz] = Blocks.repeatMinusZ
                if(doCollide):
                    region[lane,3,pz - 1] = Blocks.repeatMinusZ
        ##


    def _schematicPlaceCross(region,cx,direction):
        conn = cx.conn
        wire = cx.wire
        if(not cx.dirUp):
            if(cx.inverting):
                SchemGen.buildNotDown(region,conn.lane,wire.lane,direction)
            else:
                SchemGen.buildIndDown(region,conn.lane,wire.lane,direction)
        else:
            if(cx.inverting):
                SchemGen.buildNotTower(region,conn.lane,wire.lane,direction)
            else:
                SchemGen.buildIndTower(region,conn.lane,wire.lane,direction)
    def schematicPlaceCross(region,cx):
        conn = cx.conn
        wire = cx.wire
        dirTyp = 0
        if(conn.lane > wire.start): dirTyp |= 1
        if(conn.lane < wire.end  ): dirTyp |= 2
        # TODO add a selector here!
        if(wire.lane > conn.start): dirTyp |= 4
        if(wire.lane < conn.end  ): dirTyp |= 8
        if(dirTyp == 0):print("(2026-08-23T17:00:17) Error")
        if(dirTyp & 1 and dirTyp & 4):
            SchemGen._schematicPlaceCross(region,cx,0)
        elif(dirTyp & 2 and dirTyp & 4):
            SchemGen._schematicPlaceCross(region,cx,1)
        elif(dirTyp & 1 and dirTyp & 8):
            SchemGen._schematicPlaceCross(region,cx,2)
        elif(dirTyp & 2 and dirTyp & 8):
            SchemGen._schematicPlaceCross(region,cx,3)

def setupSettings(settings):
    joining = {
            "Save"       :"./output.litematic",
            "Name"       :"Computational Stuff",
            "Author"     :"MineWire",
            "Description":"MineWire",
    }
    for k,v in joining.items():
        if(k not in settings):settings[k] = v

def createSchematic(settings,module):
    setupSettings(settings)
    region = Region(-2,0,-2,100,6,100)
    schematic = region.as_schematic(name=settings["Name"],
                                 author=settings["Author"],
                                 description=settings["Description"])
    for mwire in module.namedWires:
        SchemGen.schematicTraceWire(region,mwire)
    for mconn in module.connections:
        SchemGen.schematicTraceConn(region,mconn)
    for mconn in module.connections:
        for cx in mconn.inLet:
            SchemGen.schematicPlaceCross(region,cx)
        for cx in mconn.outLet:
            SchemGen.schematicPlaceCross(region,cx)

    schematic.save(settings["Save"])


def main():
    settings = {}
    setupSettings(settings)
    size = 100
    region = Region(0,0,0,size,6,size)
    schematic = region.as_schematic(name=settings["Name"],
                                 author=settings["Author"],
                                 description=settings["Description"])
    SchemGen.placeGridWires(region,size)
    #
    schematic.save(settings["Save"])

if __name__ == "__main__":main()
