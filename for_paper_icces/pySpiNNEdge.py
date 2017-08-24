#!/usr/bin/python
"""
This is the GUI for Edge Detector.
"""

from PyQt4 import Qt
import sys
from QtForms import edgeGUI
import argparse

DEF_IMAGE_DIR = "images"

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='GUI for Image Processing on SpiNNaker.')
    parser.add_argument("-n", "--nodeNum", type=int, help="Number of nodes (for ICCES, default is 1)", default=1)
    parser.add_argument("-f", "--fastMode", help="non-interactive image loading and sending", action="store_true")
    parser.add_argument("-i", "--image", type=str, help="Image file")
    args = parser.parse_args()

    if args.fastMode:
        if args.image is None:
            print "Please provide the image for fastMode"
            sys.exit(-1)

    app = Qt.QApplication(sys.argv)
    gui = edgeGUI(def_image_dir=DEF_IMAGE_DIR, jmlNode=args.nodeNum, fastMode=args.fastMode, img=args.image)
    gui.show()
    sys.exit(app.exec_())

