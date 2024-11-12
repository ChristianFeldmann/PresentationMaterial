import subprocess
from subprocess import PIPE
import sys
import os
from Common import YuvFile, YuvFrame, BlockData, copyAndAddBlockToFrame

class FrameDecodingOrder:
    def __init__(self):
        self.data = []
    def parseLine(self, line):
        lineSplit = line.split(";")
        if (len(lineSplit) == 5):
            b = BlockData()
            b.type = lineSplit[0]
            b.pos = (int(lineSplit[1]), int(lineSplit[2]))
            b.size = (int(lineSplit[3]), int(lineSplit[4]))
            self.data.append(b)

class decodingOrderFile:
    def __init__(self, filename):
        self.frameData = {}
        self._readFile(filename)
    def _readFile(self, filename):
        f = open(filename, "r")
        frameData = FrameDecodingOrder()
        for line in f:
            if line.startswith("POC"):
                lineSplit = line.split()
                poc = int(lineSplit[1])
                print("Data read {} blocks".format(len(frameData.data)))
                self.frameData[poc] = frameData
                frameData = FrameDecodingOrder()
            else:
                frameData.parseLine(line)
        print("Read {} frames data from file {}.".format(len(self.frameData), filename))
    def nrFrames(self):
        return len(self.frameData)

def encodeYUVUsingX264(inFileName, outFileName, frameSize, framerate):
    print("Encoding file " + inFileName)
    exe_x264 = "D:/Projekte/x264.exe"
    cmd_x264 = [
        exe_x264,
        "--demuxer", "raw",
        "--input-csp", "i420",
        "--input-res", "{0:d}x{1:d}".format(frameSize[0], frameSize[1]),
        "--fps", "{0:f}".format(framerate),
        "--crf", "15",
        "--output", outFileName,
        inFileName
    ]
    subprocess.call(cmd_x264)

def main():
    filePred = YuvFile([2048, 872], "pred_2048x872_24.yuv")
    fileResi = YuvFile([2048, 872], "resi_2048x872_24.yuv")
    fileRec  = YuvFile([2048, 872], "rec_2048x872_24.yuv")

    decodingOrderData = decodingOrderFile("str.dec.txt")

    nrFrames = decodingOrderData.nrFrames()
    assert(filePred.nrFrames() == nrFrames)
    assert(fileResi.nrFrames() == nrFrames)
    assert(fileRec.nrFrames() == nrFrames)

    blockX = 4*64
    blockY = 10*64

    SEGMENTSIZEFRAMES = 1000
    
    for i in range(nrFrames):
        print("Processing frame {}".format(i))
        out_data = b''

        outFrame = YuvFrame((64, 64))
        outFrame.createBlankFrame("black")
        rec = fileRec.frames[i]
        pred = filePred.frames[i]
        resi = fileResi.frames[i]

        tempYUVFileName = "blocks/render_64x64_24_{}.yuv".format(i)
        tempYUVFile = open(tempYUVFileName, "wb")
        outFrame.writeFrameToFile(tempYUVFile)

        for block in decodingOrderData.frameData[i].data:
            if (block.pos[0] >= blockX and block.pos[0] < blockX + 64 and block.pos[1] >= blockY and block.pos[1] < blockY + 64):
                offsetInDstX = block.pos[0] - blockX
                offsetInDstY = block.pos[1] - blockY
                for j in range(3):
                    if (j == 0):
                        pred.copyBlockToFrame(outFrame, block, (offsetInDstX, offsetInDstY))
                    elif (j == 1):
                        resi.copyBlockToFrame(outFrame, block, (offsetInDstX, offsetInDstY), True, 2)
                    else:
                        copyAndAddBlockToFrame(pred, resi, outFrame, block, (offsetInDstX, offsetInDstY))
                    outFrame.writeFrameToFile(tempYUVFile)

        # Add the filtered output
        outFrame.createBlankFrame("black")
        block = BlockData()
        block.size = (64, 64)
        block.pos = (blockX, blockY)
        rec.copyBlockToFrame(outFrame, block)
        outFrame.writeFrameToFile(tempYUVFile)

if __name__ == "__main__":
    main()
