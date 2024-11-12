from Common import YuvFile, YuvFrame, BlockData

def main():
    filePred = YuvFile([2048, 872], "D:/Bitmovin/yuv/sintel_2048x872_yuv420p.yuv")
    yuvFile = open("SintelCropped_64x64.yuv", "wb")
    
    for i in range(3):
        f = filePred.frames[i]
        print("Processing frame {}".format(i))
        out_data = b''

        outFrame = YuvFrame((64, 64))
        outFrame.createBlankFrame()

        block = BlockData()
        block.size = (64, 64)
        srcPos = (250, 660)
        f.copyBlockToFrame(outFrame, block, srcPos)
        outFrame.writeFrameToFile(yuvFile)


if __name__ == "__main__":
    main()