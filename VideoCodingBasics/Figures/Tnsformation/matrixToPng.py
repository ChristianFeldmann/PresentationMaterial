import cv2
import numpy
import scipy.fftpack

data = [[190, 255, 255,  21,   0,  28,  54,  75], 
        [237, 255, 255,  35,  58,  93, 112, 119], 
        [255, 255, 234, 110, 121, 119, 112, 108], 
        [187, 140, 110, 110, 109, 101,  99,  97], 
        [105, 105, 103, 103, 100, 100, 103, 100], 
        [105, 105, 103, 105, 103, 105, 105, 105], 
        [105, 105, 108, 108, 110, 110, 110, 110], 
        [108, 110, 115, 115, 115, 115, 117, 119]]

arr = numpy.array(data)

# Write the data into an image
cv2.imwrite('SingleBlock.png',arr)

# Do the forward transform
coefficients = scipy.fftpack.dct(scipy.fftpack.dct(arr.T, norm="ortho").T, norm="ortho")

# Print data to output
numpy.set_printoptions(precision=2)
numpy.set_printoptions(suppress=True)
print(coefficients)

# Scale the values to 0-255 so that we can see something
valueRange = coefficients.max() - coefficients.min()
if (valueRange == 0):
  valueRange = 1
coefficientsScaled = (coefficients - coefficients.min()) / valueRange * 255

cv2.imwrite(f"TransformCoefficients.png", coefficientsScaled) 
