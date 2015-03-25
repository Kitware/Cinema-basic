from PySide.QtCore import *
from PySide.QtGui import *

# Subclass of QGraphicsView that emits signals for various  events.  Emits
# signals with the mouse position when the mouse is pressed, moved,
# and released.
class QRenderView(QGraphicsView):
    # Qt signals in the PySide style
    mousePressSignal   = Signal(('QMouseEvent'))
    mouseMoveSignal    = Signal(('QMouseEvent'))
    mouseReleaseSignal = Signal(('QMouseEvent'))
    mouseWheelSignal   = Signal(('QWheelEvent'))

    def __init__(self, parent=None):
        super(QRenderView, self).__init__(parent)

        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        self._pixmapItem = QGraphicsPixmapItem()
        self._pixmapItem.setTransformationMode(Qt.SmoothTransformation)
        self._scene.addItem(self._pixmapItem)

    def mousePressEvent(self, mouseEvent):
        self.mousePressSignal.emit(mouseEvent)

        newMouseEvent =  self._remapMouseButton(mouseEvent)
        super(QRenderView, self).mousePressEvent(newMouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        self.mouseMoveSignal.emit(mouseEvent)

        newMouseEvent =  self._remapMouseButton(mouseEvent)
        super(QRenderView, self).mouseMoveEvent(newMouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        self.mouseReleaseSignal.emit(mouseEvent)

        newMouseEvent =  self._remapMouseButton(mouseEvent)
        super(QRenderView, self).mouseReleaseEvent(newMouseEvent)

    # The default mouse mapping in QSceneWidget is to use left mouse button
    # for panning. I want to match ParaView's mouse bindings, so remap left
    # mouse button presses to the middle button and vice-versa here.
    # Right mouse button is untouched.
    def _remapMouseButton(self, mouseEvent):
        mouseButtonMap = {}
        mouseButtonMap[Qt.MiddleButton] = Qt.LeftButton
        mouseButtonMap[Qt.LeftButton] = Qt.MiddleButton
        mouseButtonMap[Qt.RightButton] = Qt.RightButton

        button = mouseEvent.button()
        buttons = mouseEvent.buttons()
        newButton = mouseEvent.button()
        newButtons = mouseEvent.buttons()

        # Map left button to middle button
        if (int(buttons & Qt.LeftButton)):
            newButtons = (buttons & ~Qt.LeftButton) | Qt.MiddleButton
        if (button == Qt.LeftButton):
            newButton =  Qt.MiddleButton

        # Map middle button to left button

        if (int(buttons & Qt.MiddleButton)):
            newButtons = (buttons & ~Qt.MiddleButton) | Qt.LeftButton
        if (button == Qt.MiddleButton):
            newButton = Qt.LeftButton

        newMouseEvent = QMouseEvent(mouseEvent.type(), mouseEvent.pos(),
                                    newButton, newButtons, mouseEvent.modifiers())
        return newMouseEvent

    def wheelEvent(self, event):
        self.mouseWheelSignal.emit(event)

    def setPixmap(self, pixmap):
        self._pixmapItem.setPixmap(pixmap)
