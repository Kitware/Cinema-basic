import cinema_store
import itertools

class Explorer(object):
    """
    Middleman that connects an arbitrary producing codes to the CinemaStore.
    The purpose of this class is to run through the parameter sets, and tell a
    set of tracks (in order) to do something with the parameter values
    it cares about.
    """

    def __init__(self,
        cinema_store,
        parameters, #these are the things that this explorer is responsible for and their ranges
        tracks #the things we pass off values to in order to do the work
        ):

        self.__cinema_store = cinema_store
        self.parameters = parameters
        self.tracks = tracks

    @property
    def cinema_store(self):
        return self.__cinema_store

    def list_parameters(self):
        """
        parameters is an ordered list of parameters that the Explorer varies over
        """
        return self.parameters

    def prepare(self):
        """ Give tracks a chance to get ready for a run """
        if self.tracks:
            for e in self.tracks:
                res = e.prepare(self)

    def execute(self, desc):
        # Create the document/data product for this sample.
        doc = cinema_store.Document(desc)
        for e in self.tracks:
            e.execute(doc)
        self.insert(doc)

    def explore(self, fixedargs=None):
        """
        Explore the problem space to populate the store.
        fixed arguments are the parameters that we want to hold constant in the exploration
        """
        self.prepare()

        dependencies = self.cinema_store.parameter_associations
        #print "DEPS", dependencies

        param_names = self.list_parameters()
        params = []
        values = []
        dep_params = []
        for name in param_names:
            vals = self.cinema_store.get_parameter(name)['values']
            if fixedargs and name in fixedargs:
                continue

            if name in dependencies:
                dep_params.append(name)
            else:
                params.append(name)
                values.append(vals)
        #print "PARAMS", params
        #print "VALUES", values
        #print "DEP PARAMS", dep_params

        for element in itertools.product(*values):
            descriptor = dict(itertools.izip(params, element))

            if fixedargs != None:
                descriptor.update(fixedargs)

            #print "DESC", descriptor

            ok_params = []
            ok_vals = []
            for possible in dep_params:
                #print "TEST", possible, dependencies, dependencies[possible]
                ok = True
                for dep, oks in dependencies[possible].iteritems():
                    #print "DEP", dep, "OKS", oks
                    if not descriptor[dep] in oks:
                        #print "BAD"
                        ok = False
                if ok:
                    ok_params.append(possible)
                    ok_vals.append(self.cinema_store.get_parameter(possible)['values'])

            for element2 in itertools.product(*ok_vals):
                descriptor2 = dict(itertools.izip(ok_params, element2))
                #print "DESC2", descriptor2
                full_desc = dict()
                full_desc.update(descriptor)
                full_desc.update(descriptor2)

                self.execute(full_desc)
                #print "FULL", full_desc

        self.finish()

    def finish(self):
        """ Give tracks a chance to clean up after a run """
        if self.tracks:
            for e in self.tracks:
                res = e.finish()

    def insert(self, doc):
        self.cinema_store.insert(doc)

class Track(object):
    """
    abstract interface for things that can produce data

    to use this:
    caller should set up some visualization
    then tie a particular set of parameters to an action with a track
    """

    def __init__(self):
        pass

    def prepare(self, explorer):
        """ subclasses get ready to run here """
        pass

    def finish(self):
        """ subclasses cleanup after running here """
        pass

    def execute(self, document):
        """ subclasses operate on parameters here"""
        pass
