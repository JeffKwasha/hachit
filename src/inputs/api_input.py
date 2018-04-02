## WebApi
import requests
from mapper import Mapper
from input import Input, h_logger, l_logger
from utils import search, search_all
from datetime import datetime

def count_reset_monthly(self):
    try:
        if self.last_query_date.month != datetime.utcnow().month:
            self.count = 0
            self.last_query_date = datetime.utcnow()
    except: pass

class ApiInput(Input):
    subtypes=('REST')
    __slots__= ['count', 'query_limit', 'last_query_date', 'count_reset_func'] # TODO - Do we need a countable query parent?
    def __init__(self, **kwargs):
        if not hasattr(self, 'location'):
            super().__init__(**kwargs)
            self.location = Mapper(self.location)
            self.data = Mapper(self.data)
            self.count_reset_func = kwargs.get('count_reset_func')
            self.query_limit = kwargs.get('query_limit')
            if self.query_limit:
                self.count = 0
                if self.count_reset_func and not callable(self.count_reset_func):
                    raise Exception('{} count_reset_func must be a function that resets the count'.format(self.name))
                elif type(self.query_limit) is not int:
                    raise Exception('{} query_limit must be an integer, the maximum number of allowed queries'.format(self.name))
                else:
                    from types import MethodType
                    self.count_reset_func = MethodType(self.count_reset_func, self)
                pass
            pass
        pass

    def get(self, index):
        return self.query({self.id_name: index})

    def query(self, args):
        """get the needed headers / arguments by running location mapper on our arguments"""
        assert(type(self.location) is Mapper)
        assert(type(self.data) is Mapper)
        if self.query_limit:
            self.count_reset_func()
            if self.count > self.query_limit:
                raise Exception("{} Exceeded Limit: {}/{}".format(self.name, self.count, self.query_limit))
                pass
            pass
        args.update({'name':self.name, 'id':self.id_name,})
        l = self.location(args)
        r = requests.get(l.get('url'), headers=l.get('headers'), params=l.get('params')) # TODO, authentication support, cookies?

        if r.status_code != 200:
            errors = {
                403: "{}: Forbidden - did you specify the right parameters?".format(self.name),
                404: "{}: File not found... ?".format(self.name),
                500: "{}: Permanent failure".format(self.name),
            }
            error = "{} request to {} failed".format(self.name, l.get('url'))
            if 'errors' in l:
                error = l['errors'].get(r.status_code)
                h_logger.error(error)
            else:
                error = errors.get(r.status_code)
            return "Error: {}".format(error)
        elif self.query_limit:
            self.last_query_date = datetime.utcnow()
            self.count += 1

        tmp = r.json()
        if not tmp:
            return {}
        # convert result into our 'common' fields using our Mapper 'data'
        return self.data(tmp)

    @classmethod
    def validate(cls, dic, errors=None):
        try:
            return 100 if dic.get('location')['url'][:4] == 'http' else False
        except KeyError: pass
        except IndexError: pass
        except TypeError: pass
        errors[cls.__name__]="Expected a url in location: { location: { url: 'http... "
        return False

ApiInput.register()

def _test():
    d = {
        'type': 'REST',
        'name': 'api_input_test',
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
                ## need TrustedMSRootThumbprints !!!!
                "vt_file_scan_date"         : 'scan_date',
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

                "vt_file_is_catalog_signed" : ('additional_info', 'sigcheck', 'signers details', lambda v: v),
            },
        },
    }
    urlin = Input(**d)
    rv = urlin.get('41e25e514d90e9c8bc570484dbaff62b')
    return rv['vt_file_sha256'] == 'e6c49f7ce186dc4c9da2c393469b070c0f1b95a01d281ae2b89538da453d1583'

