from PySide import QtCore
from PySide.QtCore import *
from PySide.QtGui import *
#from PySide.QtUiTools import *

import PIL.ImageFile

from QDisplayLabel import *

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()

        # Set title
        self.setWindowTitle('Cinema Desktop')

        # Set up UI
        self._mainWidget = QSplitter(Qt.Horizontal, self)
        self.setCentralWidget(self._mainWidget)

        self._displayWidget = QDisplayLabel(self)
        self._propertiesWidget = QWidget(self)
        self._mainWidget.addWidget(self._displayWidget)
        self._mainWidget.addWidget(self._propertiesWidget)

        layout = QVBoxLayout()
        self._propertiesWidget.setLayout(layout)

        self.createMenus()

        # Connect signals and slots
        self._displayWidget.mousePressSignal.connect(self.onMousePress)
        self._displayWidget.mouseMoveSignal.connect(self.onMouseMove)
        self._displayWidget.mouseReleaseSignal.connect(self.onMouseRelease)

    # Create the menu bars
    def createMenus(self):
        # File menu
        self._exitAction = QAction('E&xit', self, statusTip='Exit the application',
                                   triggered=self.close)
        self._fileToolBar = self.menuBar().addMenu('&File')
        self._fileToolBar.addAction(self._exitAction)

    # Set the store currently being displayed
    def setStore(self, store):
        self._store = store
        self._initializeCurrentQuery()

        # Display the default image
        doc = self._store.find(dict(self._currentQuery)).next()
        self.displayDocument(doc)

    # Initializes image store query.
    def _initializeCurrentQuery(self):
        self._currentQuery = dict()
        dd = self._store.parameter_list

        for name, properties in dd.items():
            self._currentQuery[name] = dd[name]['default']

    # Create property UI
    def createPropertyUI(self):
        dd = self._store.parameter_list
        for name, properties in dd.items():
            textLabel = QLabel(properties['label'], self)
            self._propertiesWidget.layout().addWidget(textLabel)
            slider = QSlider(Qt.Horizontal, self)
            slider.setObjectName(name)
            self._propertiesWidget.layout().addWidget(slider);

            # Configure the slider
            self.configureSlider(slider, properties)

        self._propertiesWidget.layout().addStretch()

    # Convenience function for setting up a slider
    def configureSlider(self, slider, properties):
        default   = properties['default']
        values    = properties['values']
        typeValue = properties['type']
        label     = properties['label']

        slider.setMinimum(0)
        slider.setMaximum(len(values)-1)
        slider.setPageStep(1)

        slider.valueChanged.connect(self.onSliderMoved)

    # Respond to a slider movement
    def onSliderMoved(self):
        propertyName = self.sender().objectName()
        sliderIndex = self.sender().value()
        dd = self._store.parameter_list
        propertyValue = dd[propertyName]['values'][sliderIndex]
        self._currentQuery[propertyName] = propertyValue

        # Retrieve image form data store with the current query. Only
        # care about the first - there should be only one if we have
        # correctly specified all the properties.
        docs = [doc for doc in self._store.find(self._currentQuery)]
        if (len(docs) > 0):
            self.displayDocument(docs[0])
        else:
            self._displayWidget.setPixmap(None)
            self._displayWidget.setText('No Image Found')

    # Get the main widget
    def mainWidget(self):
        return self._mainWidget

    # Given a document, read the data into an image that can be displayed in Qt
    def displayDocument(self, doc):
        #load it into PIL
        imageparser = PIL.ImageFile.Parser()
        imageparser.feed(doc.data)
        pimg = imageparser.close()
        imageString = pimg.convert('RGBA').tostring('raw', 'BGRA')
        qimg = QImage(imageString, pimg.size[0], pimg.size[1], QImage.Format_ARGB32)
        pix = QPixmap.fromImage(qimg)
        self.setPixmap(pix)

    # Set the image displayed from a QPixmap
    def setPixmap(self, pixmap):
        self._displayWidget.setPixmap(pixmap)

    @QtCore.Slot(int,int)
    def onMousePress(self, x, y):
        print "press:", x, y

    @QtCore.Slot(int,int)
    def onMouseMove(self, x, y):
        print "move:", x, y

    @QtCore.Slot(int,int)
    def onMouseRelease(self, x, y):
        print "release:", x, y
