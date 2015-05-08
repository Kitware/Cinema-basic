"""
This module tests the generic interface to cinema data.
"""

from cinema_store import *

import sys
sys.path.append("/Builds/ParaView/devel/master_debug/lib")
sys.path.append("/Builds/ParaView/devel/master_debug/lib/site-packages")

def demonstrate_manual_populate(fname="/tmp/demonstrate_manual_populate/info.json"):
    """Demonstrates how to setup a basic cinema store filling the data up with text"""

    thetas = [0,10,20,30,40]
    phis = [0,10,20]

    cs = FileStore(fname)
    cs.filename_pattern = "{theta}/{phi}"
    cs.add_parameter("theta", make_parameter('theta', thetas))
    cs.add_parameter("phi", make_parameter('phi', phis))

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
    cs.add_parameter("theta", make_parameter('theta', [0,10,20,30,40]))
    cs.add_parameter("phi", make_parameter('phi', [0,10,20,30,40]))

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
    print cs.parameter_list
    for doc in cs.find({'theta': 20}):
        print doc.descriptor, doc.data

def test_SFS(fname="/tmp/cinemaSFS/info.json"):
    if not fname:
        fname = "info.json"
    fs = SingleFileStore(fname)
    fs.add_parameter('theta', {
        "default": 60,
        "type":  "range",
        "values": [60, 90, 120, 150],
        "label": "theta"
        })
    fs.add_parameter('phi', {
        "default": 60,
        "type":  "range",
        "values": [60, 90, 120, 150],
        "label": "phi"
        })
    #print fs._get_numslices()
    print "INSERT DOC 60,150"
    doc = Document({"phi": 60, "theta":150}, "Hello World")
    fs.insert(doc)
    print doc.data
    print "INSERT DOC 60,120"
    doc = Document({"phi": 60, "theta":120}, "World of WarCraft")
    fs.insert(doc)
    print doc.data
    print "INSERT DOC 150,150"
    doc = Document({"phi": 150, "theta":150}, "Craft Macaroni and Chese")
    fs.insert(doc)
    print doc.data
    print "GET 60,150"
    print fs.find({"phi":60, "theta":150}).next().data
    print "GET 60,90"
    print fs.find({"phi":60, "theta":90}).next().data
    print "GET 60,*"
    for x in fs.find({"phi":60}):
        print x.data
    print "GET *,150"
    for x in fs.find({"theta":150}):
        print x.data

def test_parameter_bifurcation():
    import explorers

    params = ["time","layer","slice_field","back_color"]

    cs = Store()
    cs.add_parameter("time", make_parameter("time", [0,1,2]))
    cs.add_parameter("layer", make_parameter("layer", ['outline','slice','background']))
    cs.add_parameter("slice_field", make_parameter("slice_field", ['solid_red', 'temperature', 'pressure']))
    cs.add_parameter("back_color", make_parameter("back_color", ['grey0', 'grey49']))

    class printDescriptor(explorers.Explorer):
        def execute(self, desc):
            print desc

    print "NO DEPENDENCIES"
    e = printDescriptor(cs, params, [])
    e.explore()

    print "NO DEPENDENCIES AND FIXED TIME"
    e.explore({'time':3})

    print "WITH DEPENDENCIES"
    cs.assign_parameter_dependence('slice_field', 'layer', ['slice'])
    cs.assign_parameter_dependence('back_color', 'layer', ['background'])
    e.explore()

    print "WITH DEPENDENCIES AND FIXED TIME"
    e.explore({'time':3})

def test_layers_and_fields():
    import explorers

    params = ["time", "layer", "component"]

    cs = Store()
    cs.add_parameter("time", make_parameter("time", ["0"]))
    cs.add_layer("layer", make_parameter("layer", ['outline','slice','background']))
    #cs.add_sublayer("sublayer", make_parameter("sublayer", ['0','1']), "layer", "slice") #TODO, explorer doesn't traverse deps of deps right
    cs.add_field("component", make_parameter("component", ['z','RGB']), "layer", 'slice')

    def showme(self):
        print "NOW YOU SEE ", self.name
    def hideme(self):
        print "NOW YOU DONT SEE ", self.name

    outline_control = explorers.Layer_Control("outline", showme, hideme)
    slice_control = explorers.Layer_Control("slice", showme, hideme)
    background_control = explorers.Layer_Control("background", showme, hideme)

    #slice_control1 = explorers.Layer_Control("0", showme, hideme)
    #slice_control2 = explorers.Layer_Control("1", showme, hideme)

    field_control1 = explorers.Layer_Control("z", showme, hideme)
    field_control2 = explorers.Layer_Control("RGB", showme, hideme)

    layertrack = explorers.Layer("layer", [outline_control, slice_control, background_control])
    #sublayertrack = explorers.Layer("sublayer", [slice_control1, slice_control2])
    fieldtrack = explorers.Layer("component", [field_control1,field_control2])

    e = explorers.Explorer(cs, params, [layertrack, fieldtrack])
    e.explore()

