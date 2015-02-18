from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *

import PIL.ImageFile

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()

        # Set title
        self.setWindowTitle('Cinema Desktop')

        # Load basic UI file
        uiLoader = QUiLoader()
        uiFile = QFile('MainWidget.ui')
        uiFile.open(QFile.ReadOnly)
        self._mainWidget = uiLoader.load(uiFile)
        uiFile.close()
        self.setCentralWidget(self._mainWidget)

        self._splitter = self._mainWidget.findChild(QSplitter, 'splitter')
        self._properties = self._splitter.findChild(QWidget, 'propertiesWidget')
        layout = QVBoxLayout()
        self._properties.setLayout(layout)

        self._imageLabel = self._mainWidget.findChild(QLabel, 'imageLabel')

        self.createMenus()

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
        dd = self._store.descriptor_definition

        for name, properties in dd.items():
            self._currentQuery[name] = dd[name]['default']

    # Create property UI
    def createPropertyUI(self):
        dd = self._store.descriptor_definition;
        for name, properties in dd.items():
            textLabel = QLabel(properties['label'], self)
            self._properties.layout().addWidget(textLabel)
            slider = QSlider(Qt.Horizontal, self)
            slider.setObjectName(name)
            self._properties.layout().addWidget(slider);

            # Configure the slider
            self.configureSlider(slider, properties)

        self._properties.layout().addStretch()

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
        dd = self._store.descriptor_definition
        propertyValue = dd[propertyName]['values'][sliderIndex]
        self._currentQuery[propertyName] = propertyValue

        # Retrieve image form data store with the current query. Only
        # care about the first - there should be only one if we have
        # correctly specified all the properties.
        docs = [doc for doc in self._store.find(self._currentQuery)]
        if (len(docs) > 0):
            self.displayDocument(docs[0])
        else:
            self._imageLabel.setPixmap(None)
            self._imageLabel.setText('No Image Found')

    # Get the main widget
    def mainWidget(self):
        return self._mainWidget

    # Given a document, read the data into an image that can be displayed in Qt
    def displayDocument(self, doc):
        #load it into PIL
        imageparser = PIL.ImageFile.Parser()
        imageparser.feed(doc.data)
        pimg = imageparser.close()
        imageString = pimg.convert('RGBA').tostring('raw', 'RGBA')
        qimg = QImage(imageString, pimg.size[0], pimg.size[1], QImage.Format_ARGB32)
        pix = QPixmap.fromImage(qimg)
        self.setPixmap(pix)

    # Set the image displayed from a QPixmap
    def setPixmap(self, pixmap):
        self._imageLabel.setPixmap(pixmap)
        #self._imageLabel.repaint()
