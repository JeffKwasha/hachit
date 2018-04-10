#!/usr/bin/env python3
""" a command line version of hachit """

from config import Config
from os import environ
from sys import argv
import argparse
import re
from pprint import pprint, pformat
from doc import Doc

Config.load(env=environ)

path_rx = re.compile(r'/([^= ]*)$')
pair_rx = re.compile(r'(?P<key>[a-zA-Z_]\w*)\s*=\s*(?P<val>"[^"]*"|\'[^\']*\'|\w*)')
queryCount = 0

def do_query(path, dic):
    d = Doc.from_url(path)
    rv = d.query(dic)
    global queryCount
    queryCount += 1
    print("Query{}: {}".format(queryCount, path))
    pprint(rv)
    print('============')

for i,v in enumerate(argv):
    if i is 0:
        path = ''
        continue
    np = path_rx.match(v)
    if np:
        if path and query:
            do_query(np.group(1), query)
        path = np.group(1)
        query = {}
    else:
        pair = pair_rx.match(v)
        if pair:
            key, val = pair.groups()
            query[key] = val
        else:
            print("unable to parse: {}".format(v))
        pass
    pass

if path and query:
    do_query(path, query)
else:
    print("path:", path, "query:", pformat(query))


