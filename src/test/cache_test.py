from inputs import api_input, cache_input

doc={'name':'api_test',
     'inputs': {
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
                 'date.created': (2, lambda v: date_from_str(v)),
                 'comment': 3,
             },
             'from_csv_input': True,
             'comment_hash': ('comment', lambda v: md5(v)),
         },
     },
     'cache': {
         'type': 'elasticcache',
         'expire_date': 1,
     },
}
