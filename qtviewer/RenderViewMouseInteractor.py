from PySide import QtCore
from PySide.QtCore import *

import math

class RenderViewMouseInteractor():
    NoneState   = 0
    RotateState = 1
    PanState    = 2
    ZoomState   = 3

    def __init__(self):
        self._state = self.NoneState
        self._xy = (0, 0)

        # Current camera settings
        self._phi   = 0
        self._theta = 0
        self._scale = 1

        # xPhiRatio How many pixels must be dragged in x per degree change in phi.
        self.xPhiRatio   = 1 #?

        # yThetaRatio How many pixels must be dragged in y per degree change in theta.
        self.yThetaRatio = 1 #?

        self._stepPhi   = 30
        self._stepTheta = 30

    def setPhiValues(self, phiValues):
        self._phiValues = phiValues

        # Warning - this assumes an even angle spacing through the phiValues array.
        self._stepPhi = phiValues[1] - phiValues[0]

    def setThetaValues(self, thetaValues):
        self._thetaValues = thetaValues

        # Warning - this assumes an even angle spacing through the thetaValues array.
        self._stepTheta = thetaValues[1] - thetaValues[0]

    def setPhi(self, phi):
        self._phi = phi

    def setTheta(self, theta):
        self._theta = theta

    def getPhi(self):
        return self._phi

    def getTheta(self):
        return self._theta

    def getScale(self):
        return self._scale

    @QtCore.Slot('QMouseEvent')
    def onMousePress(self, mouseEvent):
        if (mouseEvent.button() == Qt.LeftButton):
            self._xy = (mouseEvent.x(), mouseEvent.y())
            self._state = self.RotateState
        elif (mouseEvent.button() == Qt.RightButton):
            self._state = self.ZoomState
            self._xy = (mouseEvent.x(), mouseEvent.y())

    @QtCore.Slot('QMouseEvent')
    def onMouseMove(self, mouseEvent):
        if (self._xy == None):
            return

        dx = mouseEvent.x() - self._xy[0]
        dy = mouseEvent.y() - self._xy[1]

        if (self._state == self.RotateState):
            dphi   = dx / self.xPhiRatio
            dtheta = dy / self.yThetaRatio
            phi_sign   = 1 if dphi   > 0 else -1
            theta_sign = 1 if dtheta > 0 else -1

            # If the phi angles are not evenly spaced, this logic won't work.
            # Should look at angle above and below this one to make the increment decision.
            if (math.fabs(dphi) > self._stepPhi):
                self._phi   = self._incrementAngle(self._phi, phi_sign, self._phiValues)
                self._xy = (mouseEvent.x(), mouseEvent.y())

            # The same comment for the phi update holds for the theta update.
            if (math.fabs(dtheta) > self._stepTheta):
                self._theta = self._incrementAngle(self._theta, theta_sign, self._thetaValues)
                self._xy = (mouseEvent.x(), mouseEvent.y())

        elif (self._state == self.ZoomState):
            scaleFactor = 1.01
            if (dy < 0):
                for i in range(-dy):
                    self._scale = self._scale * scaleFactor
            else:
                for i in range(dy):
                    self._scale = self._scale * (1.0 / scaleFactor)
            self._xy = (mouseEvent.x(), mouseEvent.y())


    @QtCore.Slot('QMouseEvent')
    def onMouseRelease(self, mouseEvent):
        self._xy = None

    @QtCore.Slot('QWheelEvent')
    def onMouseWheel(self, event):
        scaleFactor = 1.01
        # reduce the size of delta for more controllable zooming
        dy = event.delta() / 20
        if (dy > 0):
            for i in range(dy):
                self._scale = self._scale * scaleFactor
        else:
            for i in range(-dy):
                self._scale = self._scale * (1.0 / scaleFactor)


    # Increment angle to be either the next or previous angle in the angle list
    def _incrementAngle(self, angle, sign, angles):
        # Find index of angle in array of angles
        index = angles.index(angle)
        index = index + sign * 1
        if (index < 0):
            index = len(angles)-1
        if (index >= len(angles)):
            index = 0

        return angles[index]
