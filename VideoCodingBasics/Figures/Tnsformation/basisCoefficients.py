import cv2
import numpy
import scipy.fftpack

for y in range(8):
  for x in range(8):
    # Create coefficients. Set only coefficients at (x,y) to 1.
    # All other coefficients are 0.
    coefficients = numpy.zeros((8, 8))
    coefficients[y, x] = 1.0

    # Do the inverste transformation back into the pixel domain
    img = scipy.fftpack.idct(scipy.fftpack.idct(coefficients.T, norm="ortho").T, norm="ortho")
    # Scale the values to 0-255 so that we can see something
    valueRange = img.max() - img.min()
    if (valueRange == 0):
      valueRange = 1
    imgScaled = (img - img.min()) / valueRange * 255

    cv2.imwrite(f"outImages/trans-{y}-{x}.png",imgScaled) 
