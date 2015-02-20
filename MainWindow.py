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
        self._displayWidget.setAlignment(Qt.AlignCenter)
        self._displayWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._displayWidget.setText("None")
        self._parametersWidget = QWidget(self)
        parametersWidgetSize = QSize(200, 100)
        self._parametersWidget.setMinimumSize(parametersWidgetSize)
        self._parametersWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self._mainWidget.addWidget(self._displayWidget)
        self._mainWidget.addWidget(self._parametersWidget)

        layout = QVBoxLayout()
        self._parametersWidget.setLayout(layout)

        self.createMenus()

        # Set up render view interactor
        self._mouseInteractor = RenderViewMouseInteractor()

        # Connect window resize event
        self._displayWidget.resizeEventSignal.connect(self.render)

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

        # Disconnect all mouse signals in case the store has no phi or theta values
        self._disconnectMouseSignals()

        if ('phi' in store.parameter_list):
            self._mouseInteractor.setPhiValues(store.parameter_list['phi']['values'])

        if ('theta' in store.parameter_list):
            self._mouseInteractor.setThetaValues(store.parameter_list['theta']['values'])

        if ('phi' in store.parameter_list or 'theta' in store.parameter_list):
            self._connectMouseSignals()

        # Display the default image
        doc = self._store.find(dict(self._currentQuery)).next()
        self.displayDocument(doc)

        self._createParameterUI()

    # Disconnect mouse signals
    def _disconnectMouseSignals(self):
        try:
            self._displayWidget.mousePressSignal.disconnect(self._initializeCamera)
            self._displayWidget.mousePressSignal.disconnect(self._mouseInteractor.onMousePress)
            self._displayWidget.mouseMoveSignal.disconnect(self._mouseInteractor.onMouseMove)
            self._displayWidget.mouseReleaseSignal.disconnect(self._mouseInteractor.onMouseRelease)

            # Update camera phi-theta if mouse is dragged
            self._displayWidget.mouseMoveSignal.disconnect(self._updateCameraAngle)
        except:
            # No big deal if we can't disconnect
            pass

    # Connect mouse signals
    def _connectMouseSignals(self):
        self._displayWidget.mousePressSignal.connect(self._initializeCamera)
        self._displayWidget.mousePressSignal.connect(self._mouseInteractor.onMousePress)
        self._displayWidget.mouseMoveSignal.connect(self._mouseInteractor.onMouseMove)
        self._displayWidget.mouseReleaseSignal.connect(self._mouseInteractor.onMouseRelease)

        # Update camera phi-theta if mouse is dragged
        self._displayWidget.mouseMoveSignal.connect(self._updateCameraAngle)

    # Initializes image store query.
    def _initializeCurrentQuery(self):
        self._currentQuery = dict()
        dd = self._store.parameter_list

        for name, properties in dd.items():
            self._currentQuery[name] = dd[name]['default']

    # Create property UI
    def _createParameterUI(self):
        dd = self._store.parameter_list
        for name, properties in dd.items():
            labelValueWidget = QWidget(self)
            labelValueWidget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
            labelValueWidget.setLayout(QHBoxLayout())
            self._parametersWidget.layout().addWidget(labelValueWidget)

            textLabel = QLabel(properties['label'], self)
            labelValueWidget.layout().addWidget(textLabel)

            valueLabel = QLabel('0', self)
            valueLabel.setAlignment(Qt.AlignRight)
            valueLabel.setObjectName(name + "ValueLabel")
            labelValueWidget.layout().addWidget(valueLabel)

            slider = QSlider(Qt.Horizontal, self)
            slider.setObjectName(name)
            self._parametersWidget.layout().addWidget(slider);

            # Configure the slider
            self.configureSlider(slider, properties)
            self._updateSlider(properties['label'], properties['default'])

        self._parametersWidget.layout().addStretch()

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
        parameterName = self.sender().objectName()
        sliderIndex = self.sender().value()
        pl = self._store.parameter_list
        parameterValue = pl[parameterName]['values'][sliderIndex]
        self._currentQuery[parameterName] = parameterValue

        # Update value label
        valueLabel = self._parametersWidget.findChild(QLabel, parameterName + "ValueLabel")
        valueLabel.setText(self._formatText(parameterValue))

        self.render()

    # Format string from number
    def _formatText(self, value):
        try:
            intValue = int(value)
            return '{0}'.format(intValue)
        except:
            pass

        try:
            floatValue = float(value)
            return '{0}'.format(floatValue)
        except:
            pass

        # String
        return value

    # Update slider from value
    def _updateSlider(self, parameterName, value):
        pl = self._store.parameter_list
        index = pl[parameterName]['values'].index(value)
        slider = self._parametersWidget.findChild(QSlider, parameterName)
        slider.setValue(index)

    # Initialize the angles for the camera
    def _initializeCamera(self):
        self._mouseInteractor.setPhi(self._currentQuery['phi'])
        self._mouseInteractor.setTheta(self._currentQuery['theta'])

    # Update the camera angle
    def _updateCameraAngle(self):
        # Set the camera settings if available
        phi   = self._mouseInteractor.getPhi()
        theta = self._mouseInteractor.getTheta()

        if ('phi' in self._currentQuery):
            self._currentQuery['phi']   = phi

        if ('theta' in self._currentQuery):
            self._currentQuery['theta'] = theta

        # Update the sliders for phi and theta
        self._updateSlider('phi', phi)
        self._updateSlider('theta', theta)

        self.render()

    # Query the image store and display the retrieved image
    def render(self):
        # Retrieve image from data store with the current query. Only
        # care about the first - there should be only one if we have
        # correctly specified all the properties.
        docs = [doc for doc in self._store.find(self._currentQuery)]
        if (len(docs) > 0):
            self.displayDocument(docs[0])
        else:
            self._displayWidget.setPixmap(None)
            self._displayWidget.setAlignment(Qt.AlignCenter)
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

        # Try to resize the display widget
        self._displayWidget.sizeHint = pix.size

        # Resize pixmap to fill the screen
        size = self._displayWidget.size()
        scaledPixmap = pix.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.setPixmap(scaledPixmap)

    # Set the image displayed from a QPixmap
    def setPixmap(self, pixmap):
        self._displayWidget.setPixmap(pixmap)
