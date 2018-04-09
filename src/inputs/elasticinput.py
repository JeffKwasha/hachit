# https://github.com/elastic/elasticsearch-py
from pprint import pformat
from elasticsearch import Elasticsearch, ConnectionTimeout, NotFoundError, ImproperlyConfigured, ConnectionError, TransportError
from input import Input
from exceptions import NotFound
from mapper import Mapper
from config import Config
logger = Config.getLogger(__name__)

import logging
logging.getLogger('elasticsearch').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

class ElasticInput(Input):
    __slots__= []
    subtypes = ('elasticsearch', 'elastic')
    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)
        if type(self.data) is dict:
            self.data = Mapper(self.data)
        if type(self.location) is not str:
            self.location = Mapper(self.location)(kwargs)
        try:
            es = Elasticsearch(**self.location, request_timeout=0.2, retries=False, ignore=404) # TODO url=self.location, ssl_context, http_auth
            es.info()
            self.location = es
        except ImproperlyConfigured as e:
            raise NotFound("ElasticSearch rejected {}\n-----\n\t{}".format(pformat(self.location),e))
        except TransportError as e:
            raise NotFound("Failed to reach ElasticSearch at {}\n-----\n\t{}".format(pformat(self.location),e.error))
        except:
            raise NotFound("Unable to connect to ElasticSearch at host:{}".format(self.location.get('host')))

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

