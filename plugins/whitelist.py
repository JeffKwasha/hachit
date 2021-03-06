# a plugin: CSV whitelist. 
#   here we create a 'document type' (or 'an instance of Doc') with one input (a csv file)
# NOTE: 'doc' is a magic variable that is used to build a Doc instance `Doc( **module.doc )`
#       This eliminates any need for us to 'from doc import Doc', which is good.

from datetime import datetime
from utils import date_from_str

def counter(*args):
    global count
    try:
        count += 1
    except:
        count = 1
    return count

doc = {
    'name':'whitelist',
    'inputs':{
        'name' : 'whitelist_csv',   # again, a unique name is always required
        # csv_input simply wants to read a file. So 'location' is just a file path.
        'location' : 'whitelist.csv',   # This path will be read immediately, so we can use a relative path (to the plugin file)
        # csv_input only knows how to use one value - a dictionary key we name with 'id'
        'id': 'hash',

        # 'data' is a 'Mapper': it massages the raw input data into the document's format
        'data': {
            'REMAP': {      # REMAP instructs the Mapper to name outputs directly from inputs
                'name': 0,  #   our output dictionary will have a 'name' field taken from column 0
                'hash': 1,  #   and a 'hash' field taken from column 1
                'date.created': (2, lambda v: date_from_str(v)),
                'comment': 3,
            },
            'from_whitelist': True, # this field will simply be copied
            'counter': counter,                            # THIS, IS, PYTHON
            'date.retrieved': lambda v: datetime.utcnow().replace(microsecond=0), # yes, we can
        },
    },
}
