#!/usr/bin/python

# Import PySide classes
import sys
from PySide.QtCore import *
from PySide.QtGui import *

# import Python Image Library
import PIL.ImageFile

# Import cinema IO
import IO.cinema_store

#open up a store
cs = IO.cinema_store.FileStore(sys.argv[1])
cs.load()

#from list of tracks, find default for each to make up a query
aselection = {}
for key, val in cs.descriptor_definition.iteritems():
    aselection[key] = val[u'default']

#find that default image
doc = cs.find(aselection).next() #only care about first one here

#load it into PIL
imageparser = PIL.ImageFile.Parser()
imageparser.feed(doc.data)
pimg = imageparser.close()

# Show it in Qt
app = QApplication(sys.argv)

qimg = QImage(pimg.tostring('raw', 'RGB'), pimg.size[0], pimg.size[1], QImage.Format_RGB888)
pix = QPixmap.fromImage(qimg)
lbl = QLabel()
lbl.setPixmap(pix)
lbl.show()

# Enter Qt application main loop
app.exec_()
sys.exit()