"""
{'scans': {
    'Bkav': {'detected': False, 'version': '1.3.0.9466', 'result': None, 'update': '20180228'},
    'MicroWorld-eScan': {'detected': False, 'version': '14.0.297.0', 'result': None, 'update': '20180228'},
    'nProtect': {'detected': False, 'version': '2018-02-28.03', 'result': None, 'update': '20180228'},
    'CMC': {'detected': False, 'version': '1.1.0.977', 'result': None, 'update': '20180228'},
    'CAT-QuickHeal': {'detected': False, 'version': '14.00', 'result': None, 'update': '20180228'},
    'McAfee': {'detected': False, 'version': '6.0.6.653', 'result': None, 'update': '20180228'},
    'Cylance': {'detected': False, 'version': '2.3.1.101', 'result': None, 'update': '20180228'},
    'VIPRE': {'detected': False, 'version': '64932', 'result': None, 'update': '20180228'},
    'SUPERAntiSpyware': {'detected': False, 'version': '5.6.0.1032', 'result': None, 'update': '20180228'},
    'TheHacker': {'detected': False, 'version': '6.8.0.5.2451', 'result': None, 'update': '20180225'},
    'K7GW': {'detected': False, 'version': '10.40.26354', 'result': None, 'update': '20180228'},
    'K7AntiVirus': {'detected': False, 'version': '10.40.26356', 'result': None, 'update': '20180228'},
    'TrendMicro': {'detected': False, 'version': '9.862.0.1074', 'result': None, 'update': '20180228'},
    'Baidu': {'detected': False, 'version': '1.0.0.2', 'result': None, 'update': '20180227'},
    'F-Prot': {'detected': False, 'version': '4.7.1.166', 'result': None, 'update': '20180228'},
    'Symantec': {'detected': False, 'version': '1.5.0.0', 'result': None, 'update': '20180228'},
    'TotalDefense': {'detected': False, 'version': '37.1.62.1', 'result': None, 'update': '20180228'},
    'TrendMicro-HouseCall': {'detected': False, 'version': '9.950.0.1006', 'result': None, 'update': '20180228'},
    'Avast': {'detected': False, 'version': '18.1.3800.0', 'result': None, 'update': '20180228'},
    'ClamAV': {'detected': False, 'version': '0.99.2.0', 'result': None, 'update': '20180228'},
    'Kaspersky': {'detected': False, 'version': '15.0.1.13', 'result': None, 'update': '20180228'},
    'BitDefender': {'detected': False, 'version': '7.2', 'result': None, 'update': '20180228'},
    'NANO-Antivirus': {'detected': False, 'version': '1.0.100.21498', 'result': None, 'update': '20180228'},
    'Paloalto': {'detected': False, 'version': '1.0', 'result': None, 'update': '20180228'},
    'AegisLab': {'detected': False, 'version': '4.2', 'result': None, 'update': '20180228'},
    'Tencent': {'detected': False, 'version': '1.0.0.1', 'result': None, 'update': '20180228'},
    'Ad-Aware': {'detected': False, 'version': '3.0.3.1010', 'result': None, 'update': '20180228'},
    'Sophos': {'detected': False, 'version': '4.98.0', 'result': None, 'update': '20180228'},
    'Comodo': {'detected': False, 'version': '28603', 'result': None, 'update': '20180228'},
    'F-Secure': {'detected': False, 'version': '11.0.19100.45', 'result': None, 'update': '20180228'},
    'DrWeb': {'detected': False, 'version': '7.0.28.2020', 'result': None, 'update': '20180228'},
    'Zillya': {'detected': False, 'version': '2.0.0.3502', 'result': None, 'update': '20180228'},
    'Invincea': {'detected': False, 'version': '6.3.4.26036', 'result': None, 'update': '20180121'},
    'McAfee-GW-Edition': {'detected': False, 'version': 'v2015', 'result': None, 'update': '20180228'},
    'Emsisoft': {'detected': False, 'version': '4.0.2.899', 'result': None, 'update': '20180228'},
    'Ikarus': {'detected': False, 'version': '0.1.5.2', 'result': None, 'update': '20180228'},
    'Cyren': {'detected': False, 'version': '5.4.30.7', 'result': None, 'update': '20180228'},
    'Jiangmin': {'detected': False, 'version': '16.0.100', 'result': None, 'update': '20180228'},
    'Webroot': {'detected': False, 'version': '1.0.0.207', 'result': None, 'update': '20180228'},
    'Avira': {'detected': False, 'version': '8.3.3.6', 'result': None, 'update': '20180228'},
    'Fortinet': {'detected': False, 'version': '5.4.247.0', 'result': None, 'update': '20180228'},
    'Antiy-AVL': {'detected': False, 'version': '3.0.0.1', 'result': None, 'update': '20180228'},
    'Kingsoft': {'detected': False, 'version': '2013.8.14.323', 'result': None, 'update': '20180228'},
    'Endgame': {'detected': False, 'version': '2.0.0', 'result': None, 'update': '20180228'},
    'Arcabit': {'detected': False, 'version': '1.0.0.830', 'result': None, 'update': '20180228'},
    'ViRobot': {'detected': False, 'version': '2014.3.20.0', 'result': None, 'update': '20180228'},
    'ZoneAlarm': {'detected': False, 'version': '1.0', 'result': None, 'update': '20180228'},
    'Avast-Mobile': {'detected': False, 'version': '180228-06', 'result': None, 'update': '20180228'},
    'Microsoft': {'detected': False, 'version': '1.1.14500.5', 'result': None, 'update': '20180228'},
    'AhnLab-V3': {'detected': False, 'version': '3.12.0.20130', 'result': None, 'update': '20180228'},
'ALYac': {'detected': False, 'version': '1.1.1.5', 'result': None, 'update': '20180228'},
'AVware': {'detected': False, 'version': '1.5.0.42', 'result': None, 'update': '20180228'},
'MAX': {'detected': False, 'version': '2017.11.15.1', 'result': None, 'update': '20180228'},
'VBA32': {'detected': False, 'version': '3.12.28.0', 'result': None, 'update': '20180228'},
'Malwarebytes': {'detected': False, 'version': '2.1.1.1115', 'result': None, 'update': '20180228'},
'WhiteArmor': {'detected': False, 'version': None, 'result': None, 'update': '20180223'},
'Zoner': {'detected': False, 'version': '1.0', 'result': None, 'update': '20180228'},
'ESET-NOD32': {'detected': False, 'version': '16980', 'result': None, 'update': '20180228'},
'Rising': {'detected': False, 'version': '25.0.0.1', 'result': None, 'update': '20180228'},
'Yandex': {'detected': False, 'version': '5.5.1.3', 'result': None, 'update': '20180228'},
'SentinelOne': {'detected': False, 'version': '1.0.15.206', 'result': None, 'update': '20180225'},
'eGambit': {'detected': False, 'version': 'v4.3.5', 'result': None, 'update': '20180228'},
'GData': {'detected': False, 'version': 'A:25.16176B:25.11692', 'result': None, 'update': '20180228'},
'AVG': {'detected': False, 'version': '18.1.3800.0', 'result': None, 'update': '20180228'},
'Cybereason': {'detected': False, 'version': '1.2.27', 'result': None, 'update': '20180225'},
'Panda': {'detected': False, 'version': '4.6.4.2', 'result': None, 'update': '20180228'},
'CrowdStrike': {'detected': False, 'version': '1.0', 'result': None, 'update': '20170201'},
'Qihoo-360': {'detected': False, 'version': '1.0.0.1120', 'result': None, 'update': '20180228'}},
'scan_id': 'e6c49f7ce186dc4c9da2c393469b070c0f1b95a01d281ae2b89538da453d1583-1519852821',
'sha1': '9d41d484b79570b3040909689259d52b24bf6d21',
'resource': '41e25e514d90e9c8bc570484dbaff62b',
'response_code': 1,
'scan_date': '2018-02-28 21:20:21',
'permalink': 'https://www.virustotal.com/file/e6c49f7ce186dc4c9da2c393469b070c0f1b95a01d281ae2b89538da453d1583/analysis/1519852821/',
'verbose_msg': 'Scan finished, information embedded',
'total': 68,
'positives': 0,
'sha256': 'e6c49f7ce186dc4c9da2c393469b070c0f1b95a01d281ae2b89538da453d1583',
'md5': '41e25e514d90e9c8bc570484dbaff62b'}
"""
#
#params = {
#    'apikey': '8696a0eb1dedb279b266b319a3cd7b304b3f25a4e9cf173ca3bffebb9dceb556',
#    'resource': 'a8fd9222e4d72596bb37da8be95c0ba4',
#    'allinfo': 1
#}
## 'c1ce0d366721e43fd0c4f983da408feb79a2db54e164d47346691e9c9b575aa3', 

#           'remap': {
#               'hash' : lambda v: v[1],
#               'name' : lambda v: v[0],
#               'date_created' : lambda v: v[2],
#               'comment' : lambda v: v[3],
#           },
#WebApi.register()
# vim ts=4 sw=4
