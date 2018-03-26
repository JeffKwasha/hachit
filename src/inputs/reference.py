"""
Reference is a thin wrapper 
"""

from input import Input
from config import Config
logger = Config.getLogger(__name__)

class Reference(Input):
    __slots__ = ()
    subtypes = ('ref',)
    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)
        if self.data:
            self.data = Mapper(self.data)

    @classmethod
    def validate(cls, dic, errors=None):
        location = getattr(dic, 'location', None)
        if location in Input._all:
            return 100
        if type(location) is str:
            # could be an input that hasn't loaded yet.
            return 1
        return False

    def query(self, dic):
        if not isinstance(self.location, Input):
            self.location = Input._all[self.location]
        rv = self.location.query(dic)
        if self.data:
            return search(self.data, rv)

    def get(self, index, default={}):
        return self.location.get(index, default)

    def set(self, index, value):
        if hasattr(self.location, 'set'):
            return self.location.set(index, value)

    def __getitem__(self, key):         return self.get(key)
    def __setitem__(self, key, val):    return self.set(key, val)
#    def __iter__(self):                 return self.results.__iter__()
#    def __next__(self):                 return self.results.__next__()

Reference.register()
