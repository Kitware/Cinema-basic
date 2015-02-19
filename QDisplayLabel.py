from PySide.QtCore import *
from PySide.QtGui import *

# Subclass of QLabel that emits signals for mouse events.  Emits
# signals with the mouse position when the mouse is pressed, moved,
# and released.
class QDisplayLabel(QLabel):
    # Qt signals in the PySide style
    mousePressSignal = Signal((int,int,))
    mouseMoveSignal = Signal((int,int,))
    mouseReleaseSignal = Signal((int,int,))

    def __init__(self, parent=None):
        super(QDisplayLabel, self).__init__(parent)

    def mousePressEvent(self, mouseEvent):
        self.mousePressSignal.emit(mouseEvent.x(), mouseEvent.y())

    def mouseMoveEvent(self, mouseEvent):
        self.mouseMoveSignal.emit(mouseEvent.x(), mouseEvent.y())

    def mouseReleaseEvent(self, mouseEvent):
        self.mouseReleaseSignal.emit
