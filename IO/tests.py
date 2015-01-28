"""
This module tests the generic interface to cinema data.
"""

from cinema_store import *

#import sys
#sys.path.append("/Builds/ParaView/devel/master_debug/lib")
#sys.path.append("/Builds/ParaView/devel/master_debug/lib/site-packages")

def demonstrate_manual_populate(fname="/tmp/demonstrate_manual_populate/info.json"):
    """Demonstrates how to setup a basic cinema store filling the data up with text"""

    thetas = [0,10,20,30,40]
    phis = [0,10,20]

    cs = FileStore(fname)
    cs.filename_pattern = "{theta}/{phi}"
    cs.add_descriptor("theta", make_cinema_descriptor_properties('theta', thetas))
    cs.add_descriptor("phi", make_cinema_descriptor_properties('phi', phis))

    for t in thetas:
        for p in phis:
            doc = Document({'theta':t,'phi':p})
            doc.data = str(doc.descriptor)
            cs.insert(doc)

    cs.save()

def demonstrate_populate(fname="/tmp/demonstrate_populate/info.json"):
    """Demonstrates how to setup a basic cinema store filling the data up with text"""
    import explorers

    cs = FileStore(fname)
    cs.filename_pattern = "{theta}/{phi}"
    cs.add_descriptor("theta", make_cinema_descriptor_properties('theta', [0,10,20,30,40]))
    cs.add_descriptor("phi", make_cinema_descriptor_properties('phi', [0,10,20,30,40]))

    class Track(explorers.Track):
        def execute(self, doc):
            # we save the document's descriptor as the data in
            # this dummy document.
            doc.data = str(doc.descriptor)

    e = explorers.Explorer(cs, ['theta', 'phi'], [Track()])
    e.explore()

def demonstrate_analyze(fname="/tmp/demonstrate_populate/info.json"):
    """
    this demonstrates traversing an existing cinema store and doing some analysis
    (in this case just printing the contents) on each item
    """
    cs = FileStore(fname)
    cs.load()
    print cs.descriptor_definition
    for doc in cs.find({'theta': 20}):
        print doc.descriptor, doc.data

def test_vtk_clip(fname=None):
    import explorers
    import vtk_explorers
    import vtk

    if not fname:
        fname = "info.json"

    # set up some processing task
    s = vtk.vtkSphereSource()

    plane = vtk.vtkPlane()
    plane.SetOrigin(0, 0, 0)
    plane.SetNormal(-1, -1, 0)

    clip = vtk.vtkClipPolyData()
    clip.SetInputConnection(s.GetOutputPort())
    clip.SetClipFunction(plane)
    clip.GenerateClipScalarsOn()
    clip.GenerateClippedOutputOn()
    clip.SetValue(0)

    m = vtk.vtkPolyDataMapper()
    m.SetInputConnection(clip.GetOutputPort())

    rw = vtk.vtkRenderWindow()
    r = vtk.vtkRenderer()
    rw.AddRenderer(r)

    a = vtk.vtkActor()
    a.SetMapper(m)
    r.AddActor(a)

    #make or open a cinema data store to put results in
    cs = FileStore(fname)
    cs.filename_pattern = "{offset}_slice.png"
    cs.add_descriptor("offset", make_cinema_descriptor_properties('offset', [0,.2,.4,.6,.8,1.0]))

    #associate control points wlth parameters of the data store
    g = vtk_explorers.Clip('offset', clip)
    e = vtk_explorers.ImageExplorer(cs, ['offset'], [g], rw)

    #run through all parameter combinations and put data into the store
    e.explore()
    return e


def test_pv_slice(fname):
    import explorers
    import pv_explorers
    import paraview.simple as pv

    # set up some processing task
    view_proxy = pv.CreateRenderView()
    s = pv.Sphere()
    sliceFilt = pv.Slice( SliceType="Plane", Input=s, SliceOffsetValues=[0.0] )
    sliceFilt.SliceType.Normal = [0,1,0]
    sliceRep = pv.Show(sliceFilt)

    #make or open a cinema data store to put results in
    cs = FileStore(fname)
    cs.filename_pattern = "{phi}_{theta}_{offset}_{color}_slice.png"
    cs.add_descriptor("phi", make_cinema_descriptor_properties('phi', [90, 120, 140]))
    cs.add_descriptor("theta", make_cinema_descriptor_properties('theta', [-90,-30,30,90]))
    cs.add_descriptor("offset", make_cinema_descriptor_properties('offset', [-.4,-.2,0,.2,.4]))
    cs.add_descriptor("color", make_cinema_descriptor_properties('color', ['yellow', 'cyan', "purple"], typechoice='list'))

    colorChoice = pv_explorers.ColorList()
    colorChoice.AddSolidColor('yellow', [1, 1, 0])
    colorChoice.AddSolidColor('cyan', [0, 1, 1])
    colorChoice.AddSolidColor('purple', [1, 0, 1])

    #associate control points wlth parameters of the data store
    cam = pv_explorers.Camera([0,0,0], [0,1,0], 10.0, view_proxy) #phi,theta implied
    filt = pv_explorers.Slice("offset", sliceFilt)
    col = pv_explorers.Color("color", colorChoice, sliceRep)

    args = ["phi","theta","offset","color"]
    e = pv_explorers.ImageExplorer(cs, args, [cam, filt, col])
    #run through all parameter combinations and put data into the store
    e.explore()
    del view_proxy
    return e

