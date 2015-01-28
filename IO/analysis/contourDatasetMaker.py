
# -----------------------------------------------------------------------------
# ParaView Python - Path setup
# -----------------------------------------------------------------------------

import sys

from paraview.simple import *
from paraview import data_exploration as wx

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
end_time = 12

#data_base_path = '/Users/OLeary/MPAS/data/'
data_base_path = '/media/scott/CINEMA FAT/DataExploration/Data/MPAS/data/'

globe_file_pattern = 'xyz_n_primal/X_Y_Z_NLAYER-primal_%d_0.vtu'
globe_file_times = range(50, 5151, 50) # range(50, 5901, 50)
globe_filenames = [ data_base_path + (globe_file_pattern % time) for time in globe_file_times]

number_of_contour_surface = 10

# -----------------------------------------------------------------------------
# Rendering configuration
# -----------------------------------------------------------------------------

view_size = [600, 600]
angle_steps = [15, 30]
distance = 25000000
rotation_axis = [0.0, 0.0, 1.0]
center_of_rotation = [0.0, 0.0, 0.0]

view = GetRenderView()
view.ViewSize = view_size
view.Background = [1.0, 1.0, 1.0]
view.OrientationAxesVisibility = 0
view.CenterAxesVisibility = 0

# -----------------------------------------------------------------------------
# Output configuration
# -----------------------------------------------------------------------------

#output_working_dir = '/Users/kitware/Desktop/MPAS/web-generated/contour3d'
output_working_dir = '/home/scott/Documents/cinemaDemo/simpleCinemaWebGL/mpas-data'
title       = "MPAS - World Ocean - 120km"
description = """
              The following data anaylisis try to simulate the evolution
              of the ocean in term of temperature and salinity distribution accross
              20 years.
              """

analysis = wx.AnalysisManager(output_working_dir, title, description)

id = 'contour-time' + str(start_time)
title = 'Earth iso-contours'
description = '''
              Show the computational mesh with temperature and salinity
              iso-lines for the 40 layers and 120 time steps.
              '''
analysis.register_analysis(id, title, description, '{time}/{surfaceContour}/{contourIdx}/{theta}_{phi}.jpg', wx.ThreeSixtyImageStackExporter.get_data_type())
fng = analysis.get_file_name_generator(id)
exporter = wx.ThreeSixtyImageStackExporter(fng, view, center_of_rotation, distance, rotation_axis, angle_steps)
exporter.set_analysis(analysis)

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
buildLookupTables(luts, number_of_contour_surface)

# -----------------------------------------------------------------------------
# Batch processing
# -----------------------------------------------------------------------------

analysis.begin()

for time in range(start_time, end_time):
	GetAnimationScene().TimeKeeper.Time = float(time)
	for field in luts:
		fng.update_active_arguments(surfaceContour=field)
		fng.update_label_arguments(surfaceContour="Surface contour")

		# Update pipeline config
		surface_contour.ContourBy          = field
		surface_contour_rep.LookupTable    = luts[field]["lut"]
		surface_contour_rep.ColorArrayName = luts[field]["colorBy"]

		for contourIdx in range(1, len(luts[field]["iso-surfaces"])):
			value = luts[field]["iso-surfaces"][contourIdx]
			surface_contour.Isosurfaces = [value]

			fng.update_active_arguments(contourIdx=contourIdx)

			exporter.UpdatePipeline(time)

analysis.end()
