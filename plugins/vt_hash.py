# This hachit plugin defines the API for VirusTotal file hash data

from secrets import VT_API_KEY, TrustedMSRootThumbprints, TrustedOrganizations
from utils import date_from_str, epoch_from_date, date_from_epoch

def is_goodware(v):
    for li in v:
        if li.get('organization') in TrustedOrganization and li.get('verdict') is 'goodware':
            return ('Yes', "VT validated organization: {}".format(li['organization']))

def checkTrustedVerdicts(dic):
    v = [True for d in dic if d.get('status')]
    l = [True for d in dic if d.get('thumbprint') in TrustedMSRootThumbprints or []]
    if l and len(v) == len(dic):
       return ('Yes', 'Valid signatures chained to a trusted Microsoft cert')

# This little function solves a little conundrum for us.
# The source data contains a list of dictionaries, but they aren't all the same.
# Also, we're not sure if order is consistent (we can't just pick index 0)...
# This function returns the first dictionary with a 'codeview' - dynamically picking 
# the 'right' index so we can continue to drill down to find our pe_pdb_string
# TODO make a 'wildcard' index which 'searches' into each item until valid data is returned.
def find_type_str(li):
    for i in li:
        if i.get('codeview'):
            return i

doc={
    'name':'vt_hash',
    'id': 'hash',
    'inputs':   {
        'type': 'REST',
        'name': 'vt_hash_input',
        'location' : {
            # location is a Mapper instance used to build parameters for a request from query arguments
            # currently requests use 'GET'
            'url': 'https://www.virustotal.com/vtapi/v2/file/report',
            'params': {
                'apikey' : VT_API_KEY,
                'resource': lambda args: args.get('hash'),
                'allinfo': '1',
            },
            'errors' : {
                200: "OK",
                403: "Bad request params",
                404: "File not found... ?",
                500: "Permanent fail",
            },
        },
        'data': {
            'REMAP': {
                "vt_file_scan_date"         : ('scan_date', lambda v: epoch_from_date(date_from_str(v))),
                "vt_file_first_seen"        : ('first_seen',lambda v: epoch_from_date(date_from_str(v))),
                "vt_file_last_seen"         : ('last_seen', lambda v: epoch_from_date(date_from_str(v))),
                "vt_file_times_submitted"   : 'times_submitted',

                "vt_file_positives"         : 'positives',
                "vt_file_sha256"            : 'sha256',
                "vt_file_permalink"         : 'permalink',

                "vt_file_exiftool_description": ('additional_info', 'exiftool', 'FileDescription',),
                "vt_file_exiftool_object_type": ('additional_info', 'exiftool', 'ObjectFileType',),

                "vt_file_pe_magic"          : ('additional_info', 'magic',),
                "vt_file_pe_pdb_string"     : ('additional_info', 'pe-debug', find_type_str, 'codeview', 'name'),
                "vt_file_pe_product"        : ('additional_info', 'sigcheck', 'product', ),
                "vt_file_pe_copyright"      : ('additional_info', 'sigcheck', 'copyright'),
                "vt_file_pe_original_name"  : ('additional_info', 'sigcheck', 'original name'),

                "vt_file_signature_signing_date"                : ('additional_info', 'sigcheck', 'signing date', lambda v: epoch_from_date(date_from_str(v))),
                "vt_file_signature_description"                 : ('additional_info', 'sigcheck', 'description'),
                "vt_file_signature_signers"                     : ('additional_info', 'sigcheck', 'signers'),
                "vt_file_signature_signers_thumbprints"         : ('additional_info', 'sigcheck', 'signers details',
                                                                   lambda v: ';'.join([s.get('thumbprint', '') for s in v])),
                "vt_file_signature_verified"                    : ('additional_info', 'sigcheck', 'verified'),
                "vt_file_signature_counter_signers"             : ('additional_info', 'sigcheck', 'counter signers'),
                "vt_file_signature_counter_signers_thumbprints" : ('additional_info', 'sigcheck', 'counter signers details',
                                                                   lambda v: ';'.join([s.get('thumbprint', '') for s in v])),

                ("vt_file_trusted_microsoft",
                 "vt_file_trusted_microsoft_reason") : ('additional_info','trusted_verdicts', is_goodware),
                ("vt_file_trusted_microsoft",
                 "vt_file_trusted_microsoft_reason") : ('additional_info','trusted_verdicts', is_goodware),
                 "vt_file_microsoft_trusted" : ('additional_info','trusted_verdicts', checkTrustedVerdicts),
            },
            'from_vt_md5': True,
        },
    },
    'cache':{
        'type': 'elasticcache',
        'location': {
            'urls': 'http://localhost:9200',
#            'timeout': 1,
#            'username': None,
#            'password': None,
        },
        'expire_date': ('vt_file_first_seen', lambda v: double_time(date_from_epoch(v)), 0.5),
    },
}
