from PySide import QtCore
from PySide.QtCore import *
from PySide.QtGui import *

import PIL.ImageFile
import numpy

from QRenderView import *
from RenderViewMouseInteractor import *

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()

        # Set title
        self.setWindowTitle('Cinema Desktop')

        # Set up UI
        self._mainWidget = QSplitter(Qt.Horizontal, self)
        self.setCentralWidget(self._mainWidget)

        self._displayWidget = QRenderView(self)
        self._displayWidget.setRenderHints(QPainter.SmoothPixmapTransform)
        self._displayWidget.setAlignment(Qt.AlignCenter)
        self._displayWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._parametersWidget = QWidget(self)
        self._parametersWidget.setMinimumSize(QSize(200, 100))
        self._parametersWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self._mainWidget.addWidget(self._displayWidget)
        self._mainWidget.addWidget(self._parametersWidget)

        layout = QVBoxLayout()
        self._parametersWidget.setLayout(layout)

        self.createMenus()

        # Set up render view interactor
        self._mouseInteractor = RenderViewMouseInteractor()

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
            dw = self._displayWidget
            dw.mousePressSignal.disconnect(self._initializeCamera)
            dw.mousePressSignal.disconnect(self._mouseInteractor.onMousePress)
            dw.mouseMoveSignal.disconnect(self._mouseInteractor.onMouseMove)
            dw.mouseReleaseSignal.disconnect(self._mouseInteractor.onMouseRelease)
            dw.mouseWheelSignal.disconnect(self._mouseInteractor.onMouseWheel)

            # Update camera phi-theta if mouse is dragged
            self._displayWidget.mouseMoveSignal.disconnect(self._updateCamera)

            # Update camera if mouse wheel is moved
            self._displayWidget.mouseWheelSignal.disconnect(self._updateCamera)
        except:
            # No big deal if we can't disconnect
            pass

    # Connect mouse signals
    def _connectMouseSignals(self):
        dw = self._displayWidget
        dw.mousePressSignal.connect(self._initializeCamera)
        dw.mousePressSignal.connect(self._mouseInteractor.onMousePress)
        dw.mouseMoveSignal.connect(self._mouseInteractor.onMouseMove)
        dw.mouseReleaseSignal.connect(self._mouseInteractor.onMouseRelease)
        dw.mouseWheelSignal.connect(self._mouseInteractor.onMouseWheel)

        # Update camera phi-theta if mouse is dragged
        self._displayWidget.mouseMoveSignal.connect(self._updateCamera)

        # Update camera if mouse wheel is moved
        self._displayWidget.mouseWheelSignal.connect(self._updateCamera)

    # Initializes image store query.
    def _initializeCurrentQuery(self):
        self._currentQuery = dict()
        dd = self._store.parameter_list

        for name, properties in dd.items():
            self._currentQuery[name] = dd[name]['default']

    # Create property UI
    def _createParameterUI(self):
        keys = sorted(self._store.parameter_list)
        for name in keys:
            properties = self._store.parameter_list[name]
            if len(properties['values']) == 1:
                #don't have widget if no choice possible
                continue
            labelValueWidget = QWidget(self)
            labelValueWidget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
            labelValueWidget.setLayout(QHBoxLayout())
            labelValueWidget.layout().setContentsMargins(0, 0, 0, 0)
            self._parametersWidget.layout().addWidget(labelValueWidget)

            textLabel = QLabel(properties['label'], self)
            labelValueWidget.layout().addWidget(textLabel)

            valueLabel = QLabel('0', self)
            valueLabel.setAlignment(Qt.AlignRight)
            valueLabel.setObjectName(name + "ValueLabel")
            labelValueWidget.layout().addWidget(valueLabel)

            sliderControlsWidget = QWidget(self)
            sliderControlsWidget.setSizePolicy(QSizePolicy.MinimumExpanding,
                                               QSizePolicy.Fixed)
            sliderControlsWidget.setLayout(QHBoxLayout())
            sliderControlsWidget.layout().setContentsMargins(0, 0, 0, 0)
            #sliderControlsWidget.setContentsMargins(0, 0, 0, 0)
            self._parametersWidget.layout().addWidget(sliderControlsWidget)

            flat = False
            width = 25

            skipBackwardIcon = self.style().standardIcon(QStyle.SP_MediaSkipBackward)
            skipBackwardButton = QPushButton(skipBackwardIcon, '', self)
            skipBackwardButton.setObjectName("SkipBackwardButton." + name)
            skipBackwardButton.setFlat(flat)
            skipBackwardButton.setMaximumWidth(width)
            skipBackwardButton.clicked.connect(self.onSkipBackward)
            sliderControlsWidget.layout().addWidget(skipBackwardButton)

            seekBackwardIcon = self.style().standardIcon(QStyle.SP_MediaSeekBackward)
            seekBackwardButton = QPushButton(seekBackwardIcon, '', self)
            seekBackwardButton.setObjectName("SeekBackwardButton." + name)
            seekBackwardButton.setFlat(flat)
            seekBackwardButton.setMaximumWidth(width)
            seekBackwardButton.clicked.connect(self.onSeekBackward)
            sliderControlsWidget.layout().addWidget(seekBackwardButton)

            slider = QSlider(Qt.Horizontal, self)
            slider.setObjectName(name)
            sliderControlsWidget.layout().addWidget(slider);

            seekForwardIcon = self.style().standardIcon(QStyle.SP_MediaSeekForward)
            seekForwardButton = QPushButton(seekForwardIcon, '', self)
            seekForwardButton.setObjectName("SeekForwardButton." + name)
            seekForwardButton.setFlat(flat)
            seekForwardButton.setMaximumWidth(width)
            seekForwardButton.clicked.connect(self.onSeekForward)
            sliderControlsWidget.layout().addWidget(seekForwardButton)

            skipForwardIcon = self.style().standardIcon(QStyle.SP_MediaSkipForward)
            skipForwardButton = QPushButton(skipForwardIcon, '', self)
            skipForwardButton.setObjectName("SkipForwardButton." + name)
            skipForwardButton.setFlat(flat)
            skipForwardButton.setMaximumWidth(width)
            skipForwardButton.clicked.connect(self.onSkipForward)
            sliderControlsWidget.layout().addWidget(skipForwardButton)

            playIcon = self.style().standardIcon(QStyle.SP_MediaPlay)
            playButton = QPushButton(playIcon, '', self)
            playButton.setObjectName("PlayButton." + name)
            playButton.setFlat(flat)
            playButton.setMaximumWidth(width)
            playButton.clicked.connect(self.onPlay)
            sliderControlsWidget.layout().addWidget(playButton)

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

    # Back up slider all the way to the left
    def onSkipBackward(self):
        parameterName = self.sender().objectName().replace("SkipBackwardButton.", "")
        slider = self._parametersWidget.findChild(QSlider, parameterName)
        slider.setValue(0)

    # Back up slider one step to the left
    def onSeekBackward(self):
        parameterName = self.sender().objectName().replace("SeekBackwardButton.", "")
        slider = self._parametersWidget.findChild(QSlider, parameterName)
        slider.setValue(0 if slider.value() == 0 else slider.value() - 1)

    # Forward slider one step to the right
    def onSeekForward(self):
        parameterName = self.sender().objectName().replace("SeekForwardButton.", "")
        slider = self._parametersWidget.findChild(QSlider, parameterName)
        maximum = slider.maximum()
        slider.setValue(maximum if slider.value() == maximum else slider.value() + 1)

    # Forward the slider all the way to the right
    def onSkipForward(self):
        parameterName = self.sender().objectName().replace("SkipForwardButton.", "")
        slider = self._parametersWidget.findChild(QSlider, parameterName)
        slider.setValue(slider.maximum())

    # Play forward through the parameters
    def onPlay(self):
        parameterName = self.sender().objectName().replace("PlayButton.", "")
        timer = QTimer(self)
        timer.setObjectName("Timer." + parameterName)
        timer.setInterval(200)
        timer.timeout.connect(self.onPlayTimer)
        timer.start()

    def onPlayTimer(self):
        parameterName = self.sender().objectName().replace("Timer.", "")

        slider = self._parametersWidget.findChild(QSlider, parameterName)
        maximum = slider.maximum()
        if (slider.value() == slider.maximum()):
            self.sender().stop()
        else:
            slider.setValue(maximum if slider.value() == maximum else slider.value() + 1)

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
    def _updateCamera(self):
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

        scale = self._mouseInteractor.getScale()
        self._displayWidget.resetTransform()
        self._displayWidget.scale(scale, scale)

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

    # Get the main widget
    def mainWidget(self):
        return self._mainWidget

    # Given a document, read the data into an image that can be displayed in Qt
    def displayDocument(self, doc):

        if doc.data == None:
            return

        pimg = PIL.Image.fromarray(doc.data)
        imageString = pimg.tostring('raw', 'RGB')
        qimg = QImage(imageString, pimg.size[0], pimg.size[1], QImage.Format_RGB888)

        pix = QPixmap.fromImage(qimg)

        # Try to resize the display widget
        self._displayWidget.sizeHint = pix.size

        self._displayWidget.setPixmap(pix)
