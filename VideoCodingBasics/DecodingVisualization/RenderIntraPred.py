from Common import YuvFrame, YuvFile, BlockData

def intraPredDC(width, height, topRowPixels, leftRowPixels):
    predFrame = YuvFrame((width, height))
    predFrame.createBlankFrame("black")
    
    iSum = 0
    for x in range(width):
        iSum += topRowPixels[x + 1]
    for y in range(height):
        iSum += leftRowPixels[y + 1]

    pDcVal = int((iSum + width) / (width + height))

    predFrame = YuvFrame((width, height))
    predFrame.createBlankFrame()
    predFrame.fillWithColor(pDcVal, 128, 128)

    return predFrame

def intraPred(width, height, dirMode, topRowPixels, leftRowPixels):
    HOR_IDX = 10
    VER_IDX = 26
    edgeFilter = False

    if (dirMode <= 1):
        return

    predFrame = YuvFrame((width, height))
    predFrame.createBlankFrame("black")

    bIsModeVer = (dirMode >= 18)
    intraPredAngleMode =  -(dirMode - HOR_IDX)
    if (bIsModeVer):
        intraPredAngleMode = dirMode - VER_IDX
    absAngMode = abs(intraPredAngleMode)
    signAng = 1
    if (intraPredAngleMode < 0):
        signAng = -1
    angTable = [0, 2, 5, 9, 13, 17, 21, 26, 32]
    absAng = angTable[absAngMode]
    intraPredAngle = signAng * absAng
    invAngTable = [0, 4096, 1638, 910, 630, 482, 390, 315, 256]
    invAngle = invAngTable[absAngMode]

    MAX_CU_SIZE = 64
    refAbove = bytearray(2*MAX_CU_SIZE + 1)
    refLeft = bytearray(2*MAX_CU_SIZE + 1)

    # Initialize the Main and Left reference array.
    if (intraPredAngle < 0):
        refMainOffsetPreScale = width - 1
        if (bIsModeVer):
            refMainOffsetPreScale = height - 1
        refMainOffset = height - 1

        for x in range(width + 1):
            refAbove[x+refMainOffset] = topRowPixels[x]
        for y in range(height + 1):
            refLeft[y+refMainOffset] = leftRowPixels[y]
        
        invAngleSum = 128
        kend = ((refMainOffsetPreScale+1)*intraPredAngle) >> 5
        for k in range(-1, kend, -1):
            invAngleSum += invAngle
            refMainIdx = refMainOffset + k
            refSideIdx = refMainOffset + (invAngleSum>>8)
            if (bIsModeVer):
                refAbove[refMainIdx] = refLeft[refSideIdx]
            else:
                refLeft[refMainIdx] = refAbove[refSideIdx]
    else: # intraPredAngle >= 0
        refMainOffset = 0
        for x in range(2*width+1):
            refAbove[x] = topRowPixels[x]
        for y in range(2*height+1):
            refLeft[y] = leftRowPixels[y]

    refMain = refLeft
    refSide = refAbove
    if (bIsModeVer):
        refMain = refAbove
        refSide = refLeft
    
    if (intraPredAngle == 0):
        for y in range(height):
            for x in range(width):
                predFrame.Y[y*width+x] = refMain[x+1]
        if (edgeFilter):
            pass
    else:
        deltaPos=intraPredAngle
        for y in range(height):
            deltaInt   = deltaPos >> 5
            deltaFract = deltaPos & (32 - 1)
            if (deltaFract):
                # Do linear filtering
                pRMIdx = refMainOffset + deltaInt + 1
                lastRefMainPel = refMain[pRMIdx]
                pRMIdx += 1
                for x in range(width):
                    thisRefMainPel = refMain[pRMIdx]
                    predFrame.Y[y*width + x] = ( ((32-deltaFract)*lastRefMainPel + deltaFract*thisRefMainPel +16) >> 5 )
                    lastRefMainPel = thisRefMainPel
                    pRMIdx += 1
            else:
                # Just copy the integer samples
                for x in range(width):
                    predFrame.Y[y*width + x] = refMain[refMainOffset + x + deltaInt + 1]
            deltaPos+=intraPredAngle
    
    # Flip the block if this is the horizontal mode
    if not bIsModeVer:
        flippedFrame = YuvFrame((width, height))
        flippedFrame.createBlankFrame("black")
        for y in range(height):
            for x in range(width):
                flippedFrame.Y[x * width + y] = predFrame.Y[y * width + x]
        return flippedFrame

    return predFrame

def main():
    
    # The first pixel is the same pixel (top left) where the rows meet
    topRowPixels = [10, 20, 30, 50, 90, 200, 255, 255, 255, 160, 100, 20, 20, 10, 10, 10, 20, 30, 50, 90, 200, 255, 255, 255, 160, 100, 20, 20, 10, 10, 10, 10, 10, 10]
    leftRowPixels = [10, 20, 30, 50, 90, 200, 255, 255, 255, 160, 100, 20, 20, 10, 10, 10, 20, 30, 50, 90, 200, 255, 255, 255, 160, 100, 20, 20, 10, 10, 10, 10, 10, 10]

    f = open("intraPredTest.yuv", "wb")
    for dirMode in range(1, 35):
        if (dirMode == 1):
            predFrame = intraPredDC(16, 16, topRowPixels, leftRowPixels)
        else:
            predFrame = intraPred(16, 16, dirMode, topRowPixels, leftRowPixels)

        outFrame = YuvFrame((34, 34))
        outFrame.createBlankFrame("grey")

        # Copy top and left row
        for x in range(33):
            outFrame.Y[x] = topRowPixels[x]
        for y in range(33):
            outFrame.Y[y*34] = leftRowPixels[y]
        
        # Copy pred block
        predBlock = BlockData()
        predBlock.size = (16, 16)
        predFrame.copyBlockToFrame(outFrame, predBlock, (1, 1), False)

        # Write frame
        outFrame.writeFrameToFile(f)

if __name__ == "__main__":
    main()