# This hachit plugin defines the API for VirusTotal file hash data

# md5sum cmd.exe: 41e25e514d90e9c8bc570484dbaff62b
from secrets import VT_API_KEY
TrustedMSRootThumbprints = [ 'foo' ] #[ l for l in open(os.path.join(Config[PLUGIN_DIR],'TrustedMSRootThumbprints.list'))]

def checkTrustedVerdicts(dic):
    v = [True for d in dic if d.get('status')]
    l = [True for d in dic if d.get('thumbprint') in TrustedMSRootThumbprints]
    if l and len(v) == len(dic):
       return 'Valid signatures chained to a trusted Microsoft cert'

def find_type_str(li):
    for i in li:
        if i.get('codeview'):
            return i

doc={
    'name':'file_hash_md5',
    'id': 'hash',
    'inputs':   {
        'type': 'REST',
        'name': 'vt_file_hash',
        'location' : {
            'url': 'https://www.virustotal.com/vtapi/v2/file/report',
            'params': {
                'apikey' : VT_API_KEY,
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
                ## need TrustedMSRootThumbprints !!!!
                "vt_file_scan_date"         : 'scan_date',
                "vt_file_first_seen"        : 'first_seen',
                "vt_file_last_seen"         : 'last_seen',
                "vt_file_times_submitted"   : 'times_submitted',

                "vt_file_pe_magic"          : ('additional_info', 'magic',),
                "vt_file_pe_pdb_string"     : ('additional_info', 'pe-debug', find_type_str, 'codeview', 'name'),
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

                "vt_file_is_catalog_signed" : ('additional_info','trusted_verdicts', checkTrustedVerdicts),
            },
            'from_vt_md5': True,
            #'an_output_field' : 'anything you like',
            #'output_field_2' : ('additional_info', 'exiftool', lambda v: v.get('foo') is 'France'),
            #'magic_field' : lambda v: v.get('vt_file_scan_date') and v.get('vt_file_positives') < 5,
        },
    },
    'cache':{
        'type': 'elasticcache',
        'location': 'localhost',
    },
}