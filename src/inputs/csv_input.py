import os
import logging
import csv
import re

from utils import search, search_all, FuncType, multiple_replace
from mapper import Mapper
from input import Input, h_logger, l_logger
from pprint import pformat

def _validify(s): 
    """ simply replaces '.' and '/' from strings that must be attributes """
    s_t = type(s)
    if s_t in (int, float):
        return s
    elif s_t is str:
        return re.sub('^[^a-zA-Z_]|[^a-zA-Z0-9_]', '_', s)
    else:
        raise Exception("What is <{}>?".format(pformat(s)))

class CsvInput(Input):
    """ load a csv into 'data' - so the entire csv is loaded into memory. 
        In a multiprocess environment (uwsgi) each process will have its 
        own copy in memory (processes can't share). Please keep csv data to a minimum.
    """
    # NOTE: unix_dialect requires python 3.2
    #dialect = csv.register_dialect('myDialect', csv.unix_dialect, quoting=csv.QUOTE_MINIMAL)
    subtypes = ('csv',)
    __slots__ = ()

    def __init__(self, **kwargs):
        """ read the file into memory as self.data. 
        """
        if not hasattr(self,'location'):
            super().__init__(**kwargs)
        filename = self.location
        if callable(filename):
            filename = filename(kwargs)
        if not hasattr(self,'name'):
            basename = os.path.basename(filename)
            self.name= os.path.splitext(basename)
            pass
        self.data = self._read(
                filename  = filename,
                id_name   = self.id_name,
                mapper = Mapper(self.data),
                # fieldnames= kwargs.get('fieldnames') # leave None if the csv has a header line 
            )

    def _read(self, filename, id_name, mapper=None):
        """ read a csv file. Return a dictionary of mapped rows """
        with open(filename, newline='') as f:
            dialect = csv.Sniffer().sniff(f.read(1024))
            f.seek(0)
            reader = csv.reader(f, dialect=dialect)
            id_field = 0
            try:
                if mapper and mapper.remap and mapper.remap.get(self.id_name):
                    premap_id = mapper.remap[self.id_name]
                    if type(premap_id) is str:
                        self._headers = next(reader)
                        if premap_id not in self._headers:
                            raise ValueError("{} not found in first row of {}".format(premap_id, filename))
                        id_field = self._headers.index(id_name)
                    elif type(premap_id) is int:
                        id_field = premap_id
                        pass
                    pass
                # Above will fail If lambda used to 'build' the id_name field.
                elif mapper[id_name]:   # Mapper[] uses get to lookup fields
                    raise Exception("Using a lambda to 'build' the id field of a csv input is not implemented")
                else:
                    mapper = lambda v: v
                return { row[id_field]: mapper(row) for row in reader}
            except csv.Error as e:
                logging.error("%s csv format error at %d", filename, row.line_num)
                return None

    def get(self, key, default={}):
        nt = self.data.get(key)
        if not nt:
            return default
        return nt

    @classmethod
    def validate(cls, dic, errors=None):
        if type(dic) is not dict:
            return False
        if os.path.exists(dic.get('location')):
            try:
                with open(dic['location']) as f:
                    r = csv.reader(f)
                    next(r)
                return 100
            except:  pass
        errors[cls.__name__]="Unable to open {} as a csv file".format(dic['location'])
        return False

CsvInput.register()

def _test():
    d = {
        'name' : 'white',
        'location' : '../test/white.csv',   # Ugly, but effective.
        'id': 'hash',
        'data': {
            'REMAP': {
                'name': 0,
                'hash': 1,
                'date.created': 2,
                'comment': 3,
                },
            },
        }
    csvin = Input(**d)
    from pprint import pprint as pp
    return csvin.get('41e25e514d90e9c8bc570484dbaff62b')['name'] == 'cmd.exe'
# vim ts=4 sw=4
