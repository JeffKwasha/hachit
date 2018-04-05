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
        'name': 'api_input_test', # I just need it to be unique
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
    }
    urlin = Input(**d)
    rv = urlin.get(1)
    return search(('reqres_ids', 'name'), rv) == "George Bluth"

# vim ts=4 sw=4
