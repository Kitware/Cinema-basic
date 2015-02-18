
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

aselection = {}

# Show it in Qt
app = QApplication(sys.argv)

# set up UI
from MainWindow import *
mainWindow = MainWindow('MainWindow.ui')

mainWindow.setStore(cs)
mainWindow.createPropertyUI()
mainWindow.show()

# Enter Qt application main loop
app.exec_()
sys.exit()
