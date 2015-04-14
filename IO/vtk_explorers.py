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

    def insert(self, document):
        self.rw.Render()
        self.w2i.Modified()
        self.w2i.Update()
        image = self.w2i.GetOutput()
        npview = dsa.WrapDataObject(image)
        idata = npview.PointData[0]
        ext = image.GetExtent()
        width = ext[1]-ext[0]+1
        height = ext[3]-ext[2]+1
        imageslice = np.flipud(idata.reshape(width,height,3))
        document.data = imageslice
        super(ImageExplorer, self).insert(document)

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

#TODO: add templated classes so we don't end up with a track for each
#vtkAlgorithm
