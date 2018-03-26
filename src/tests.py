import unittest
import os
from pprint import pprint as pp
from config import Config
from utils import *
from mapper import Mapper
from doc import Doc
Config._setup_loggers(verbosity=99)


class off_testConfig(unittest.TestCase):
    def test_load(self):
        return 
        """
        # TODO - Absolute path          "./test/test.yaml"
        filename = os.path.join(os.curdir, 'test', 'test.yaml')
        Config.load(filename, env={'MERGED_NAME': 'envOverride', 'new_val': 'value'})
        self.assertIsNone(Config.get("NOT_CONFIGURED"))
        self.assertEqual(Config.get('SECRET_KEY'), 'ITS_A_SECRET_TO_EVERBODY')
        self.assertEqual(Config.get('MERGED_NAME'), 'envOverride')
        self.assertEqual(Config.get('new_val'), 'value')
        if not os.path.exists(Config.get('SPOOL_DIR')):
            os.mkdir(Config.get('SPOOL_DIR'), 700)
        """

    def test_defaults(self):
        return
        """
        self.assertEqual(Config.get('WEB_ROOT'), None)
        self.assertEqual(Config.get('TEST_DEFAULT_1'), None)
        self.assertEqual(Config.setdefault('TEST_DEFAULT_1', 1), 1)
        self.assertEqual(Config.get('TEST_DEFAULT_1'), 1)
        self.assertEqual(Config.get('TEST_DEFAULT_1', minval=2), 2)
        self.assertEqual(Config.get('TEST_DEFAULT_1'), 2) 
        with self.assertRaises(ValueError, msg="conflicting defaults"):
            Config.get('TEST_DEFAULT_1', default=2)
        with self.assertRaises(ValueError, msg="default < minval"):
            Config.get('TEST_DEFAULT_1', default=1, minval=2)
        """

class testUtils(unittest.TestCase):
    def test_parse_duration(self):
        self.assertEqual(parse_duration("20.5h 25m 300s").total_seconds(), 3600 * 21)
        self.assertEqual(parse_duration("1d ago").total_seconds(), 3600 * 24)
        self.assertEqual(parse_duration("1w 1d").total_seconds(), 3600 * 24 * 8)
        self.assertEqual(parse_duration("5").total_seconds(), 5)
        self.assertEqual(parse_duration("3.15").total_seconds(), 3.15)

    def test_parse_capacity(self):
        self.assertEqual(parse_capacity(100), 100)
        self.assertEqual(parse_capacity("25"), 25)
        self.assertEqual(parse_capacity("0.5 TB 1GB 1mb 50b"), 
                (1024**4)/2.0 + 1024**3 + 1024**2 + 50)
        return

    def test_time(self):
        from datetime import datetime, timedelta
        self.assertEqual(datetime(1970, 1, 1) + timedelta(seconds=100), from_epoch(100) )
        self.assertEqual(epoch(datetime(1970, 1, 2)), timedelta(days=1).total_seconds())

    def test_recurse_update(self):
        a = { 
                '3': 1,
                '1': 1, 
                'map': {'set':'set', 'unset':None},
                'extend': [(1, 1), (3, 3)],
                'three': (1, 2, 5),}
        b = { 
                '3': 3,
                '1': None, 
                'map': {'set': None, 'unset': 'unset', 'new': 'new'},
                'extend': [(2, 2), (1, 1)],
                'three': 'three'}
        c = recurse_update(a,b, ignore_none=True)
        self.assertEqual(c, a)
        for k,v in c.items():
            if type(v) in (int, str):
                self.assertEqual(k, str(v))
            elif type(v) is dict:
                for i,j in v.items():
                    self.assertEqual(i, j, msg="{} {}:{}".format(k,i,j))
            elif type(v) is list:
                v.sort()
                self.assertEqual(v, [ (i, i) for i in range(1, len(v)+1)])
            elif type(v) is tuple:
                self.assertEqual(v, tuple(k.split()), msg="{}, {}".format(v,k))

    def test_search(self):
        """ tests searchTuple, searchDict, and searchFunction """
        source = { "foo": [ 1, 2 ], 'bar' : { 'bar1': 1, 'bar2':2 }, 'baz' : ['a', 'bunch', 'of', 'strings'] }
        conf = { "fooc" : 'foo', 'bar1c' : ( 'bar', 'bar1' ), 'bazzes': ('baz', lambda v: ';'.join(v)) }
        output = search(conf, source)
        self.assertEqual(output, {'bar1c': 1, 'bazzes': 'a;bunch;of;strings', 'fooc': [1, 2]})

    def off_test_mergeDict(self):
        s1 = { 'a': 'a1', 'b' : 'b1', 'c':['c.l1','c.l2'], 'd':{'d.k1': 'd.v1', 'd.k2': ('d.v2.t1', 'd.v2.t2')}}
        s2 = { 'a': 'a2', 'b' : ('b1', 'b2.t1',), 'c':'c.l1', 'd':{'d.k1': 'd.v2', 'd.k2': 'd2.v2.t1'}}
        s3 = { 'd': 'd3'}
        output = mergeDict(s1, s2)
        print("-----------------------")
        pp(output)
        print("-----------------------")
        #self.assertEqual(output, {'bar1c': 1, 'bazzes': 'a;bunch;of;strings', 'fooc': [1, 2]})