def test_store():
    fs = FileStore()
    fs.filename_pattern = "{phi}/{theta}/data.raw"
    fs.add_descriptor('theta', {
        "default": 60,
        "type":  "range",
        "values": [60, 90, 120, 150],
        "label": "theta"
        })
    fs.add_descriptor('phi', {
        "default": 180,
        "type":  "range",
        "values": [180],
        "label": "phi"
        })
    doc = Document({"phi": 10}, "Hello World")
    fs.insert(doc)

def test_pv_contour(fname):
    import explorers
    import pv_explorers
    import paraview.simple as pv

    if not fname:
        fname = "info.json"

    # set up some processing task
    view_proxy = pv.CreateRenderView()
    s = pv.Wavelet()
    contour = pv.Contour(Input=s, ContourBy='RTData', ComputeScalars=1 )
    sliceRep = pv.Show(contour)

    #make or open a cinema data store to put results in
    cs = FileStore(fname)
    cs.filename_pattern = "{phi}_{theta}_{contour}_{color}_contour.png"
    cs.add_descriptor("phi", make_cinema_descriptor_properties('phi', [90,120,140]))
    cs.add_descriptor("theta", make_cinema_descriptor_properties('theta', [-90,-30,30,90]))
    cs.add_descriptor("contour", make_cinema_descriptor_properties('contour', [50,100,150,200]))
    cs.add_descriptor("color", make_cinema_descriptor_properties('color', ['white', 'RTData'], typechoice='list'))

    #associate control points wlth parameters of the data store
    cam = pv_explorers.Camera([0,0,0], [0,1,0], 75.0, view_proxy) #phi,theta implied
    filt = pv_explorers.Contour("contour", contour)

    colorChoice = pv_explorers.ColorList()
    colorChoice.AddSolidColor('white', [1,1,1])
    colorChoice.AddLUT('RTData', pv.GetLookupTableForArray( "RTData", 1, RGBPoints=[43.34006881713867, 0.23, 0.299, 0.754, 160.01158714294434, 0.865, 0.865, 0.865, 276.68310546875, 0.706, 0.016, 0.15] )
)
    col = pv_explorers.Color("color", colorChoice, sliceRep)

    args = ["phi","theta","contour","color"]
    e = pv_explorers.ImageExplorer(cs, args, [cam, filt, col])

    #run through all parameter combinations and put data into the store
    e.explore()

    pv.Delete(s)
    pv.Delete(contour)
    pv.Delete(view_proxy)
    return e

def test_NOP(fname):
    import explorers
    import pv_explorers
    import paraview.simple as pv

    if not fname:
        fname = "info.json"

    # set up some processing task
    view_proxy = pv.CreateRenderView()
    s = pv.Wavelet()
    c = pv.Contour(Input=s, ContourBy='RTData', ComputeScalars=1 )
    sliceRep = pv.Show(c)

    #make or open a cinema data store to put results in
    cs = FileStore(fname)
    cs.filename_pattern = "{phi}_{theta}_{contour}_{color}_data.raw"
    cs.add_descriptor("phi", make_cinema_descriptor_properties('phi', [90,120,140]))
    cs.add_descriptor("theta", make_cinema_descriptor_properties('theta', [-90,-30,30,90]))
    cs.add_descriptor("contour", make_cinema_descriptor_properties('contour', [50,100,150,200]))
    cs.add_descriptor("color", make_cinema_descriptor_properties('color', ['white', 'RTData'], typechoice='list'))
    cs.add_descriptor("operation", make_cinema_descriptor_properties('operation',
        ['a', 'b', 'c'], typechoice='list'))

    #associate control points wlth parameters of the data store
    cam = pv_explorers.Camera([0,0,0], [0,1,0], 75.0, view_proxy) #phi,theta implied
    filt = pv_explorers.Contour("contour", c)
    colorChoice = pv_explorers.ColorList()
    colorChoice.AddSolidColor('white', [1,1,1])
    colorChoice.AddLUT('RTData', pv.GetLookupTableForArray( "RTData", 1, RGBPoints=[43.34006881713867, 0.23, 0.299, 0.754, 160.01158714294434, 0.865, 0.865, 0.865, 276.68310546875, 0.706, 0.016, 0.15] )
)
    col = pv_explorers.Color("color", colorChoice, sliceRep)

    class testEE(explorers.Track):
        """
        An explorer to demonstrate not having an entry in the name_pattern.
        Concievable can use these to combine several internal passes together.
        May be useful for composite view type for example.
        """
        import os.path

        def execute(self, doc):
            o = doc.descriptor['operation']
            print doc.descriptor, "OP=", o
            doc.data = o

    op = testEE()

    args = ["phi","theta","contour","color","operation"]
    e = explorers.Explorer(cs, args, [cam, filt, col, op])

    #run through all parameter combinations and put data into the store
    e.explore()
    return e

if __name__ == "__main__":
    test_store()
    demonstrate_populate()
    demonstrate_analyze()
    test_pv_slice("/tmp/pv_slice_data/info.json")
    test_vtk_clip("/tmp/vtk_clip_data/info.json")
    test_pv_contour("/tmp/pv_contour/info.json")
    test_NOP("/tmp/nop/info.json")
