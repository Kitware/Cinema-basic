
###
### This script generates a static image cinema dataset with multiple contours
### on two different variables (salinity and temperature).  It has been altered
### from the same script in the "UpdatedScripts" directory so that it no longer
### requires the paraview data_exploration.py script.  Instead it uses the new
### genericCinemaIO api for iterating over the data parameters.  ParaView is
### still used for the visualization, however.
###
### To run this script, use pvpython and make sure the genericCinemaIO directory
### is in your python path:
###
### PYTHONPATH=</path/to/genericCinemaIO> pvpython contourDatasetMaker.py
###

# -----------------------------------------------------------------------------
# ParaView Python - Path setup
# -----------------------------------------------------------------------------

import sys, os

from paraview.simple import *

from cinema_store import *
import pv_explorers

# -----------------------------------------------------------------------------
# Helper methods
# -----------------------------------------------------------------------------

def buildIsoValues(rangeValues, nbContour):
    inc = float(rangeValues[1]-rangeValues[0]) / float(nbContour)
    values = []
    for i in range(nbContour+1):
        values.append(float(rangeValues[0] + (float(i)*inc) ))
    return values

# -----------------------------------------------------------------------------

def buildLookupTables(luts, nbSurfaces):
    for key in luts:
        dataRange = luts[key]["range"]
        if key == 'temperature':
            luts[key]["lut"] = GetLookupTableForArray( key, 1, RGBPoints=[dataRange[0], 0.231373, 0.298039, 0.752941, (dataRange[0]+dataRange[1])/2, 0.865003, 0.865003, 0.865003, dataRange[1], 0.705882, 0.0156863, 0.14902], VectorMode='Magnitude', NanColor=[0.0, 0.0, 0.0], ColorSpace='Diverging', ScalarRangeInitialized=1.0, LockScalarRange=1)
        else:
            luts[key]["lut"] = GetLookupTableForArray( key, 1, RGBPoints=[dataRange[0], 0.0, 0.0, 1.0, dataRange[1], 1.0, 0.0, 0.0], VectorMode='Magnitude', NanColor=[0.0, 0.0, 0.0], ColorSpace='HSV', ScalarRangeInitialized=1.0, LockScalarRange=1)

        luts[key]["iso-surfaces"] = buildIsoValues(dataRange, nbSurfaces)

# -----------------------------------------------------------------------------
# Input data to process
# -----------------------------------------------------------------------------

start_time = 0
#end_time = 12
end_time = 4

path_root = '/Source/CINEMA/genericIO/mpas/'

data_base_path = os.path.join(path_root, 'indata')
output_working_dir = os.path.join(path_root, 'outdata')

#data_base_path = '/Users/OLeary/MPAS/data/'
#data_base_path = '/media/scott/CINEMA FAT/DataExploration/Data/MPAS/data/'

#output_working_dir = '/media/scott/CINEMA FAT/DataExploration/Output/MPAS/mpas-contour-data'
#output_working_dir = '/home/scott/Documents/genericCinemaIO/Output/MPAS/mpas-contour-data'

globe_file_pattern = 'xyz_n_primal/X_Y_Z_NLAYER-primal_%d_0.vtu'
#globe_file_times = range(50, 5151, 50) # range(50, 5901, 50)
globe_file_times = range(50, 351, 50) # range(50, 5901, 50)
globe_filenames = [ data_base_path + "/" + (globe_file_pattern % time) for time in globe_file_times]

number_of_contour_surface = 10

# -----------------------------------------------------------------------------
# Rendering configuration
# -----------------------------------------------------------------------------

view_size = [600, 600]
angle_steps = [15, 30]
distance = 25000000
rotation_axis = [0.0, 0.0, 1.0]
center_of_rotation = [0.0, 0.0, 0.0]

#view = GetRenderView()
view = CreateRenderView()
view.ViewSize = view_size
view.Background = [1.0, 1.0, 1.0]
view.OrientationAxesVisibility = 0
view.CenterAxesVisibility = 0

# -----------------------------------------------------------------------------
# Output configuration
# -----------------------------------------------------------------------------

