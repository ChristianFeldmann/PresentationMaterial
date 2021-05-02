import cv2
import numpy
import scipy.fftpack

data = numpy.array([[190, 255, 255,  21,   0,  28,  54,  75],
                    [237, 255, 255,  35,  58,  93, 112, 119],
                    [255, 255, 234, 110, 121, 119, 112, 108],
                    [187, 140, 110, 110, 109, 101,  99,  97],
                    [105, 105, 103, 103, 100, 100, 103, 100],
                    [105, 105, 103, 105, 103, 105, 105, 105],
                    [105, 105, 108, 108, 110, 110, 110, 110],
                    [108, 110, 115, 115, 115, 115, 117, 119]])

for quant in [10, 20, 50, 100, 200, 400]:

  # Do the forward transform
  coefficients = scipy.fftpack.dct(scipy.fftpack.dct(data.T, norm="ortho").T, norm="ortho")

  # Do the quantization
  quantCoeff = numpy.round(coefficients / quant)
  deQuantCoeff = quantCoeff * quant

  #print(deQuantCoeff)

  # Do the inverste transformation back into the pixel domain
  rec = scipy.fftpack.idct(scipy.fftpack.idct(deQuantCoeff.T, norm="ortho").T, norm="ortho")

  cv2.imwrite(f"rec-quant{quant}.png",rec)
