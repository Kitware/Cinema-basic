"""
    Module consisting of explorers and tracks that connect arbitrary VTK
    pipelines to cinema stores.
"""

import explorers
import vtk
from vtk.util import numpy_support
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
        #TODO: choice of writer should be based on store.get_image_type
        self.pw = vtk.vtkDataSetWriter()
        self.pw.SetInputConnection(self.w2i.GetOutputPort())
        self.pw.WriteToOutputStringOn()

    def insert(self, document):
        self.rw.Render()
        self.w2i.Modified()
        self.pw.Write()
        document.data = np.fromstring(self.pw.GetOutputString())
        super(ImageExplorer, self).insert(document)

    def nextDoZ(self):
        self.w2i.SetInputBufferTypeToZBuffer()

    def nextDoRGB(self):
        self.w2i.SetInputBufferTypeToRGB()

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

    def execute(self, doc):
        o = doc.descriptor[self.parameter]
        spec = self.colorlist.getColor(o)
        if spec['type'] == 'rgb':
            self.actor.GetMapper().ScalarVisibilityOff()
            self.actor.GetProperty().SetColor(spec['content'])
        if spec['type'] == 'lut':
            self.actor.GetMapper().ScalarVisibilityOn()
            self.actor.GetMapper().SetLookupTable(spec['content'])
            self.actor.GetMapper().SetScalarMode(spec['field'])
            self.actor.GetMapper().SelectColorArray(spec['arrayname'])

class Depth(explorers.Track):
    """
    A track that facilitates capturing RGB images, or Z depths, or values
    """
    def __init__(self, parameter):
        super(Depth, self).__init__()
        self.parameter = parameter
        self.imageExplorer = None

    def execute(self, doc):
        o = doc.descriptor[self.parameter]
        if o == 'depth':
           self.imageExplorer.nextDoZ()
        else:
           self.imageExplorer.nextDoRGB()
