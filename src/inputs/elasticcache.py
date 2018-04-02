from datetime import datetime, timedelta
from pprint import pformat
from elasticsearch import ConnectionTimeout, NotFoundError
from inputs.elasticinput import ElasticInput
from config import Config
from utils import parse_duration
logger = Config.getLogger(__name__)

FuncType = type(lambda v:v)

def _ed_fn(expire_date, dic):
    if callable(expire_date):
        expire_date = expire_date(dic)
    val_t = type(expire_date)
    fn = _ed_map.get(val_t)
    if fn:
        return fn(expire_date, dic)
    return None

_ed_map = {
    int:       lambda ex_v, dic: datetime.utcnow() + timedelta(hours=ex_v),
    float:     lambda ex_v, dic: datetime.utcnow() + timedelta(hours=ex_v),
    tuple:     lambda ex_v, dic: datetime.utcnow() + timedelta(*ex_v),
    dict:      lambda ex_v, dic: datetime.utcnow() + timedelta(**ex_v),
    str:       lambda ex_v, dic: datetime.utcnow() + parse_duration(ex_v),
    timedelta: lambda ex_v, dic: datetime.utcnow() + ex_v,
    datetime:  lambda ex_v, dic: ex_v,
    FuncType:  _ed_fn,
}


class ElasticCache(ElasticInput):
    __slots__= ['count', 'expire_date']
    subtypes = ('elasticcache',)
    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)
        # create an index in elasticsearch, ignore status code 400 (index already exists)
        self.location.indices.create(index=self.name, request_timeout=1.0, ignore=400)

        # expire_date - a function(data) that returns the date this data should expire
        self.expire_date = kwargs.get('expire_date')

    def query(self, dic):
        rv = super().query(dic)
        expire = rv.get('EXPIRE_DATE')
        if expire and datetime.utcnow() > expire:
            return None
        return rv

    def get(self, index, default={}):
        rv = super().get(index, default)
        expire = rv.get('EXPIRE_DATE')
        if expire and datetime.utcnow() > expire:
            return None
        return rv

    def set(self, index, value):
        try:
            if self.expire_date:
                value['EXPIRE_DATE'] = _ed_fn(self.expire_date, value)
            rv = self.location.index(index=self.name, doc_type=self.name, id=index, body=value)
        except ConnectionTimeout:
            logger.warning('Connection timeout setting: {} [{}]'.format(self.name, index))

    def delete(self, index):
        rv = self.location.delete(index=self.name, doc_type=self.name, id=index)
        if rv['found']

    def expire(self):


    def __getitem__(self, key):         return self.get(key)
    def __setitem__(self, key, val):    return self.set(key, val)
#    def __iter__(self):                 return self.results.__iter__()
#    def __next__(self):                 return self.results.__next__()

ElasticCache.register()
