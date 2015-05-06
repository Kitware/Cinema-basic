#!/usr/bin/python
import time
import sys
from PySide.QtCore import *
from PySide.QtGui import *
import PIL.Image
import numpy as np

sys.path.append("/Source/CINEMA/Cinema-basic/IO")
import cinema_store
cs = cinema_store.FileStore("/tmp/vtk_composite_data/info.json")
cs.load()
aselection = {}
for key, val in cs.parameter_list.iteritems():
    aselection[key] = val[u'default']

aselection['contour'] = 175
aselection['color'] = 'depth'
d1 = cs.find(aselection).next().data
aselection['color'] = 'white'
c1 = cs.find(aselection).next().data

aselection['contour'] = 200
aselection['color'] = 'depth'
d2 = cs.find(aselection).next().data7
aselection['color'] = 'red'
c2 = cs.find(aselection).next().data


# Try numpy
t0 = time.time()
indxarray = np.where(d2<d1)
c1cpy = np.copy(c1)
c1cpy[indxarray[0],indxarray[1],:] = c2[indxarray[0],indxarray[1],:]
t1 = time.time()
print t1-t0
pimg = PIL.Image.fromarray(c1cpy)
pimg.show()
pimg = PIL.Image.fromarray(c1)
pimg.show()

# Try python
t2 = time.time()
m1 = d2 < d1
res = c1
for i in range(0,m1.shape[0]):
    for j in range(0,m1.shape[1]):
        #print d1[i,j], d2[i,j], m1[i,j]
        if d2[i,j] < d1[i,j]:
            res[i,j] = c2[i,j]
t3 = time.time()
print t3-t2

pimg = PIL.Image.fromarray(res)
pimg.show()