def test_vtk_layers(fname=None):
    import explorers
    import vtk_explorers
    import vtk

    if not fname:
        fname = "info.json"

    # set up some processing task
    s = vtk.vtkRTAnalyticSource()
    s.SetWholeExtent(-50,50,-50,50,-50,50)

    rw = vtk.vtkRenderWindow()
    r = vtk.vtkRenderer()
    rw.AddRenderer(r)

    cactors = []
    isos = []
    for x in range(50,250,50):
        isos.append(x)
        cf = vtk.vtkContourFilter()
        cf.SetInputConnection(s.GetOutputPort())
        cf.SetInputArrayToProcess(0,0,0, "vtkDataObject::FIELD_ASSOCIATION_POINTS", "RTData")
        cf.SetNumberOfContours(1)
        cf.SetValue(0, x)
        m = vtk.vtkPolyDataMapper()
        m.SetInputConnection(cf.GetOutputPort())
        a = vtk.vtkActor()
        a.SetMapper(m)
        r.AddActor(a)
        cactors.append(a)

    rw.Render()
    r.ResetCamera()

    #make or open a cinema data store to put results in
    cs = FileStore(fname)
    cs.filename_pattern = "{contour}_{color}.png"
    contour_strs = [str(i) for i in isos]
    param = make_parameter('contour', contour_strs)
    cs.add_layer("contour", param)
    cs.add_field("color", make_parameter('color', ['white','red','depth']), "contour", contour_strs)

    vcontrols = []
    for i in range(0,len(cactors)):
        vcontrol = vtk_explorers.ActorInLayer(str(isos[i]), cactors[i])
        vcontrols.append(vcontrol)
    layertrack = explorers.Layer("contour", [v for v in vcontrols])

    colorChoice = vtk_explorers.ColorList()
    colorChoice.AddSolidColor('white', [1,1,1])
    colorChoice.AddSolidColor('red', [1,0,0])
    colorChoice.AddDepth('depth')

    #associate control points wlth parameters of the data store
    c = vtk_explorers.Color('color', colorChoice, a)
    e = vtk_explorers.ImageExplorer(cs, ['contour', 'color'], [layertrack, c], rw)
    c.imageExplorer = e
    e.explore()

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
    cs.add_parameter("offset", make_parameter('offset', [0,.2,.4,.6,.8,1.0]))

    #associate control points wlth parameters of the data store
    g = vtk_explorers.Clip('offset', clip)
    e = vtk_explorers.ImageExplorer(cs, ['offset'], [g], rw)

    #run through all parameter combinations and put data into the store
    e.explore()
    return e

def test_vtk_clipSFS(fname=None):
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
    cs = SingleFileStore(fname)
    cs.add_parameter("offset", make_parameter('offset', [-.4,-.2,0,.2,.4,.6]))
    #print cs._get_numslices()

    #associate control points wlth parameters of the data store
    g = vtk_explorers.Clip('offset', clip)
    e = vtk_explorers.ImageExplorer(cs, ['offset'], [g], rw)

    #run through all parameter combinations and put data into the store
    e.explore()

    #for x in cs.find({"offset":0.2}):
    #    for pixel in x.data:
    #        print pixel

    return e

def test_vtk_contour(fname=None):
    import explorers
    import vtk_explorers
    import vtk

    if not fname:
        fname = "info.json"

    # set up some processing task
    s = vtk.vtkRTAnalyticSource()
    s.SetWholeExtent(-50,50,-50,50,-50,50)
    cf = vtk.vtkContourFilter()
    cf.SetInputConnection(s.GetOutputPort())
    cf.SetInputArrayToProcess(0,0,0, "vtkDataObject::FIELD_ASSOCIATION_POINTS", "RTData")
    cf.SetNumberOfContours(1)
    cf.SetValue(0, 100)

    m = vtk.vtkPolyDataMapper()
    m.SetInputConnection(cf.GetOutputPort())

    rw = vtk.vtkRenderWindow()
    r = vtk.vtkRenderer()
    rw.AddRenderer(r)

    a = vtk.vtkActor()
    a.SetMapper(m)
    r.AddActor(a)

    rw.Render()
    r.ResetCamera()

    #make or open a cinema data store to put results in
    cs = FileStore(fname)
    cs.filename_pattern = "{contour}_{color}.png"
    cs.add_parameter("contour", make_parameter('contour', [0,25,50,75,100,125,150,175,200,225,250]))
    cs.add_parameter("color", make_parameter('color', ['white','red']))

    colorChoice = vtk_explorers.ColorList()
    colorChoice.AddSolidColor('white', [1,1,1])
    colorChoice.AddSolidColor('red', [1,0,0])

    #associate control points wlth parameters of the data store
    g = vtk_explorers.Contour('contour', cf, 'SetValue')
    c = vtk_explorers.Color('color', colorChoice, a)
    e = vtk_explorers.ImageExplorer(cs, ['contour','color'], [g,c], rw)

    #run through all parameter combinations and put data into the store
    e.explore()
    return e

