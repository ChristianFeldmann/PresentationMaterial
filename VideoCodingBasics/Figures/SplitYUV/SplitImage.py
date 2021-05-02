import cv2
 
#read image
src = cv2.imread('SplitImage.png', cv2.IMREAD_UNCHANGED)
print(src.shape)

#extract red channel
red_channel = src[:,:,2]
green_channel = src[:,:,1]
blue_channel = src[:,:,0]

#write red channel to greyscale image
cv2.imwrite('SplitImageRed.png',red_channel) 
cv2.imwrite('SplitImageGreen.png',green_channel) 
cv2.imwrite('SplitImageBlue.png',blue_channel) 

src_yuv = cv2.cvtColor(src, cv2.COLOR_BGR2YUV)

print(src_yuv.shape)

Y = src_yuv[:,:,0]
U = src_yuv[:,:,1]
V = src_yuv[:,:,2]

cv2.imwrite('SplitImageY.png',Y) 
cv2.imwrite('SplitImageU.png',U) 
cv2.imwrite('SplitImageV.png',V) 
