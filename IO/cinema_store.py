"""
    Module defining classes and methods for managing cinema data storage.
"""

import sys
import json
import os.path
import re
import itertools
import weakref
import PIL.ImageFile
import numpy as np
from vtk.numpy_interface import dataset_adapter as dsa
import vtk

class Document(object):
    """
    This refers to a document in the cinema data storage. A document is
    uniquely identified by a 'descriptor'. A descriptor is a dictionary
    with key-value pairs, where key is a parameter name and value is the
    value for that particular parameter.
    TODO:
    A document can have arbitrary data (as 'data') and meta-data (as
    'attributes') associated with it. At the moment we are assuming
    stored images and are ignoring the attributes.
    """
    def __init__(self, descriptor, data=None):
        self.__descriptor = descriptor
        self.__data = data
        self.__attributes = None

    @property
    def descriptor(self):
        """A document descriptor is a unique
        identifier for the document. It is a dict with key value pairs. The
        descriptor cannot be changed once the document has been instantiated."""
        return self.__descriptor

    @property
    def data(self):
        """Data associated with the document."""
        return self.__data

    @data.setter
    def data(self, val):
        self.__data = val

    @property
    def attributes(self):
        """Attributes are arbitrary meta-data associated with the document.
        If no attributes are present, it is set to None. When present,
        attributes are a dict with arbitrary meta-data relevant to the application.
        """
        return self.__attributes

    @attributes.setter
    def attributes(self, attrs):
        self.__attributes = attrs

class Store(object):
    """
    API for cinema stores. A store is a collection of Documents,
    with API to add, find, and access them. This class is an abstract class
    defining the API and storage independent logic. Storage specific
    subclasses handle the 'database' access.

    The design of cinema store is based on the following principles:

    The store comprises of documents (Document instances). Each document has a
    unique set of parameters, aka a "descriptor" associated with it. This
    can be thought of as the 'unique key' in database terminology.

    One defines the parameters (contents of the descriptor) for documents
    on the store itself. The set of them is is referred to as 'parameter_list'.
    One uses 'add_parameter()' calls to add new parameter definitions for a new
    store instance.

    Users insert documents in the store using 'insert'. One can find
    document(s) using 'find' which returns a generator (or cursor) allow users
    to iterate over all match documents.
    """

    def __init__(self):
        self.__metadata = None
        self.__parameter_list = {}
        self.__loaded = False
        self.__parameter_associations = {}

    @property
    def parameter_list(self):
        """
        The parameter list is the set of variables and their values that the
        documents in the store vary over. """
        return self.__parameter_list

    def _set_parameter_list(self, val):
        """For use by subclasses alone"""
        self.__parameter_list = val

    def add_parameter(self, name, properties):
        """Add a parameter.
        :param name: Name for the parameter.
        :param properties: Keyword arguments can be used to associate miscellaneous
        meta-data with this parameter.
        """
        #if self.__loaded:
        #    raise RuntimeError("Updating parameters after loading/creating a store is not supported.")
        # TODO: Err, except when it is, in the important case of adding new time steps to a collection.
        # I postulate it is always OK to add safely to outermost parameter (loop).
        properties = self.validate_parameter(name, properties)
        self.__parameter_list[name] = properties

    def get_parameter(self, name):
        return self.__parameter_list[name]

    def get_complete_descriptor(self, partial_desc):
        """
        Convenience method that expands an incomplete list of parameters into
        the full set using default values for the missing variables.
        """
        full_desc = dict()
        for name, properties in self.parameter_list.items():
            if properties.has_key("default"):
                full_desc[name] = properties["default"]
        full_desc.update(partial_desc)
        return full_desc

    def validate_parameter(self, name, properties):
        """Validates a new parameter and return updated parameter properties.
        Subclasses should override this as needed.
        """
        return properties

    @property
    def parameter_associations(self):
        return self.__parameter_associations

    def _set_parameter_associations(self, val):
        """For use by subclasses alone"""
        self.__parameter_associations = val

    @property
    def metadata(self):
        """
        Auxiliary data about the store itself. An example is hints that help the
        viewer app know how to interpret this particular store.
        """
        return self.__metadata

    @metadata.setter
    def metadata(self, val):
        self.__metadata = val

    def add_metadata(self, keyval):
        if not self.__metadata:
            self.__metadata = {}
        self.__metadata.update(keyval)

    def create(self):
        """
        Creates an empty store.
        Subclasses must extend this.
        """
        assert not self.__loaded
        self.__loaded = True

    def load(self):
        """
        Loads contents on the store (but not the documents).
        Subclasses must extend this.
        """
        assert not self.__loaded
        self.__loaded = True

    def find(self, q=None):
        """
        Return iterator to all documents that match query q.
        Should support empty query or direct values queries e.g.
        for doc in store.find({'phi': 0}):
            print doc.data
        for doc in store.find({'phi': 0, 'theta': 100}):
            print doc.data
        """
        raise RuntimeError("Subclasses must define this method")

    def insert(self, document):
        """
        Inserts a new document.
        Subclasses must extend this.
        """
        if not self.__loaded:
            self.create()

    def assign_parameter_dependence(self, dep_param, param, on_values):
        """
        mark a particular parameter as being explorable only for a subset
        of the possible values of another.

        For example given parameter 'appendage type' which might have
        value 'foot' or 'flipper', a dependent parameter might be 'shoe type'
        which only makes sense for 'feet'. More to the point we use this
        for 'layers' and 'fields' in composite rendering of objects in a scene
        and the color settings that each object is allowed to take.
        """
        self.__parameter_associations.setdefault(dep_param, {}).update(
        {param: on_values})


