from inputs import api_input
from utils import date_from_str

TrustedMSRootThumbprints = ('foo', )
def checkTrustedVerdicts(dic):
    v = [True for d in dic if d.get('status')]
    l = [True for d in dic if d.get('thumbprint') in TrustedMSRootThumbprints]
    if l and len(v) == len(dic):
       return 'Valid signatures chained to a trusted Microsoft cert'


doc={'name':'api_test',
    'inputs':{
        'type': 'https:',
        'name': 'vt_hash_test', # I just need it to be unique
        'id': 'hash',
        'location' : {
            'url': 'https://www.virustotal.com/vtapi/v2/file/report',
            'params': {
                'apikey' : 'c1ce0d366721e43fd0c4f983da408feb79a2db54e164d47346691e9c9b575aa3',  #TODO remove my personal key.
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
                "vt_file_scan_date"         : ('scan_date', lambda v: date_from_str(v)),
                "vt_file_first_seen"        : 'first_seen',
                "vt_file_last_seen"         : 'last_seen',
                "vt_file_times_submitted"   : 'times_submitted',

                "vt_file_pe_magic"          : ('additional_info', 'magic',),
                "vt_file_pe_pdb_string"     : ('additional_info', 'pe-debug', 
                                               lambda v: v.get('codeview', {}).get('name') if v.get('type_str') else None),
                "vt_file_positives"         : 'positives',
                "vt_file_sha256"            : 'sha256',
                "vt_file_permalink"         : 'permalink',

                "vt_file_exiftool_description": ('additional_info', 'exiftool', 'FileDescription',),
                "vt_file_exiftool_object_type": ('additional_info', 'exiftool', 'ObjectFileType',),

                "vt_file_pe_product"        : ('additional_info', 'sigcheck', 'product', ),
                "vt_file_pe_copyright"      : ('additional_info', 'sigcheck', 'copyright'),
                "vt_file_pe_original_name"  : ('additional_info', 'sigcheck', 'original name'),

                "vt_file_signature_signing_date"                : ('additional_info', 'sigcheck', 'signing date'),
                "vt_file_signature_description"                 : ('additional_info', 'sigcheck', 'description'),
                "vt_file_signature_signers"                     : ('additional_info', 'sigcheck', 'signers'),
                "vt_file_signature_signers_thumbprints"         : ('additional_info', 'sigcheck', 'counter signers details', 
                                                                   lambda v: ';'.join([s.get('thumbprint', '') for s in v])),
                "vt_file_signature_verified"                    : ('additional_info', 'sigcheck', 'verified'),
                "vt_file_signature_counter_signers"             : ('additional_info', 'sigcheck', 'counter signers'),
                "vt_file_signature_counter_signers_thumbprints" : ('additional_info', 'sigcheck', 'counter signers details', 
                                                                   lambda v: ';'.join([s.get('thumbprint', '') for s in v])),

                "vt_file_is_catalog_signed" : ('additional_info', 'sigcheck', 'signers details', checkTrustedVerdicts),
            },
        },
    },
}
