from PySide import QtCore

import math

class RenderViewMouseInteractor():
    def __init__(self):
        self._xy = (0, 0)

        # Current camera settings
        self._phi   = 0
        self._theta = 0

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

    @QtCore.Slot(int,int)
    def onMousePress(self, x, y):
        self._xy = (x, y)

    @QtCore.Slot(int,int)
    def onMouseMove(self, x, y):
        dx = x - self._xy[0]
        dy = y - self._xy[1]

        dphi   = dx / self.xPhiRatio
        dtheta = dy / self.yThetaRatio
        phi_sign   = 1 if dphi   > 0 else -1
        theta_sign = 1 if dtheta > 0 else -1

        # If the phi angles are not evenly spaced, this logic won't work.
        # Should look at angle above and below this one to make the increment decision.
        if (math.fabs(dphi) > self._stepPhi):
            self._phi   = self._incrementAngle(self._phi, phi_sign, self._phiValues)
            self._xy = (x, y)

        # The same comment for the phi update holds for the theta update.
        if (math.fabs(dtheta) > self._stepTheta):
            self._theta = self._incrementAngle(self._theta, theta_sign, self._thetaValues)
            self._xy = (x, y)

    @QtCore.Slot(int,int)
    def onMouseRelease(self, x, y):
        self._xy = None

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