class FileStore(Store):
    """Implementation of a store based on named files and directories."""

    def __init__(self, dbfilename=None):
        super(FileStore, self).__init__()
        self.__filename_pattern = None
        self.__dbfilename = dbfilename if dbfilename \
                else os.path.join(os.getcwd(), "info.json")

    def create(self):
        """creates a new file store"""
        super(FileStore, self).create()
        self.save()

    def load(self):
        """loads an existing filestore"""
        super(FileStore, self).load()
        with open(self.__dbfilename, mode="rb") as file:
            info_json = json.load(file)
            #for legacy reasons, the parameters are called
            #arguments" in the files
            self._set_parameter_list(info_json['arguments'])
            self.metadata = info_json['metadata']
            self.filename_pattern = info_json['name_pattern']
            self._set_parameter_associations(info_json['associations'])

    def save(self):
        """ writes out a modified file store """
        info_json = dict(
                arguments = self.parameter_list,
                name_pattern = self.filename_pattern,
                metadata = self.metadata,
                associations = self.parameter_associations
                )
        dirname = os.path.dirname(self.__dbfilename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(self.__dbfilename, mode="wb") as file:
            json.dump(info_json, file)

    @property
    def filename_pattern(self):
        """
        Files corresponding to Documents are arranged on disk
        according the the directory and filename structure described
        by the filename_pattern. The format is a regular expression
        consisting of parameter names enclosed in '{' and '}' and
        separated by spacers. "/" spacer characters produce sub
        directories.
        """
        return self.__filename_pattern

    @filename_pattern.setter
    def filename_pattern(self, val):
        self.__filename_pattern = val
        #Now set up to be able to convert filenames into descriptors automatically
        #break filename pattern up into an ordered list of parameter names
        cp = re.sub("{[^}]+}", "(\S+)", self.__filename_pattern) #convert to a RE
        #extract names
        keyargs = re.match(cp, self.__filename_pattern).groups()
        self.__fn_keys = list(x[1:-1] for x in keyargs) #strip "{" and "}"
        #make an RE to get the values from full pathname, igoring leading directories
        self.__fn_vals_RE = '(\S+)/'+cp

    def get_image_type(self):
        return self.filename_pattern[self.filename_pattern.rfind("."):]

    def insert(self, document):
        super(FileStore, self).insert(document)
        fname = self._get_filename(document)
        dirname = os.path.dirname(fname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if not document.data == None:
            imageslice = document.data
            pimg = PIL.Image.fromarray(imageslice)
            pimg.save(fname)

    def _get_filename(self, document):
        desc = self.get_complete_descriptor(document.descriptor)
        suffix = self.filename_pattern.format(**desc)
        if hasattr(document, 'extension'):
            suffix = suffix[:suffix.rfind(".")] + document.extension
        dirname = os.path.dirname(self.__dbfilename)
        return os.path.join(dirname, suffix)

    def _load_image(self, doc_file):
        #with open(doc_file + ".__data__", "r") as file:
        #    info_json = json.load(file)
        try:
            with open(doc_file, "r") as file:
                temp = file.read()
                imageparser = PIL.ImageFile.Parser()
                imageparser.feed(temp)
                temp = imageparser.close()
                data = np.array(temp.getdata(), np.uint8).reshape(temp.size[1], temp.size[0], 3)
        except IOError:
            data = None
        # convert filename into a list of values
        vals = re.match(self.__fn_vals_RE, doc_file).groups()[1:]
        descriptor = dict(zip(self.__fn_keys, vals))
        doc = Document(descriptor, data)
        doc.attributes = None
        return doc

    def find(self, q=None):
        q = q if q else dict()
        p = q

        # build a file name match pattern based on the query.
        for name, properties in self.parameter_list.items():
            if not name in q:
                p[name] = "*"
        dirname = os.path.dirname(self.__dbfilename)
        match_pattern = os.path.join(dirname, self.filename_pattern.format(**p))

        from fnmatch import fnmatch
        from os import walk
        for root, dirs, files in walk(os.path.dirname(self.__dbfilename)):
            for fn in files:
                doc_file = os.path.join(root, fn)
                #if file.find("__data__") == -1 and fnmatch(doc_file, match_pattern):
                #    yield self.load_document(doc_file)
                if fnmatch(doc_file, match_pattern):
                    yield self._load_image(doc_file)

class SingleFileStore(Store):
    """Implementation of a store based on a single volume file (image stack)."""

    def __init__(self, dbfilename=None):
        super(SingleFileStore, self).__init__()
        self.__filename_pattern = None
        self.__dbfilename = dbfilename if dbfilename \
                else os.path.join(os.getcwd(), "info.json")
        self._volume = None
        self._needWrite = False

    def __del__(self):
        if self._needWrite:
            vw = vtk.vtkXMLImageDataWriter()
            vw.SetFileName(self._vol_file)
            vw.SetInputData(self._volume)
            vw.Write()

    def create(self):
        """creates a new file store"""
        super(SingleFileStore, self).create()
        self.save()

    def load(self):
        """loads an existing filestore"""
        super(SingleFileStore, self).load()
        with open(self.__dbfilename, mode="rb") as file:
            info_json = json.load(file)
            self._set_parameter_list(info_json['arguments'])
            self.metadata = info_json['metadata']

    def save(self):
        """ writes out a modified file store """
        info_json = dict(
                arguments = self.parameter_list,
                metadata = self.metadata
                )
        dirname = os.path.dirname(self.__dbfilename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(self.__dbfilename, mode="wb") as file:
            json.dump(info_json, file)

    def _get_numslices(self):
        slices = 0
        for name in sorted(self.parameter_list.keys()):
            numvals = len(self.get_parameter(name)['values'])
            if slices == 0:
                slices = numvals
            else:
                slices = slices * numvals
        return slices

    def compute_sliceindex(self, descriptor):
        #find position of descriptor within the set of slices
        #TODO: algorithm is dumb, but consisent with find (which is also dumb)
        args = []
        values = []
        ordered = sorted(self.parameter_list.keys())
        for name in ordered:
            vals = self.get_parameter(name)['values']
            args.append(name)
            values.append(vals)
        index = 0
        for element in itertools.product(*values):
            desc = dict(itertools.izip(args, element))
            fail = False
            for k,v in descriptor.items():
                if desc[k] != v:
                    fail = True
            if not fail:
                return index
            index = index + 1

    def get_sliceindex(self, document):
        desc = self.get_complete_descriptor(document.descriptor)
        index = self.compute_sliceindex(desc)
        return index

    def _insertslice(self, vol_file, index, document):
        volume = self._volume
        width = document.data.shape[0]
        height = document.data.shape[1]
        if not volume:
            if not os.path.exists(vol_file):
                slices = self._get_numslices()
                volume = vtk.vtkImageData()
                volume.SetExtent(0, width-1, 0, height-1, 0, slices-1)
                volume.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 3)
                vw = vtk.vtkXMLImageDataWriter()
                vw.SetFileName(vol_file)
                vw.SetInputData(volume)
                vw.Write()
            else:
                vr = vtk.vtkXMLImageDataReader()
                vr.SetFileName(vol_file)
                vr.Update()
                volume = vr.GetOutput()
            self._volume = volume
            self._vol_file = vol_file

        imageslice = document.data
        imageslice = imageslice.reshape(width*height, 3)

        image = dsa.WrapDataObject(volume)
        oid = volume.ComputePointId([0,0,index])
        nparray = image.PointData[0]
        nparray[oid:oid+(width*height)] = imageslice

        self._needWrite = True

    def insert(self, document):
        super(SingleFileStore, self).insert(document)

        index = self.get_sliceindex(document)

        if not document.data == None:
            dirname = os.path.dirname(self.__dbfilename)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            vol_file = os.path.join(dirname, "cinema.vti")
            self._insertslice(vol_file, index, document)

    def _load_slice(self, q, index):

        if not self._volume:
            dirname = os.path.dirname(self.__dbfilename)
            vol_file = os.path.join(dirname, "cinema.vti")
            vr = vtk.vtkXMLImageDataReader()
            vr.SetFileName(vol_file)
            vr.Update()
            volume = vr.GetOutput()
            self._volume = volume
            self._vol_file = vol_file
        else:
            volume = self._volume

        ext = volume.GetExtent()
        width = ext[1]-ext[0]
        height = ext[3]-ext[2]

        image = dsa.WrapDataObject(volume)

        oid = volume.ComputePointId([0, 0, index])
        nparray = image.PointData[0]
        imageslice = np.reshape(nparray[oid:oid+width*height], (width,height,3))

        descriptor = self.get_complete_descriptor(q)
        doc = Document(descriptor, imageslice)
        doc.attributes = None
        return doc

    def find(self, q=None):
        #TODO: algorithm is dumb, but consisent with find (which is also dumb)
        q = q if q else dict()
        args = []
        values = []
        ordered = sorted(self.parameter_list.keys())
        for name in ordered:
            vals = self.get_parameter(name)['values']
            args.append(name)
            values.append(vals)

        index = 0
        for element in itertools.product(*values):
            desc = dict(itertools.izip(args, element))
            fail = False
            for k,v in q.items():
                if desc[k] != v:
                    fail = True
            if not fail:
                yield self._load_slice(q, index)
            index = index + 1


def make_parameter(name, values, **kwargs):
    default = kwargs['default'] if 'default' in kwargs else values[0]
    typechoice = kwargs['typechoice'] if 'typechoice' in kwargs else 'range'
    label = kwargs['label'] if 'label' in kwargs else name

    types = ['list','range','option']
    if not typechoice in types:
        raise RuntimeError, "Invalid typechoice, must be on of %s" % str(types)
    if not default in values:
        raise RuntimeError, "Invalid default, must be one of %s" % str(values)
    properties = dict()
    properties['type'] = typechoice
    properties['label'] = label
    properties['values'] = values
    properties['default'] = default
    return properties