title       = "MPAS - World Ocean - 120km"
description = """
              The following data anaylisis try to simulate the evolution
              of the ocean in term of temperature and salinity distribution accross
              20 years.
              """

id = 'contour-time' + str(start_time)
title = 'Earth iso-contours'
description = '''
              Show the computational mesh with temperature and salinity
              iso-lines for the 40 layers and 120 time steps.
              '''

luts = {
    "temperature" : {
        "range": [-1.6428141593933105, 28.691740036010742],
        #"nbLines": 30,
        "isoLinesArray": "salinity",
        "colorBy": ('POINT_DATA', 'temperature')
    },
    "salinity": {
        "range": [33.391498565673828, 36.110965728759766],
        #"nbLines": 10,
        "isoLinesArray": "temperature",
        "colorBy": ('POINT_DATA', 'salinity')
    }
}

phis = [ 120, 140, 170 ]
thetas = [ 30, 90 ]

# -----------------------------------------------------------------------------
# Pipeline configuration
# -----------------------------------------------------------------------------

# Processing pipeline
globe_reader = XMLUnstructuredGridReader(FileName = globe_filenames, CellArrayStatus = ["salinity", "temperature"])
extract_valid_data = Threshold(Input=globe_reader, Scalars = ['CELLS', 'temperature'], ThresholdRange= [-1000.0, 1000.0])
data_to_points = CellDatatoPointData(Input=extract_valid_data)
surface_contour = Contour(Input=data_to_points, PointMergeMethod="Uniform Binning", ContourBy=['POINTS', 'temperature'], ComputeNormals=0, Isosurfaces=[0])

# Rendering pipeline
surface_contour_rep = Show(surface_contour)

buildLookupTables(luts, number_of_contour_surface)

cam = pv_explorers.Camera(center_of_rotation, rotation_axis, distance, view)
fng = FileStore(os.path.join(output_working_dir, 'info.json'))
fng.filename_pattern = "{time}/{surfaceContour}/{contourIdx}/{theta}/{phi}/image.png"

fng.add_descriptor(
    'time',
    make_cinema_descriptor_properties('time',range(start_time, end_time)))
fng.add_descriptor(
    'surfaceContour',
    make_cinema_descriptor_properties('surfaceContour',['temperature','salinity'],
                                      typechoice='list'))
fng.add_descriptor(
    'contourIdx',
    make_cinema_descriptor_properties('isosurfaces',range(1,number_of_contour_surface+1)))
fng.add_descriptor(
    'theta',
    make_cinema_descriptor_properties('theta',thetas))
fng.add_descriptor(
    'phi',
    make_cinema_descriptor_properties('phis',phis))

# -----------------------------------------------------------------------------
# Batch processing
# -----------------------------------------------------------------------------

for time in range(start_time, end_time):
    #fng.update_active_arguments(time=time)
    GetAnimationScene().TimeKeeper.Time = float(time)
    UpdatePipeline(time)

    for field in luts:
        #fng.update_active_arguments(surfaceContour=field)

        # Update pipeline config
        surface_contour.ContourBy          = field
        surface_contour_rep.LookupTable    = luts[field]["lut"]
        surface_contour_rep.ColorArrayName = luts[field]["colorBy"]

        for contourIdx in range(1, len(luts[field]["iso-surfaces"])):
            value = luts[field]["iso-surfaces"][contourIdx]
            surface_contour.Isosurfaces = [value]
            #fng.update_active_arguments(contourIdx=contourIdx)

            for theta in thetas:
                #fng.update_active_arguments(theta=theta)
                for phi in phis:
                    #fng.update_active_arguments(phi=phi)

                    doc = Document({'time':time,
                                    'surfaceContour':field,
                                    'contourIdx':contourIdx,
                                    'theta':theta, 'phi':phi})
                    cam.execute(doc)

                    fn = fng.get_filename(doc)
                    fng.insert(doc)

                    # Triggers the pipeline and then writes the resulting image
                    WriteImage(fn)

# Generate metadata
fng.add_metadata({'type':'parametric-image-stack'})
fng.save()