def test_vtk_composite(fname=None):
    import explorers
    import vtk_explorers
    import vtk

    if not fname:
        fname = "info.json"

    # set up some processing task
    s = vtk.vtkRTAnalyticSource()
    s.SetWholeExtent(-50,50,-50,50,-50,50)
    cf = vtk.vtkContourFilter()
    cf.SetInputConnection(s.GetOutputPort())
    cf.SetInputArrayToProcess(0,0,0, "vtkDataObject::FIELD_ASSOCIATION_POINTS", "RTData")
    cf.SetNumberOfContours(1)
    cf.SetValue(0, 100)

    m = vtk.vtkPolyDataMapper()
    m.SetInputConnection(cf.GetOutputPort())

    rw = vtk.vtkRenderWindow()
    r = vtk.vtkRenderer()
    rw.AddRenderer(r)

    a = vtk.vtkActor()
    a.SetMapper(m)
    r.AddActor(a)

    rw.Render()
    r.ResetCamera()

    #make or open a cinema data store to put results in
    cs = FileStore(fname)
    cs.filename_pattern = "{contour}_{color}.png"
    cs.add_parameter("contour", make_parameter('contour', [50,75,100,125,150,175,200,225]))
    cs.add_parameter("color", make_parameter('color', ['white','red','depth']))

    colorChoice = vtk_explorers.ColorList()
    colorChoice.AddSolidColor('white', [1,1,1])
    colorChoice.AddSolidColor('red', [1,0,0])
    colorChoice.AddDepth('depth')

    #associate control points wlth parameters of the data store
    g = vtk_explorers.Contour('contour', cf, 'SetValue')
    c = vtk_explorers.Color('color', colorChoice, a)
    e = vtk_explorers.ImageExplorer(cs, ['contour','color'], [g,c], rw)
    c.imageExplorer = e

    #run through all parameter combinations and put data into the store
    e.explore()
    return e

def test_read_vtk_composite(fname=None):
    import explorers
    import vtk_explorers
    import vtk

    if not fname:
        fname = "info.json"

    #make or open a cinema data store to put results in
    cs = FileStore(fname)
    cs.load()
    print cs.parameter_list
    #for doc in cs.find({'color': 'white'}):
    for doc in cs.find({'color': 'depth'}):
        print doc.descriptor, doc.data

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
    cs.add_parameter("phi", make_parameter('phi', [90, 120, 140]))
    cs.add_parameter("theta", make_parameter('theta', [-90,-30,30,90]))
    cs.add_parameter("offset", make_parameter('offset', [-.4,-.2,0,.2,.4]))
    cs.add_parameter("color", make_parameter('color', ['yellow', 'cyan', "purple"], typechoice='list'))

    colorChoice = pv_explorers.ColorList()
    colorChoice.AddSolidColor('yellow', [1, 1, 0])
    colorChoice.AddSolidColor('cyan', [0, 1, 1])
    colorChoice.AddSolidColor('purple', [1, 0, 1])

    #associate control points wlth parameters of the data store
    cam = pv_explorers.Camera([0,0,0], [0,1,0], 10.0, view_proxy) #phi,theta implied
    filt = pv_explorers.Slice("offset", sliceFilt)
    col = pv_explorers.Color("color", colorChoice, sliceRep)

    params = ["phi","theta","offset","color"]
    e = pv_explorers.ImageExplorer(cs, params, [cam, filt, col], view_proxy)
    #run through all parameter combinations and put data into the store
    e.explore()
    del view_proxy
    return e

