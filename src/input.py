# Input - imports and massages data. Subclasses provide access to different 'types': csv, webapi, elasticsearch, ...
#       input plugins are loaded by config.py - _setup_plugins()
#       subclasses ('plugins') should inherit Input, and register their 'type' by calling __class__.register()
#       Input's constructor is 'magic' and will construct the appropriate subclass for the given kwargs!
from config import Config
from mapper import Mapper
from exceptions import NotFound
from pprint import pformat

h_logger = Config.getLogger('hachit')
l_logger = Config.getLogger(__name__)

#   Docs need to query external sources for data.
#   Input classes handle getting and mapping external data into our common format
#   Like Doc, Input classes must have get() and query() methods ...
#       although get() can return None to force a query()
#   Input concerns itself with:
#       formatting requests and responses
#       rate limiting
#       logging

# TODO - have imported locations register their types with Input
class Input:
    """ An Input defines a way to import and lookup data.  Like a doc it supports query() and get(). 
        REST - WebApi (RESTful webapi data sources )
        CSV - CsvFile
        DB  - DBInput ( Future )
        URLs / JSON ( other than RESTful)

        Input knows how to:
            select and instance a registered subclass based on input parameters
            get   - lookup an unique ID ('index') and return a value
                Either of these might need to obtain a new record, and remap it to 'common fields'
            query* - remap 'common (argument) fields' into location specific fields, and validate them
                ( FUTURE, currently just a wrapper for get )
            remap the source data into 'common fields'
    """

    types = {}
    _all = {}
    __slots__ = ('name', 'data', 'id_name', 'location')

    def __new__(cls, name, **kwargs):
        """ Magically instantiate the correct subclass.

            There's no earthly way of knowing 
            Which direction we are going 
            There's no knowing where we're rowing 
            Or which way the river's flowing 
        """
        # TODO. This isn't clean - It 'should' return a new instance of a subclass, 
        #   but we might also want an existing instance, or a new instance linked to an existing instance.
        if cls is not Input:
            return super().__new__(cls)
        if name in Input._all:      # return any existing instance
            return Input._all[name]
        subcls = Input.get_subclass(name, **kwargs)
        if subcls:
            obj = super().__new__(subcls)
            return obj
        raise Exception("Unknown Input type: {}. supported: {}".format(name, Input.types.keys()))

    def __init__(self, name, location=None, id=None, data=None, **kwargs):
        if name in Input._all:      # already initialized?
            logger.info('{} exists, returning existing object unchanged'.format(name))
            return
        self.name = name            # uniquely identifies this source. Used in logging or to use a source by reference (DRY)
        self.data = data            # data remaps fields returned by this source to a 'common' set of fields
        self.id_name = id           # id_name - the name of the 'common' field the source uses as a unique record identifier
        self.location = location    # location - file/URL/DB/... how to access the data, can be a dict or simply name an instance
        Input._all[name]=self       # record every instance as it leaves the factory so it can be referenced by name

    @classmethod
    def build(cls, name, dic):
        """ given a definition dict, do whatever is needed and return an instance:
            select an input subtype, instantiate and return it 
        """
        l_logger.info("Building: {}".format(dic))
        subcls = get_subclass(name, **dic)
        if subcls:
            obj = super().__new__(subcls)
            return obj

    @classmethod
    def register(cls):
        """ called by subclass to allow Input() constructor to find and return that subclass """
        if cls is Input:
            return None
        if not cls.subtypes:
            l_logger.error("A location must define its types: {}".format(cls.name))
            raise ValueError("{} has no 'types', unable to register".format(cls.name))
    
        t = type(cls.subtypes)
        if t in (list, tuple):          # a subclass can specify multiple 'types' - ODBC subclass might accept DB2/sqlite/mysql ...
            for subtype in cls.subtypes:   # "subtype" is some immutable unique identifier, probably strings: 'csv', 'sqlite', 'webapi' or some type identifier
                Input.types[subtype]= cls
        elif t in (str, int):
            Input.types[cls.subtypes]= cls

        h_logger.info("Input: {} registered for {}".format(cls.__name__, cls.subtypes))
        return True

    @staticmethod
    def get_subclass(name, type=None, **kwargs):
        """ return a subclass that handles the input """
        if type in Input.types:
            return Input.types[type]
        errors = {}
        best, pick = 0, None
        for t,cls in Input.types.items():
            tmp = cls.validate(kwargs, errors=errors)
            if tmp > best:
                pick = cls
                best = tmp
        if pick:
            return pick
        raise NotFound("Unable to build Input for '{}':\n{}\n-------------".format(name, pformat(errors)))

    @classmethod
    def validate(cls, dic, errors=None):
        """ validate is used to 'autodetect' an Input subclass given a dict.
            return True if dic is valid for your subclass
            use errors[cls.__name__] = REASON STRING to help users create valid docs
        """
        return False

    # This generic implementation assumes args contain an ID and run the instance's get()
    def query(self, dic):
        return self.get(dic.get(self.id_name))

    def __getitem__(self, key):        return self.get(key)
    def __setitem__(self, key, value): return self.set(key, value)

    def get(self, index, default={}):
        """ generic Input.get assumes self.data is a dict """
        return self.data.get(index, default)

    def set(self, index, value):
        self.data[index]=value

# vim ts=4 sw=4
