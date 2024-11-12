import subprocess
from subprocess import PIPE
import sys
import os
from Common import YuvFile, YuvFrame, BlockData, copyAndAddBlockToFrame
import av
import math

def fillListsWithNoneToSameLength(data):
    maxLength = 0
    for d in data:
        if len(d) > maxLength:
            maxLength = len(d)
    for d in data:
        fillAmount = maxLength - len(d)
        for i in range(fillAmount):
            d.append(None)

class FrameDecodingOrder:
    def __init__(self):
        self._data = []
        self.width = 0
        self.height = 0
    def parseLine(self, line):
        lineSplit = line.split(";")
        if (len(lineSplit) == 5):
            b = BlockData()
            b.type = lineSplit[0]
            b.pos = (int(lineSplit[1]), int(lineSplit[2]))
            b.size = (int(lineSplit[3]), int(lineSplit[4]))
            self._data.append(b)
            w = b.pos[0] + b.size[0]
            h = b.pos[1] + b.size[1]
            if (w > self.width):
                self.width = w
            if (h > self.height):
                self.height = h
    def getBlockLists(self, mode = "none"):
        assert mode in ["none", "slice", "Tiles", "Wavefront"]
        if (mode == "none"):
            return [self._data]
        widthCU = math.ceil(self.width / 64)
        heightCU = math.ceil(self.height / 64)
        nrCU = widthCU * heightCU
        if (mode == "slice"):
            nrSlices = 4
            nrCUPerSlice = math.ceil(nrCU / nrSlices)
            nextSliceEnd = nrCUPerSlice
            data = [ [] for _ in range(nrSlices) ]
            threadIdx = 0
            for block in self._data:
                if (block.getCUidx(widthCU) >= nextSliceEnd):
                    threadIdx += 1
                    nextSliceEnd += nrCUPerSlice
                data[threadIdx].append(block)
            fillListsWithNoneToSameLength(data)
            return data
        if (mode == "Tiles"):
            data = [ [] for _ in range(4) ]
            xLimit = (widthCU // 2 * 64)
            yLimit = (heightCU // 2 * 64)
            data = [ [] for _ in range(4) ]
            for block in self._data:
                threadIdx = 0
                if (block.pos[0] >= xLimit):
                    threadIdx += 1
                if (block.pos[1] >= yLimit):
                    threadIdx += 2
                data[threadIdx].append(block)
            fillListsWithNoneToSameLength(data)
            return data
        if (mode == "Wavefront"):
            nrWavefronts = heightCU
            data = [ [] for _ in range(nrWavefronts) ]
            
            dataIdx = []
            for y in range(heightCU):
                startCUIdx = y * widthCU
                for blockIdx, block in enumerate(self._data):
                    if block.getCUidx(widthCU) == startCUIdx:
                        dataIdx.append(blockIdx)
                        break
            assert len(dataIdx) == heightCU

            while True:
                anyThreadWorking = False
                for threadIdx in range(heightCU):
                    if (dataIdx[threadIdx] >= len(self._data)):
                        # We are done
                        fillListsWithNoneToSameLength(data)
                        return data
                    curBlock = self._data[dataIdx[threadIdx]]
                    threadBusy = True
                    curThreadCUIdx = curBlock.getCUidx(widthCU)
                    startCUIdx = threadIdx * widthCU
                    endCUIdx = startCUIdx + widthCU
                    if threadIdx == 0:
                        prevThreadCUIdx = curBlock.getCUidx(widthCU)
                    else:
                        prevThreadWorking = prevThreadCUIdx < startCUIdx
                        if (prevThreadWorking and prevThreadCUIdx < curThreadCUIdx - widthCU + 2):
                            threadBusy = False
                        prevThreadCUIdx = curThreadCUIdx
                    
                    if (curThreadCUIdx < startCUIdx or curThreadCUIdx >= endCUIdx):
                        threadBusy = False

                    if (threadBusy):
                        data[threadIdx].append(curBlock)
                        dataIdx[threadIdx] = dataIdx[threadIdx] + 1
                        anyThreadWorking = True
                    else:
                        data[threadIdx].append(None)

                if (not anyThreadWorking):
                    break

            fillListsWithNoneToSameLength(data)
            return data
        return []

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
                print("Data read {} blocks".format(len(frameData._data)))
                self.frameData[poc] = frameData
                frameData = FrameDecodingOrder()
            else:
                frameData.parseLine(line)
        print("Read {} frames data from file {}.".format(len(self.frameData), filename))
    def nrFrames(self):
        return len(self.frameData)

def main():
    filePred = YuvFile([1920, 872], "pred_1920x872_24.yuv")
    fileResi = YuvFile([1920, 872], "resi_1920x872_24.yuv")
    fileRec  = YuvFile([1920, 872], "rec_1920x872_24.yuv")

    decodingOrderData = decodingOrderFile("strQP38.dec.txt")

    nrFrames = decodingOrderData.nrFrames()
    assert(filePred.nrFrames() == nrFrames)
    assert(fileResi.nrFrames() == nrFrames)
    assert(fileRec.nrFrames() == nrFrames)

    outputVideo = av.open("render.mp4", 'w')
    videoStream = outputVideo.add_stream("libx264", 60, options={'crf': '0'})
    videoStream.pix_fmt = 'yuv420p'
    videoStream.width = 1920
    videoStream.height = 1080

    mode = "Wavefront"
    # How to use an overloay graph:
    # https://github.com/PyAV-Org/PyAV/issues/239
    # But this is too compülicated. The solution for now is: Here we do a lossless (CRF0) encode and then use ffmpeg to add the overlay

    for i in range(nrFrames):
        print("Processing frame {}".format(i))
        out_data = b''

        outFrame = YuvFrame((1920, 872))
        outFrame.createBlankFrame()
        rec = fileRec.frames[i]
        pred = filePred.frames[i]
        resi = fileResi.frames[i]

        dataPerThread = decodingOrderData.frameData[i].getBlockLists(mode)
        nrThreads = len(dataPerThread)
        blocksPerThread = len(dataPerThread[0])
        for data in dataPerThread:
            assert len(data) == blocksPerThread

        for blockNr in range(blocksPerThread):
            for j in range(3):
                for t in range(nrThreads):
                    block = dataPerThread[t][blockNr]
                    if (block == None):
                        continue

                    if (j == 0):
                        pred.copyBlockToFrame(outFrame, block, block.pos)
                    elif (j == 1):
                        resi.copyBlockToFrame(outFrame, block, block.pos, True, 2)
                    else:
                        copyAndAddBlockToFrame(pred, resi, outFrame, block, block.pos)

                frame = av.VideoFrame(1920, 1080, 'yuv420p')
                outFrame.copyDataToAVFrame(frame)
                packet = videoStream.encode(frame)
                outputVideo.mux(packet)

            # if (blockNr > 200):
            #     break

    packet = videoStream.encode(None)
    outputVideo.mux(packet)

    outputVideo.close()

if __name__ == "__main__":
    main()