def mergeAtoms(*args):
    return set(args)

class testInput(unittest.TestCase):
    def test_apiInput(self):
        """ load api_test.py and check the results """
        module = Config.load_plugin('test/api_test.py')
        doc = Doc.from_url("api_test")
        result = doc.query( { 'hash' : '41e25e514d90e9c8bc570484dbaff62b' } )
        # This URL is available on the public API, but the 'analysis' number will occasionally change
        self.assertEqual( result.get('vt_file_permalink')[:105],
                         'https://www.virustotal.com/file/e6c49f7ce186dc4c9da2c393469b070c0f1b95a01d281ae2b89538da453d1583/analysis/1520818583/'[:105]
                        )
                
    def test_csvInput(self):
        """ load csv_test.py and check the results """
        module = Config.load_plugin('test/csv_test.py')
        doc = Doc.from_url("csv_test")
        result = doc.query( { 'hash' : '41e25e514d90e9c8bc570484dbaff62b' } )
        self.assertEqual( result, {'name':'cmd.exe', 'hash':'41e25e514d90e9c8bc570484dbaff62b', 'from': 'csv_input', 'date.created':'2018-02-20T11:23:00Z'}  )
                
class testMapper(unittest.TestCase):
    def test_discard(self):
        """ see if mapper properly discards and remaps"""
        m = Mapper({ 'DISCARD': [ 'foo', ('bar', ['barbar', 'barfoo']) ] })
        r = m({'foo': 'buzz', 'bar': {'barfoo': 'bf', 'barbar': 'bb', 'barbuzz':'bz'}, 'baz': 1})
        self.assertEqual(r, {'baz': 1, 'bar': {'barbuzz':'bz'} })

    def test_eval(self):
        """ see if mapper properly uses fields """
        m = Mapper({ 'REMAP': {'F': 'foo', 'B':('bar', 'bar2')}, 'foo': 'bar' , 'twenty-three': 23, 'list': ['a','b']})
        r = search(m, {'foo': 'F', 'bar': {'bar2': 'B', 'zip': 'Z'}})
        self.assertEqual({'F':'F', 'foo':'bar', 'B': 'B', 'twenty-three': 23, 'list':['a','b']}, r)

    def test_remap(self):
        """ see if mapper properly discards and remaps"""
        source = { "foo": [ 1, 2 ], 'bar' : { 'bar1': 1, 'bar2':2 }, 'baz' : ['a', 'bunch', 'of', 'strings'] }
        conf = Mapper({ 'REMAP': { "fooc" : 'foo', 'bar1c' : ( 'bar', 'bar1' ), 'bazzes': ('baz', lambda v: ';'.join(v)) }})
        output = search(conf, source)
        self.assertEqual(output, {'bar1c': 1, 'bazzes': 'a;bunch;of;strings', 'fooc': [1, 2]})

unittest.main()
