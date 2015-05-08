"""
    Module consisting of explorers and tracks that connect arbitrary VTK
    pipelines to cinema stores.
"""

import explorers
import vtk
from vtk.util import numpy_support
from vtk.numpy_interface import dataset_adapter as dsa
import numpy as np

class ImageExplorer(explorers.Explorer):
    """
    An explorer that connects a VTK program's render window to a store
    and makes it save new images into the store.
    """
    def __init__(self, cinema_store, parameters, engines, rw):
        super(ImageExplorer, self).__init__(cinema_store, parameters, engines)
        self.rw = rw
        self.w2i = vtk.vtkWindowToImageFilter()
        self.w2i.SetInput(self.rw)
        #self.count = 0

    def insert(self, document):
        r = self.rw.GetRenderers().GetFirstRenderer()
        #print r.ComputeVisiblePropBounds()
        #r.ResetCameraClippingRange(-100,100,-100,100,-100,100)
        self.rw.Render()
        self.w2i.Modified()
        self.w2i.Update()
        image = self.w2i.GetOutput()
        #tmpw = vtk.vtkDataSetWriter()
        #tmpw.SetFileName("/tmp/foo/img_" + str(self.count) + ".vtk")
        #self.count = self.count + 1
        #tmpw.SetInputData(image)
        #tmpw.Write()
        npview = dsa.WrapDataObject(image)
        idata = npview.PointData[0]
        ext = image.GetExtent()
        width = ext[1]-ext[0]+1
        height = ext[3]-ext[2]+1
        if image.GetNumberOfScalarComponents() == 1:
            imageslice = np.flipud(idata.reshape(width,height))
        else:
            imageslice = np.flipud(idata.reshape(width,height,image.GetNumberOfScalarComponents()))

        document.data = imageslice
        super(ImageExplorer, self).insert(document)

    def nextDoZ(self):
        self.w2i.SetInputBufferTypeToZBuffer()
        #self.w2i.ReadFrontBufferOff()

    def nextDoColor(self):
        self.w2i.SetInputBufferTypeToRGB()
        #self.w2i.ReadFrontBufferOn()

class Clip(explorers.Track):
    """
    A track that connects clip filters to a scalar valued parameter.
    """

    def __init__(self, argument, clip):
        super(Clip, self).__init__()
        self.argument = argument
        self.clip = clip

    def prepare(self, explorer):
        super(Clip, self).prepare(explorer)
        explorer.cinema_store.add_metadata({'type': 'parametric-image-stack'})

    def execute(self, doc):
        o = doc.descriptor[self.argument]
        self.clip.SetValue(o) #<---- the most important thing!

class Contour(explorers.Track):
    """
    A track that connects clip filters to a scalar valued parameter.
    """

    def __init__(self, argument, filter, method):
        super(Contour, self).__init__()
        self.argument = argument
        self.filter = filter
        self.method = method

    def prepare(self, explorer):
        super(Contour, self).prepare(explorer)
        explorer.cinema_store.add_metadata({'type': 'parametric-image-stack'})

    def execute(self, doc):
        o = doc.descriptor[self.argument]
        getattr(self.filter, self.method)(0, o)

#TODO: add templated classes so we don't end up with a track for each
#vtkAlgorithm

class ColorList():
    """
    A helper that creates a dictionary of color controls for VTK. The Color track takes in
    a color name from the Explorer and looks up into a ColorList to determine exactly what
    needs to be set to apply the color.
    """
    def __init__(self):
        self._dict = {}

    def AddSolidColor(self, name, RGB):
        self._dict[name] = {'type':'rgb','content':RGB}

    def AddLUT(self, name, lut, field, arrayname):
        self._dict[name] = {'type':'lut','content':lut,'field':field,'arrayname':arrayname}

    def AddDepth(self, name):
        self._dict[name] = {'type':'depth'}

    def getColor(self, name):
        return self._dict[name]

class Color(explorers.Track):
    """
    A track that connects a parameter to a choice of surface rendered color maps.
    """
    def __init__(self, parameter, colorlist, actor):
        super(Color, self).__init__()
        self.parameter = parameter
        self.colorlist = colorlist
        self.actor = actor
        self.imageExplorer = None

    def execute(self, doc):
        o = doc.descriptor[self.parameter]
        spec = self.colorlist.getColor(o)
        if spec['type'] == 'rgb':
            if self.imageExplorer:
                self.imageExplorer.nextDoColor()
            self.actor.GetMapper().ScalarVisibilityOff()
            self.actor.GetProperty().SetColor(spec['content'])
        if spec['type'] == 'lut':
            if self.imageExplorer:
                self.imageExplorer.nextDoColor()
            self.actor.GetMapper().ScalarVisibilityOn()
            self.actor.GetMapper().SetLookupTable(spec['content'])
            self.actor.GetMapper().SetScalarMode(spec['field'])
            self.actor.GetMapper().SelectColorArray(spec['arrayname'])
        if spec['type'] == 'depth':
            self.imageExplorer.nextDoZ()

class ActorInLayer(explorers.Layer_Control):

    def showme(self):
        #print self.name, "\tON"
        self.actor.VisibilityOn()

    def hideme(self):
        #print self.name, "\tOFF"
        self.actor.VisibilityOff()

    def __init__(self, parameter, actor):
        super(ActorInLayer, self).__init__(parameter, self.showme, self.hideme)
        self.actor = actor
