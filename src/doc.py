from werkzeug.exceptions import BadRequest
from pprint import pformat
from config import Config
from input import Input
from exceptions import NotFound

logger = Config.getLogger(__name__)
        
# access imported modules for API endpoints. 
# instantiate Api() for each endpoint.
# return or somehow provide a list of Api() who can generate flask blueprint.

# should know:
# url
# urlFunction -> bp
# args -> common_args

class Doc:
    _all = {}
    def __init__(self, name, inputs, id=None, cache=None, **kwargs):
        # we can't immediately resolve inputs. Process args when requested.
        self.name = name
        if self.name in Doc._all:
            raise Exception("Doc: name collision: {}".format(self.name))
        self.id_name = id
        self.cache = Input(name=self.name, id=self.id_name, **cache) if cache else None
        self._query_config = kwargs.get('query')
        self._input_config = inputs
        try:
            # This attempts to build the inputs. 
            # Hopefully any errors will be found now while the file context exists.
            self.inputs
        except NotFound:
            # our inputs are merely named (not defined...yet). As more plugins are built this should resolve.
            pass
        self.query_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        # Api tracks all instances for 'from_url'
        Doc._all[self.name] = self

    @property
    def inputs(self):
        """ An input is anything we can query() for data (Doc, Input, ... ?)
            it must have: 
                query(**args)
                get(id) ?
        """
        if getattr(self, '_inputs', False) and not getattr(self,'_input_config', False):
            return self._inputs
        self._inputs = self.build(self._input_config, id_name=self.id_name)
        if not self._inputs:
            raise ValueError("{} Unable to build inputs. self-terminating".format(self.name))
        if type(self._inputs) not in (list, tuple):
            self._inputs = (self._inputs,)
        del self._input_config
        return self._inputs


    @classmethod
    def build(cls, dic, id_name=None):
        dic_t = type(dic)
        if dic_t in (tuple, list):
            rv = [cls.build(d, id_name) for d in dic]
        elif dic_t is dict:
            id_name = dic.pop('id', id_name)
            rv = Input(id=id_name, **dic)
        elif dic_t is str:
            rv = Doc._all.get(dic) or Input._all.get(dic)
        if not rv:
            raise NotFound("{}: Unable to build {}".format(cls.__name__, pformat(dic)))
        return rv
        # at some point this may be needed, it's from inputs()

    def query(self, args):
        # IDEA: could return an iterator of results ?!?
        """ query cache??

            if an arg allows input.get() ??
            otherwise use input.query()
            merge results
        """
        if self.cache and self.cache.id_name in args:
            rv = self.cache.get(args[self.cache.id_name])
            if rv:
                return rv

        rv = {}
        for src in self.inputs:
            if getattr(src,'id_name',None) in args:
                rv.update(src.get(args[src.id_name]))
            else:
                rv.update(src.query(args))

        if rv and self.cache and self.cache.id_name in rv:
            self.cache.set(key=rv[self.cache.id_name], value=rv)
        return rv

    def get(self, _id):
        """ given an index value return a document
            get doesn't know how to pick from multiple arguments, so every input better use the same field 
        """
        self.query_count += 1
        if type(_id) is str:
            if self.cache:
                rv = self.cache.get(_id)
                if rv:
                    self.cache_hits += 1
                    return rv
                self.cache_misses += 1
            rv = {}
            for src in self.inputs:
                # TODO - merge (sets) instead of 'update'
                rv.update(src.get(_id))
            if self.cache:
                self.cache.set(_id, rv)
            return rv
        pass

    def pop(self, key, default=None):
        return getattr(self, key, default)

    # if we had a 'default query' we could support __iter__ and __next__ ?

    def delete_self(self):
        del Doc._all[self.name]
        pass

    def stats(self):
        return {'cache_hits'  : self.cache_hits,
                'cache_misses': self.cache_misses,
                'query_count' : self.query_count 
               }

    @classmethod
    def from_url(cls, path):
        """ find a Doc instance from the flask request path """
        rv = cls._all.get(path)
        if rv:
            return rv
        raise BadRequest("Hachit: plugin <{}> was not found. "
                       "Check the log for errors".format(path))
        pass
    pass

    @classmethod
    def urls(cls):
        return { k: getattr(v, 'id_name', 'Unknown') for k,v in cls._all.items()}
#END of Doc

def _test():
    import inputs.csv_input
    import inputs.cache
    d = Doc(
        name='testDoc',
        id='hash',
        inputs=[{
            'name': 'white',
            'location' : './test/white.csv',
            'data': {
                'REMAP': {
                    'name': 0,
                    'hash': 1,
                    'date.created': 2,
                    'comment': 3,
                },
            },
        }],
        cache={
            'type':'elasticcache',
            'location': 'localhost',
            'expire-date': '1y',
        },
    )
    return d.get('41e25e514d90e9c8bc570484dbaff62b')['name'] == 'cmd.exe'

