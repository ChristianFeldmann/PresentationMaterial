import av

class BlockData:
    def __init__(self):
        self.type = ""
        self.pos = (0, 0)
        self.size = (0, 0)
    def getCUidx(self, widthInCU):
        xIdx = self.pos[0] // 64
        yIdx = self.pos[1] // 64
        return yIdx * widthInCU + xIdx

class YuvFrame:
    def __init__(self, imgSize):
        self.Y = None
        self.U = None
        self.V = None
        self.size = imgSize
    def createBlankFrame(self, fill=None):
        lumaSize = self.size[0] * self.size[1]
        self.Y = bytearray(lumaSize)
        self.U = bytearray(lumaSize // 4)
        self.V = bytearray(lumaSize // 4)
        if (fill == "black"):
            self.fillWithColor(0, 128, 128)
        if (fill == "grey"):
            self.fillWithColor(128, 128, 128)
    def fillWithColor(self, Y, U, V):
        lumaSize = self.size[0] * self.size[1]
        for i in range(lumaSize):
            self.Y[i] = Y
        for i in range(lumaSize // 4):
            self.U[i] = U
            self.V[i] = V
    def readFrame(self, f):
        lumaSize = self.size[0] * self.size[1]
        self.Y = f.read(lumaSize)
        if (len(self.Y) < lumaSize):
            return False
        chromaSize = lumaSize // 4
        self.U = f.read(chromaSize)
        if (len(self.U) < chromaSize):
            return False
        self.V = f.read(chromaSize)
        if (len(self.V) < chromaSize):
            return False
        return True
    def writeFrameToFile(self, f):
        f.write(self.Y)
        f.write(self.U)
        f.write(self.V)
    def copyDataToAVFrame(self, frame : av.VideoFrame):
        planes = frame.planes
        assert self.size[0] == frame.width
        assert self.Y != None and self.U != None and self.V != None
        if (self.size[1] == frame.height):
            planes[0].update(self.Y)
            planes[1].update(self.U)
            planes[2].update(self.V)
        else:
            assert self.size[1] < frame.height
            # Luma
            linesAboveBelow = ((frame.height - self.size[1]) // 2)
            dataBlackBar = bytearray(linesAboveBelow * frame.width)
            tmpArray = dataBlackBar + self.Y + dataBlackBar
            planes[0].update(tmpArray)
            # Chroma
            linesAboveBelow = linesAboveBelow // 2
            dataBlackBar = bytearray([128] * (linesAboveBelow * frame.width // 2))
            planes[1].update(dataBlackBar + self.U + dataBlackBar)
            planes[2].update(dataBlackBar + self.V + dataBlackBar)
    def copyBlockToFrame(self, out, block, offsetInDst=(0, 0), copyChroma=True, multiplyer=1):
        if (block.size[0] == 0 or block.size[1] == 0):
            return
        for y in range(block.size[1]):
            for x in range(block.size[0]):
                idxLumaIn = (y + block.pos[1]) * self.size[0] + x + block.pos[0]
                idxLumaOut = (y + offsetInDst[1]) * out.size[0] + x + offsetInDst[0]
                if (multiplyer == 1):
                    out.Y[idxLumaOut] = self.Y[idxLumaIn]
                else:
                    Y = (self.Y[idxLumaIn] - 128) * multiplyer + 128
                    if (Y < 0):
                        Y = 0
                    if (Y > 255):
                        Y = 255
                    out.Y[idxLumaOut] = Y
        if (not copyChroma):
            return
        for y in range(block.size[1] // 2):
            for x in range(block.size[0] // 2):
                idxChromaIn = (y + block.pos[1] // 2) * self.size[0] // 2 + x + block.pos[1] // 2
                idxChromaOut = (y + offsetInDst[1] // 2) * out.size[0] // 2 + x + offsetInDst[0] // 2
                if (multiplyer != 1):
                    U = (self.U[idxChromaIn] - 128) * multiplyer + 128
                    V = (self.V[idxChromaIn] - 128) * multiplyer + 128
                    if (U < 0):
                        U = 0
                    if (U > 255):
                        U = 255
                    if (V < 0):
                        V = 0
                    if (V > 255):
                        V = 255
                    out.U[idxChromaOut] = (self.U[idxChromaIn] - 128) * multiplyer + 128
                    out.V[idxChromaOut] = (self.V[idxChromaIn] - 128) * multiplyer + 128
                else:
                    out.U[idxChromaOut] = self.U[idxChromaIn]
                    out.V[idxChromaOut] = self.V[idxChromaIn]

class YuvFile:
    def __init__(self, imgSize, filename):
        self.frames = []
        self.size = imgSize
        self._loadFile(filename)
    def _loadFile(self, filename):
        f = open(filename, "rb")
        frame = YuvFrame(self.size)
        while (frame.readFrame(f)):
            self.frames.append(frame)
            frame = YuvFrame(self.size)
        print("Read {} frames from file {}.".format(len(self.frames), filename))
    def nrFrames(self):
        return len(self.frames)

def copyAndAddBlockToFrame(pred, resi, out, block, offsetInDst=(0, 0), copyChroma=True):
    if (block.size[0] == 0 or block.size[1] == 0):
        return
    for y in range(block.size[1]):
        for x in range(block.size[0]):
            idxLumaIn = (y + block.pos[1]) * pred.size[0] + x + block.pos[0]
            idxLumaOut = (y + offsetInDst[1]) * out.size[0] + x + offsetInDst[0]
            o = pred.Y[idxLumaIn] + (resi.Y[idxLumaIn] - 128)
            if (o > 255):
                o = 255
            if (o < 0):
                o = 0
            out.Y[idxLumaOut] = o
    if (not copyChroma):
        return
    for y in range(block.size[1] // 2):
        for x in range(block.size[0] // 2):
            idxChromaIn = (y + block.pos[1] // 2) * pred.size[0] // 2 + x + block.pos[0] // 2
            idxChromaOut = (y + offsetInDst[1] // 2) * out.size[0] // 2 + x + offsetInDst[0] // 2
            uo = pred.U[idxChromaIn] + (resi.U[idxChromaIn] - 128)
            vo = pred.V[idxChromaIn] + (resi.V[idxChromaIn] - 128)
            if (uo < 0):
                uo = 0
            if (uo > 255):
                uo = 255
            if (vo < 0):
                vo = 0
            if (vo > 255):
                vo = 255
            out.U[idxChromaOut] = uo
            out.V[idxChromaOut] = vo