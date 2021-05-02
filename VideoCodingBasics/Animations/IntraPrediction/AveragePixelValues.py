import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import numpy

def processFile(inputFile, outputFile):
  print(f"Processing file {inputFile}")
  img = mpimg.imread(inputFile)

  wh = 106
  positionsX = [582, 689, 796, 903]
  positionsY = [172, 279, 386, 493]

  for x in positionsX:
    for y in positionsY:
      averages = numpy.average(img[y+1: y+wh-2, x+1: x+wh-2], (0, 1))
      assert(averages.shape == (3,))
      for i in range(3):
        img[y: y+wh, x: x+wh, i].fill(averages[i])

  mpimg.imsave(outputFile, img)

def main():
  inputFolder = "BlenderRender"
  outputFolder = "Filtered"
  
  allFiles = []
  for f in os.listdir(inputFolder):
    if (os.path.isfile(inputFolder + "/" + f) and f.endswith(".png")):
      allFiles.append(f)

  print(f"Found {len(allFiles)} PNG files")

  for f in allFiles:
    processFile(inputFolder + "/" + f, outputFolder + "/" + f)

if __name__ == "__main__":
  main()
