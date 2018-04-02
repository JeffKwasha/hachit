from inputs import api_input, cache_input

doc={'name':'api_test',
     'inputs': {
         'type': 'https:',
         'name': 'vt_hash_test',
         'id': 'hash',
         'location' : {
             'url': 'https://www.virustotal.com/vtapi/v2/file/report',
             'params': {
                 'apikey' : 'c1ce0d366721e43fd0c4f983da408feb79a2db54e164d47346691e9c9b575aa3',
                 'resource': lambda args: args.get('hash'),
                 'allinfo': '1',
             },
             #'headers':None,
             'errors' : {
                 200: "OK",
                 403: "Bad request params",
                 404: "File not found... ?",
                 500: "Permanent fail",
             },
         },
         'data': {
             'REMAP': {
                 "scan_date"         : 'scan_date',
                 "first_seen"        : 'first_seen',
                 "last_seen"         : 'last_seen',
                 "times_submitted"   : 'times_submitted',
                 "positives"         : 'positives',
                 "sha256"            : 'sha256',
                 "permalink"         : 'permalink',
             },
         },
     },
     'cache': {
         'type': 'elasticcache',
         'expire_date': 1,
     },
}
