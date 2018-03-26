#from config import Config
#from source import Source
#from datetime import datetime
from doc import Doc
from inputs import csv_input    # test framework doesn't load all the plugins/inputs

#autotype: File, URL( HTTP, DB ), graphQL(HTTP POST)
#   DB - DBinput query string? - slot in the fields
#   graphQL - ? would look like HTTP
#   File - find location on disk

# query_up.
#   File - internal dict lookup
#   URL  - remap effectively selects fields, encode fields (POST json, Headers, GET Args, GET path, BASE64)
#   graphQL - remap effectively selects fields, but hierarchy...
#   DB - remap selects, hierarchy transform to table/columns.  Build the query: select * where 'and'.join(fields)

# data format:
#   File: location, type(csv, ...), fields_wanted: index - selected d
#


# how to interface DS(id) <-> D(local.id) <-> C(

Doc(name='csv_test',
    inputs=[{
        'name' : 'white',
        'location' : 'white.csv',
        # args maps from the common 'data' fields into source specific fields
        #     Here CsvInput only knows how to use one value - a dictionary key we name with 'id'
        #     I hope to eliminate args (for most cases) in the future as it is redundant with 'data'
        'id': 'hash',

        # data maps from the source specific fields into common 'data' fields that will be added to the 'Doc'
        #     A Mapper encapsulates this translation
        'data': {
            'DISCARD' : ['comment'],
            'REMAP': {
                'name': 0,
                'hash': 1,
                'date.created': 2,
                'comment': 3,
                },
            'from': 'csv_input',
            },
        }],
)