def test_pv_sliceSFS(fname):
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
    cs = SingleFileStore(fname)
    cs.add_parameter("phi", make_parameter('phi', [90, 120, 140]))
    cs.add_parameter("theta", make_parameter('theta', [-90,-30,30,90]))
    cs.add_parameter("offset", make_parameter('offset', [-.4,-.2,0,.2,.4]))
    cs.add_parameter("color", make_parameter('color', ['yellow', 'cyan', "purple"], typechoice='list'))

    colorChoice = pv_explorers.ColorList()
    colorChoice.AddSolidColor('yellow', [1, 1, 0])
    colorChoice.AddSolidColor('cyan', [0, 1, 1])
    colorChoice.AddSolidColor('purple', [1, 0, 1])

    #associate control points wlth parameters of the data store
    cam = pv_explorers.Camera([0,0,0], [0,1,0], 10.0, view_proxy) #phi,theta implied
    filt = pv_explorers.Slice("offset", sliceFilt)
    col = pv_explorers.Color("color", colorChoice, sliceRep)

    params = ["phi","theta","offset","color"]
    e = pv_explorers.ImageExplorer(cs, params, [cam, filt, col], view_proxy)
    #run through all parameter combinations and put data into the store
    e.explore()
    del view_proxy

    return e

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
    cs.add_parameter("phi", make_parameter('phi', [90,120,140]))
    cs.add_parameter("theta", make_parameter('theta', [-90,-30,30,90]))
    cs.add_parameter("contour", make_parameter('contour', [50,100,150,200]))
    cs.add_parameter("color", make_parameter('color', ['white', 'RTData'], typechoice='list'))

    #associate control points wlth parameters of the data store
    cam = pv_explorers.Camera([0,0,0], [0,1,0], 75.0, view_proxy) #phi,theta implied
    filt = pv_explorers.Contour("contour", contour)

    colorChoice = pv_explorers.ColorList()
    colorChoice.AddSolidColor('white', [1,1,1])
    colorChoice.AddLUT('RTData', pv.GetLookupTableForArray( "RTData", 1, RGBPoints=[43.34006881713867, 0.23, 0.299, 0.754, 160.01158714294434, 0.865, 0.865, 0.865, 276.68310546875, 0.706, 0.016, 0.15] )
)
    col = pv_explorers.Color("color", colorChoice, sliceRep)

    params = ["phi","theta","contour","color"]
    e = pv_explorers.ImageExplorer(cs, params, [cam, filt, col], view_proxy)

    #run through all parameter combinations and put data into the store
    e.explore()

    pv.Delete(s)
    pv.Delete(contour)
    pv.Delete(view_proxy)
    return e

def test_pv_composite(fname):
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
    cs.add_parameter("phi", make_parameter('phi', [90,120,140]))
    cs.add_parameter("theta", make_parameter('theta', [-90,-30,30,90]))
    cs.add_parameter("contour", make_parameter('contour', [50,100,150,200], typechoice='option'))
    cs.add_parameter("color", make_parameter('color', ['white', 'RTData', 'depth'], typechoice='list'))

    #associate control points wlth parameters of the data store
    cam = pv_explorers.Camera([0,0,0], [0,1,0], 75.0, view_proxy) #phi,theta implied
    filt = pv_explorers.Contour("contour", contour)

    colorChoice = pv_explorers.ColorList()
    colorChoice.AddSolidColor('white', [1,1,1])
    colorChoice.AddLUT('RTData', pv.GetLookupTableForArray
                       ( "RTData", 1,
                         RGBPoints=[43.34006881713867, 0.23, 0.299, 0.754, 160.01158714294434, 0.865, 0.865, 0.865, 276.68310546875, 0.706, 0.016, 0.15] ))
    colorChoice.AddDepth('depth')

    col = pv_explorers.Color("color", colorChoice, sliceRep)

    params = ["phi","theta","contour","color"]
    e = pv_explorers.ImageExplorer(cs, params, [cam, filt, col], view_proxy)

    #run through all parameter combinations and put data into the store
    e.explore()

    pv.Delete(s)
    pv.Delete(contour)
    pv.Delete(view_proxy)
    return e

if __name__ == "__main__":
    #demonstrate_manual_populate() #doesn't work with text data
    #demonstrate_populate() #doesn't work with text data
    #demonstrate_analyze() #doesn't work with text data
    #test_SFS() #doesn't work with text data

    #test_parameter_bifurcation()
    test_layers_and_fields()
    test_vtk_layers("/tmp/vlaf/info.json")
    #test_vtk_clip("/tmp/vtk_clip_data/info.json")
    #test_vtk_clipSFS("/tmp/vtk_clip_dataSFS/info.json")
    #test_vtk_contour("/tmp/vtk_contour_data/info.json")
    #test_vtk_composite("/tmp/vtk_composite_data/info.json")
    #test_read_vtk_composite("/tmp/vtk_composite_data/info.json")
    #test_pv_slice("/tmp/pv_slice_data/info.json")
    #test_pv_sliceSFS("/tmp/pv_slice_data/info.json")
    #test_pv_contour("/tmp/pv_contour/info.json")
    #test_pv_composite("/tmp/pv_composite/info.json")
    print "DONE"
