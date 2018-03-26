# https://github.com/elastic/elasticsearch-py
from datetime import datetime
from elasticsearch import Elasticsearch, ConnectionTimeout, NotFoundError
from input import Input
from config import Config
from pprint import pformat
logger = Config.getLogger(__name__)

class ElasticCache(Input):
    __slots__= ['count', 'query_limit', 'last_query_date', 'count_reset_func']
    subtypes = ('elasticcache',)
    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)
        # location
        # create an index in elasticsearch, ignore status code 400 (index already exists)
        # by default we connect to localhost:9200
        self.location = Elasticsearch(hosts=self.location) # TODO url=self.location, ssl_context, http_auth
        self.location.indices.create(index=self.name, request_timeout=1.0, ignore=400)

    def query(self, dic):
        assert(type(dic) is dict)
        # TODO this isn't a real elasticsearch query, it could be: returning the first(best) or only(non-ambiguous) result.
        try:
            rv = self.location.get(
                index=self.name,
                doc_type=self.name,
                id=dic.get(self.name),
                request_timeout=Config.get("ELASTICACHE_TIMEOUT", 1.0),
                ignore=404,
            )
        except ConnectionTimeout:
            logger.warning('Connection timeout querying: {} for {}'.format(self.name, dic))
            return default
        return rv.get('_source') or default

    def get(self, index, default={}):
        try:
            rv = self.location.get(index=self.name, doc_type=self.name, id=index, 
                                   request_timeout=Config.get("ELASTICACHE_TIMEOUT", 1.0), 
                                   ignore=404)
        except ConnectionTimeout:
            logger.error('Connection timeout querying: {} [{}]'.format(self.name, index))
            return default
        else:
            logger.info(pformat(rv))
        return rv.get('_source') or default

    def set(self, index, value):
        try:
            #self.location.delete(index=self.name, doc_type=self.name, id=index)
            rv = self.location.index(index=self.name, doc_type=self.name, id=index, body=value)
        except ConnectionTimeout:
            logger.warning('Connection timeout setting: {} [{}]'.format(self.name, index))

    def __getitem__(self, key):         return self.get(key)
    def __setitem__(self, key, val):    return self.set(key, val)
#    def __iter__(self):                 return self.results.__iter__()
#    def __next__(self):                 return self.results.__next__()

ElasticCache.register()
