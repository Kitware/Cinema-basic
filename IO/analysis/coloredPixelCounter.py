

import re, os, argparse
from PIL import Image


def calculateCoverage(imagePath, bgColor):
    img = Image.open(imagePath)

    """
    print "size: ",img.size
    print "format: ",img.format
    print "mode:",img.mode
    print "palette:",img.palette
    print "info: ",img.info
    """

    numPixels = img.size[0] * img.size[1]
    bgCount = 0
    fgCount = 0

    for pixel in img.getdata():
        if pixel[0] == bgColor[0] and pixel[1] == bgColor[1] and pixel[2] == bgColor[2]:
            # white pixel => background
            bgCount += 1
        else:
            fgCount += 1

    # print 'background count: ',bgCount,", foreground count: ",fgCount

    if (bgCount + fgCount) != numPixels:
        print "  ***********  ERROR: Number of pixels do not add up  ***********  "

    return float(fgCount) / numPixels * 100.0


if __name__ == "__main__":
    description = "Python script read an image and calculate the colored pixel coverage"

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("--imgpath", type=str, default="", help="Path to an image")
    parser.add_argument("--bgcolor", type=str, default="(255,255,255)", help="A tuple of values representing the image background color")

    args = parser.parse_args()

    bgColor = [255, 255, 255]

    regex = re.compile('\(([^\)]+)\)')
    m = regex.search(args.bgcolor)
    if m:
        print 'Matched a background color',m.group(1)
        bgColor = [ int(c) for c in m.group(1).split(',') ]

    percentCoverage = calculateCoverage(args.imgpath, bgColor)

    print "Percent coverage: ",percentCoverage
