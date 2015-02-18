
#!/usr/bin/python

# Import PySide classes
import sys
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *

# import Python Image Library
import PIL.ImageFile

# Import cinema IO
import IO.cinema_store

#open up a store
cs = IO.cinema_store.FileStore(sys.argv[1])
cs.load()

#from list of tracks, find default for each to make up a query
aselection = {}
#for key, val in cs.descriptor_definition.iteritems():
#    aselection[key] = val[u'default']

#find that default image
#doc = cs.find(aselection).next() #only care about first one here

#load it into PIL
#imageparser = PIL.ImageFile.Parser()
#imageparser.feed(doc.data)
#pimg = imageparser.close()

# Show it in Qt
app = QApplication(sys.argv)

# set up UI
from MainWindow import *
mainWindow = MainWindow('MainWindow.ui')

#imageString = pimg.convert('RGBA').tostring('raw', 'RGBA')
#qimg = QImage(imageString, pimg.size[0], pimg.size[1], QImage.Format_ARGB32)
#pix = QPixmap.fromImage(qimg)
#mainWindow.setPixmap(pix)
mainWindow.setStore(cs)
mainWindow.createPropertyUI()
mainWindow.show()

# Enter Qt application main loop
app.exec_()
sys.exit()
