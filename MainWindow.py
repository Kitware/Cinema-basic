from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *

class MainWindow(QMainWindow):
    def __init__(self, uiFileName, parent=None):
        super(MainWindow, self).__init__()
        uiLoader = QUiLoader()
        uiFile = QFile('MainWidget.ui')
        uiFile.open(QFile.ReadOnly)
        self._mainWidget = uiLoader.load(uiFile)
        self.setCentralWidget(self._mainWidget)
        uiFile.close()

        self._imageLabel = self._mainWidget.findChild(QLabel, 'imageLabel')

        self.createMenus()

    def createMenus(self):
        # File menu
        self._exitAction = QAction('E&xit', self, statusTip='Exit the application',
                                   triggered=self.close)
        self._fileToolBar = self.menuBar().addMenu('&File')
        self._fileToolBar.addAction(self._exitAction)

    def mainWidget(self):
        return self._mainWidget

    def setPixmap(self, pixmap):
        self._imageLabel.setPixmap(pixmap)
        
