import explorers
import vtk
from vtk.util import numpy_support

class Clip(explorers.Track):

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

class ImageExplorer(explorers.Explorer):

    def __init__(self, cinema_store, arguments, engines, rw):
        super(ImageExplorer, self).__init__(cinema_store, arguments, engines)
        self.rw = rw
        self.w2i = vtk.vtkWindowToImageFilter()
        self.w2i.SetInput(self.rw)
        self.pw = vtk.vtkPNGWriter()
        self.pw.SetInputConnection(self.w2i.GetOutputPort())
        self.pw.WriteToMemoryOn()

    def insert(self, document):
        self.rw.Render()
        self.w2i.Modified()
        self.pw.Write()
        document.data = numpy_support.vtk_to_numpy(self.pw.GetResult())
        super(ImageExplorer, self).insert(document)
