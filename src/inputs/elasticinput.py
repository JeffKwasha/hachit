# https://github.com/elastic/elasticsearch-py
from elasticsearch import Elasticsearch, ConnectionTimeout, NotFoundError
from input import Input
from config import Config
from mapper import Mapper
from pprint import pformat
logger = Config.getLogger(__name__)

class ElasticInput(Input):
    __slots__= []
    subtypes = ('elasticsearch', 'elastic')
    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)
        if type(self.data) is dict:
            self.data = Mapper(self.data)
        if type(self.location) is not str:
            self.location = Mapper(self.location)(kwargs)
        self.location = Elasticsearch(**self.location) # TODO url=self.location, ssl_context, http_auth


    def query(self, dic):
        assert(type(dic) is dict)
        # TODO this isn't a real elasticsearch query, it could be: returning the first(best) or only(non-ambiguous) result.
        try:
            rv = self.location.get(
                index=self.name,
                doc_type=self.name,
                id=dic.get(self.name),
                request_timeout=Config.get("ELASTIC_TIMEOUT", 1.0),
                ignore=404,
            )
        except ConnectionTimeout:
            logger.warning('Connection timeout querying: {} for {}'.format(self.name, dic))
            return default
        return rv.get('_source') or default

    def get(self, index, default={}):
        try:
            rv = self.location.get(index=self.name, doc_type=self.name, id=index, 
                                   request_timeout=Config.get("ELASTIC_TIMEOUT", 1.0), 
                                   ignore=404)
        except ConnectionTimeout:
            logger.error('Connection timeout querying: {} [{}]'.format(self.name, index))
            return default
        else:
            logger.info(pformat(rv))
        return rv.get('_source') or default

    def __getitem__(self, key):         return self.get(key)
#    def __iter__(self):                 return self.results.__iter__()
#    def __next__(self):                 return self.results.__next__()

ElasticInput.register()

