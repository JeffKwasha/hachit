""" Mapper
    'maps' data into a new heirarchy:
        A mapper from: { 'REMAP': {'out' : ('foo', 'bar', 2)}
        with input:    {'foo'  : { 'bar' : ('baz', 5, 'buzz') } } 
        will output:   {'out' : 'buzz' }

    More formally:
        Mapper is built from a dictionary; mapper = Mapper( {...} )
        Mapper is called on some data;     newData = mapper(data)
        Mapper REMAPs its input, evaluates its fields, and DISCARDs parts of the result.
        REMAP - search the input for values and assign them to the REMAP's fieldname:
            { K:REMAP(V, INPUT) for K,V in REMAP.items() }
                REMAP() does the following:
                if 'V' is a string or int:      return INPUT[FIELD_NAME]
                if 'V' is a tuple, drill down:  return INPUT[FIELD_NAME[0]][FIELD_NAME[1]]...
                if 'V' is a list,               return [  REMAP(i, INPUT) for i in V]
                if 'V' is a dict, recurse       return {k:REMAP(v, INPUT) for k,v in V.items()}
                if 'V' is a function,           return V(INPUT)

        'fields' - anything in mapper's top level other than 'REMAP', 'DISCARD', 'INDEX', or 'TYPES' is a field
            Fields are simply evaluated and assigned, and they 'update' the value built by REMAP

        DISCARD - search the value and discard anything found. (performed last)
            typically a list of keys or indexes to delete,
            Unnecessary if REMAP is used (Why REMAP only to later discard)
"""

# a class to execute mappings over data
from copy import deepcopy
import logging
from utils import eval_field
#TODO lambda data: {k,v for k,v in data if len(k) > 5}
#TODO lambda data: ((a,b) for a,b in data if 'foo' in a)

logger = logging.getLogger(__name__)
from pprint import pformat
class Mapper:
    """ Mapper is the universal converter between data structures.
    NOTE! Mapper doesn't make clean copies. It will wreck your input and the input and output will be linked.
    Mapper( { 'REMAP' : {...}, 'DISCARD' : [...], 'etc' : 'foo' } )
    works like a dictionary: mapper_instance['out_field'] = 'foo string'
    works like a function: out_data = mapper_instance(data_in)
    chops up and rebuilds input data based on 'REMAP', 'DISCARD', 'dictionary fields'...
    REMAP : { 'key': 'value' } navigates data using value and returns {'key': data['value']}
        You can drill down into dictionaries lists and tuples: { 'key': ('top_dict', 'sub_dict', 3) } 
        You can use a function to inspect the data and return a value { 'key' : lambda data: ','.join( data['list'] ) }

    DISCARD: throws away outputs... 

    TODO: Mapper config should be able to refer to itself: 'outfield' = lambda v: self.config['remap']['bar']
    TODO: output elastic mapping structures based on config... ?
    Mapper constant values override values from REMAP 
    Mapper DISCARD is performed last (overriding everything)
    Mapper constant values can be iterated like a dict.
    Mapper constant values can be lookedup/assigned like a dict
    Mapper constant values can be a function to execute on the data, which means the function can alter the data at will.
    """
    __slots__ = ('remap', 'discard', 'index', 'types', 'fields')

    def __init__(self, dic, data=None):
        logger.debug("Initializing {} from {}".format(self.__class__.__name__, dic))
        dic_t = type(dic)
        if dic_t is Mapper:
            raise Exception("Don't initialize a mapper with a mapper")
        if dic_t is dict:
            self.remap   = dic.pop('REMAP', None)  # fields you want to rename or rearrange
            self.discard = dic.pop('DISCARD', None)# fields you don't want
            self.index   = dic.pop('INDEX', None)  # index is reserved for future elasticsearch magicality
            self.types   = dic.pop('TYPES', None)  # types is reserved for future elasticsearch magicality
            self.fields  = dic          # fields are simply assigned values ie: return value(data) if callable(value) else value.
        elif dic_t in (str, int, float):
            self.fields = dic
        if data:
            self.fields = self(data)

    @staticmethod
    def _discards(discards, data):
        if not discards:
            return
        #logger.error('del {} on {}'.format(pformat(discards,), pformat(data)))

        d_t = type(discards)
        if d_t in (int, str):
            try:
                del data[discards]
            except IndexError: pass
            except KeyError:   pass
            except TypeError:  pass
            return
        elif d_t is tuple:
            # Drill down
            if len(discards) > 1: Mapper._discards(discards[1:], data[discards[0]])
            else: Mapper._discards(discards[0], data)
            return
        # if discards is not a tuple, but is iterable, just delete the whole list (or dictionary keys or ...)
        for li in discards:
            Mapper._discards(li, data)
        return

    def __call__(self, data):
        """ frankinstate output from data-parts.  
            this makes Mapper 'callable' so a Mapper is a valid field value in defining a Mapper. 
            Not sure how you could, but Don't make cycles.
        """
        logger.debug("mapper: {} data: {}".format(self.remap, data))
        from utils import search
        # remap the input data (effectively deleting anything not listed)
        if self.remap:
            rv = search(self.remap, data)
        elif data:
            rv = deepcopy(data)
        else:
            rv = {}
        # add the static fields 
        if self.fields:
            eval_field(rv, self.fields, rv)
        # delete any discards
        self._discards(self.discard, rv)
        return rv

    def __getitem__(self, key):         return self.fields.__getitem__(key)
    def __setitem__(self, key, val):    return self.fields.__setitem__(key, val)
    def __iter__(self):                 return self.fields.__iter__()
    def __next__(self):                 return self.fields.__next__()

def _test():
    data=  {
            'DISCARD' : 'hash',
            'REMAP': {
                'hash' : lambda v: v[0],
                'name' : lambda v: v[1],
                'date.created' : lambda v: v[2],
                'comment' : lambda v: v[3],
                },
            'key': 'value',
            }
    try:
        m = Mapper(data)
        return m(['a','b','c','d']) == {'name':'b', 'date.created':'c', 'comment':'d', 'key':'value'}
    except:
        return False
