from PySide import QtCore
from PySide.QtCore import *
from PySide.QtGui import *

import PIL.ImageFile

from QDisplayLabel import *
from RenderViewMouseInteractor import *

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

        # Set up render view interactor
        self._mouseInteractor = RenderViewMouseInteractor()

        # Connect signals and slots
        self._displayWidget.mousePressSignal.connect(self._mouseInteractor.onMousePress)
        self._displayWidget.mouseMoveSignal.connect(self._mouseInteractor.onMouseMove)
        self._displayWidget.mouseReleaseSignal.connect(self._mouseInteractor.onMouseRelease)

        # Render any time the mouse is moved
        self._displayWidget.mouseMoveSignal.connect(self.render)

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

        self._mouseInteractor.setPhiValues(store.parameter_list['phi']['values'])
        self._mouseInteractor.setThetaValues(store.parameter_list['theta']['values'])

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

        self.render()

    # Query the image store and display the retrieved image
    def render(self):
        # Set the camera settings if available
        phi   = self._mouseInteractor.getPhi()
        theta = self._mouseInteractor.getTheta()
        self._currentQuery['phi']   = phi
        self._currentQuery['theta'] = theta

        # Retrieve image from data store with the current query. Only
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
