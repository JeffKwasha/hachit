from utils import date_from_str

TrustedMSRootThumbprints = ('foo', )
def checkTrusted(dic):
    v = [True for d in dic if d.get('status')]
    l = [True for d in dic if d.get('thumbprint') in TrustedMSRootThumbprints]
    if l and len(v) == len(dic):
       return ('yes', 'Valid signatures chained to a trusted Microsoft cert')


doc={'name':'api_test',
    'inputs':{
        'type': 'REST',
        'name': 'api_test_input', # I just need it to be unique
        'id': 'page',
        'location' : {
            'url': lambda v: 'https://reqres.in/api/users?page={}'.format(v.get('page')),
            'errors' : {
                200: "OK",
                403: "Bad request params",
                404: "File not found... ?",
                500: "Permanent fail",
            },
        },
        'data': {
            'REMAP': {
                'reqres_page' : "page",
                'reqres_count': "per_page",
                'reqres_total': "total",
                'reqres_pages': "total_pages",
                'reqres_ids' : ('data', 0, {
                    'id' : 'id',
                    'name': lambda v: "{} {}".format(v.get('first_name'), v.get('last_name')),
                    'avatar': 'avatar',
                }),
            },
        },
    },
}

# In case that API ever changes, here's the data I expect

page1={"page":1,
       "per_page":3,
       "total":12,
       "total_pages":4,
       "data":[{"id":1,
                "first_name":"George",
                "last_name":"Bluth",
                "avatar":"https://s3.amazonaws.com/uifaces/faces/twitter/calebogden/128.jpg"},
               {"id":2,
                "first_name":"Janet",
                "last_name":"Weaver",
                "avatar":"https://s3.amazonaws.com/uifaces/faces/twitter/josephstein/128.jpg"},
               {"id":3,
                "first_name":"Emma",
                "last_name":"Wong",
                "avatar":"https://s3.amazonaws.com/uifaces/faces/twitter/olegpogodaev/128.jpg"}]}

page2={"page": 2,
       "per_page": 3,
       "total": 12,
       "total_pages": 4,
       "data": [
           {
               "id": 4,
               "first_name": "Eve",
               "last_name": "Holt",
               "avatar": "https://s3.amazonaws.com/uifaces/faces/twitter/marcoramires/128.jpg"
           },
           {
               "id": 5,
               "first_name": "Charles",
               "last_name": "Morris",
               "avatar": "https://s3.amazonaws.com/uifaces/faces/twitter/stephenmoon/128.jpg"
           },
           {
               "id": 6,
               "first_name": "Tracey",
               "last_name": "Ramos",
               "avatar": "https://s3.amazonaws.com/uifaces/faces/twitter/bigmancho/128.jpg"
           }
       ]
       }
