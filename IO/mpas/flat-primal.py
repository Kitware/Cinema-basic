
###
### Run this script with pvpython so python can find paraview imports.
###
### Purpose:
###
###     This script generates flat earth images of the unstructured
### grid used in the simulation.  I noticed some issues when using the argument
### names that were originally used, those are documented in a long comment
### below.
###
###     Additionally, there is some issue that causes the very first image
### generated to be shifted down and to the left, and the background to be
### filled in with black.
###
### Input:
###
###     - DataExploration/Data/MPAS/data/flat_1_primal/LON_LAT_1LAYER-primal_%d_0.vtu
###
### Output:
###
###     - A cinema dataset at: DataExploration/Output/MPAS/web-generated/flat_1_layer/primal/
###

# -----------------------------------------------------------------------------
# ParaView Python - Path setup
# -----------------------------------------------------------------------------

import sys, os

from paraview.simple import *
#from paraview import data_exploration as wx

from cinema_store import *

# -----------------------------------------------------------------------------

def buildLookupTables(luts, nb_slices):
    for key in luts:
        dataRange = luts[key]["range"]
        luts[key]["lut"] = []
        for i in range(nb_slices):
            if key == 'temperature':
                luts[key]["lut"].append(GetLookupTableForArray( key, 1, VectorComponent=i, RGBPoints=[dataRange[0], 0.231373, 0.298039, 0.752941, (dataRange[0]+dataRange[1])/2, 0.865003, 0.865003, 0.865003, dataRange[1], 0.705882, 0.0156863, 0.14902], VectorMode='Component', NanColor=[0.0, 0.0, 0.0], ColorSpace='Diverging', ScalarRangeInitialized=1.0, LockScalarRange=1))
            else:
                luts[key]["lut"].append(GetLookupTableForArray( key, 1, VectorComponent=i, RGBPoints=[dataRange[0], 0.0, 0.0, 1.0, dataRange[1], 1.0, 0.0, 0.0], VectorMode='Component', NanColor=[0.0, 0.0, 0.0], ColorSpace='HSV', ScalarRangeInitialized=1.0, LockScalarRange=1))

# -----------------------------------------------------------------------------
# Input data to process
# -----------------------------------------------------------------------------

#path_root = '/Users/kitware/Desktop'
path_root = '/Source/CINEMA/genericIO/mpas/'

data_base_path = os.path.join(path_root, 'indata')
output_working_dir = os.path.join(path_root, 'outdata')

globe_file_pattern = 'flat_1_primal/LON_LAT_1LAYER-primal_%d_0.vtu'
#globe_file_times = range(50, 5151, 50) # range(50, 5901, 50)
globe_file_times = range(50, 351, 50)
#globe_file_times = [ 50 ]
globe_filenames = [ os.path.join(data_base_path, (globe_file_pattern % time)) for time in globe_file_times]

# -----------------------------------------------------------------------------
# Rendering configuration
# -----------------------------------------------------------------------------

nb_slices = 10
view_size = [2560, 1200]

view = GetRenderView()
view.ViewSize = view_size
view.Background = [1.0, 1.0, 1.0]
view.OrientationAxesVisibility = 0
view.CenterAxesVisibility = 0

view.CameraParallelScale = 1.55

view.CameraParallelProjection = 1
view.InteractionMode = '2D'
view.CenterOfRotation = [-0.540230751037598, 0.09185272455215454, 0.0]
view.CameraPosition = [0.0, 0.1, 10.0]
view.CameraFocalPoint = [0.0, 0.1, 0.0]

# -----------------------------------------------------------------------------
# Output configuration
# -----------------------------------------------------------------------------

title       = "MPAS - World Ocean - 120km"
description = """
              The following data anaylisis try to simulate the evolution
              of the ocean in term of temperature and salinity distribution accross
              20 years.
              """

#analysis = wx.AnalysisManager(output_working_dir, title, description)

id = 'flat-time'
title = 'Earth slice'
description = '''
              Show the computational mesh with temperature and salinity
              iso-lines for the 40 layers and 120 time steps.
              '''

### The following line (in tandem with the line "fng.update_active_arguments(slice=layer)"),
### causes the UI not to show the layer/slice manipulation widget in the current
### version of Cinema.  It seems that if you use the word "layer" as an argument,
### the UI won't show it.   So I changed "layer" to "slice", and it allows the
### UI to be properly generated.  The same thing seems to go for "field", so I
### had to change that to something else, I chose "colorby".
###
### Note that you can still have the labels in the UI show up however you want,
### you just need to use the file name generator "update_label_arguments" method
### to set the label each time the argument changes.

#analysis.register_analysis(id, title, description, '{time}/{field}/{layer}.jpg', 'parametric-image-stack')
#analysis.register_analysis(id, title, description, '{time}/{colorby}/{slice}.jpg', 'parametric-image-stack')

# -----------------------------------------------------------------------------
# Pipeline configuration
# -----------------------------------------------------------------------------

# Processing pipeline
flat_reader = XMLUnstructuredGridReader(FileName = globe_filenames) # CellArrayStatus = ["salinity", "temperature","density", "pressure","vorticity", "turbulance"]


# Rendering pipeline
flat_rep = Show(flat_reader)
flat_rep.EdgeColor = [0.0, 0.0, 0.0]
flat_rep.Representation = 'Surface With Edges'

luts = {
    "temperature" : {
        "range": [-1.6428141593933105, 28.691740036010742],
        "colorBy": ('CELL_DATA', 'temperature')
    }
    ,
    "salinity": {
        "range": [33.391498565673828, 36.110965728759766],
        "colorBy": ('CELL_DATA', 'salinity')
    }
    #,
    # "density": {
    #     "range": [1019.0, 1045.0],
    #     "colorBy": ('CELL_DATA', 'density')
    # }
}
buildLookupTables(luts, nb_slices)

# -----------------------------------------------------------------------------
# Batch processing
# -----------------------------------------------------------------------------

fng = FileStore(os.path.join(output_working_dir, 'info.json'))
fng.filename_pattern = "{time}_{colorby}_{slice}_test.png"

fng.add_descriptor('time',make_cinema_descriptor_properties('time',globe_file_times))
fng.add_descriptor('colorby',make_cinema_descriptor_properties('colorby',['temperature','salinity'], typechoice='list'))
fng.add_descriptor('slice',make_cinema_descriptor_properties('slice',range(nb_slices)))

#analysis.begin()

for time in range(len(globe_file_times)):
    #fng.update_active_arguments(time=time)
    GetAnimationScene().TimeKeeper.Time = float(time)

    for field in luts:
        #fng.update_active_arguments(colorby=field)
        #fng.update_label_arguments(colorby="Color by")

        flat_rep.ColorArrayName = luts[field]["colorBy"]

        for layer in range(nb_slices):
            # Update pipeline config
            flat_rep.LookupTable = luts[field]["lut"][layer]
            flat_rep.LookupTable.VectorComponent = layer

            #fng.update_active_arguments(slice=layer)
            #fng.update_label_arguments(slice="Layer")

            #make an entry in the database and retrieve the filename
            doc = Document({'time':globe_file_times[time],'colorby':field,'slice':layer})
            #print "WHATS UP", doc, doc.descriptor
            fn = fng.get_filename(doc)
            fng.insert(doc)

            # Triggers the pipeline and then writes the resulting image
            WriteImage(fn)

# Generate metadata
fng.add_metadata({'type':'parametric-image-stack'})
fng.save()


#analysis.end()
