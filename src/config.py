from __future__ import print_function
# A central location for the config dictionary
#   started by flask_app
import yaml
import os
import sys
import logging
from utils import readdir, FuncType
from importlib import import_module, reload
from importlib.util import spec_from_file_location, module_from_spec

levels = {
    'debug'  :logging.DEBUG,
    'info'   :logging.INFO,
    'warn'   :logging.WARNING,
    'warning':logging.WARNING,
    'error'  :logging.ERROR,
    'crit'   :logging.CRITICAL,
}
log_level = lambda x: levels.get(x, logging.DEBUG) if type(x) is str else int(x)
SUCCESS = True

logger = None
# TODO  - API reload - rebuilds all sources from disk
# @bp.route("/_reload")
# def reload():

class Config:
    """ finds, loads, and provides access to config from FILENAME.yaml
        Verifies configuration default settings are uniform
        provides a uniform logging format
    """
    modules = {}
    formatter = None
    log_level = None
    file_handler = None
    cwd = os.path.abspath(os.getcwd())
    config = {
        'SECRET_KEY': 'CHANGE_THIS',        # overridden by environment
        'SESSION_COOKIE_NAME': 'HACHIT_COOKIE',
        'LOG_MSG_FORMAT': '[%(processName)-8s] %(message)s',
        'LOG_DATE_FORMAT': '%Y-%m-%dT%H:%M:%SZ',
        'LOG_DATE_UTC': True,
        'LOG_LEVEL': 'debug',
        'LOG_FILE_BACKUPS' : 7,
        'LOG_FILE_MSG_FORMAT': '%(asctime)s[%(processName)-8s] %(message)s',
        'LOG_FILE_DATE_FORMAT': '%Y%jT%H:%M:%S',
        'LOG_FILE_LEVEL': 'info',
        'PLUGIN_DIR': '../plugins',
        'INPUT_DIR': './inputs',    # probably shouldn't change INPUT_DIR, if you do, csv_input._test will lose track of white.csv
    }
    _default = config.copy()
    _redis = None


    #def off_load_module(cls, module_name):

    @classmethod
    def load(cls, filename=None, logger=None, env=None):
        """ Set Config from a yaml file:
            filename a config file: search for the file in several directories
        """

        import itertools
        root  = os.path.abspath(os.sep)
        paths = itertools.product(
            ( filename,                     # filename.yaml
            ),
            [ tuple(),                      # <empty> - filename can be any valid path
             (root, 'etc', 'hachit'),     # /etc/hachit/filename
             (root, 'etc',),             # /etc/filename
            ]
        )
        for f,p in paths:
            if not f:
                continue
            filepath = os.path.join(*(p + (f,)) )
            filepath = os.path.expandvars(filepath)
            if os.path.isfile(filepath):
                break
            elif os.path.isfile(filepath+'.yaml'):
                filepath += '.yaml'
                break
            print("Config: >{}< not found".format(filepath))
        else:
            filepath = filename

        # load the config file and update our class config data
        if filepath:
            with open(filepath) as f:
                cls.config.update(yaml.load(f.read()))
                print("Config: loaded >{}<".format(filepath))

        if type(env) is dict:
            cls.config.update(env)

        cls._setup_loggers()
        cls._setup_plugins()

        return cls.config

    @classmethod
    def _setup_plugins(cls):
        """ load all the plugins from our input and plugin directories. 
            Since these are configurable, they may not be 'valid' in our package.  Add them to our sys.path
        """
        import doc
        import input
        for path in cls.get('INPUT_DIR').split(os.pathsep) + cls.get('PLUGIN_DIR').split(os.pathsep):
            path = os.path.abspath(path)
          #  dir  = os.path.dirname(path)
          #  if dir not in sys.path: sys.path.append(dir)
            if os.path.isdir(path):
                #if path not in sys.path: sys.path.append(path)
                for filename in readdir(path, endswith='.py'):
                    cls.load_plugin(os.path.join(path, filename))
            elif os.path.isfile(path):
                dir = os.path.dirname(path)
                #if dir not in sys.path: sys.path.append(dir)
                #cls.load_plugin(os.path.basename(path))
                cls.load_plugin(path)

    @classmethod
    def load_plugin(cls, filename, package=None):
        """ Loads or reloads a plugin:
            load: finds the directory, chdir(dir), _load_module( module_name )
            reload: lookup filename, reload(module)

            using the private helper (_load_module)
        """
        if not os.path.isfile(filename):
            raise Exception("can't find <{}>".format(filename))
        global logger
        filename = os.path.abspath(filename)
        basename = os.path.basename(filename)
        module_name = package + '.' if package else ''
        module_name += os.path.splitext(basename)[0]
        logger.log(77,"load_plugin: <{}> as {}".format(filename, module_name))
        if basename == '__init__.py':
            return
        elif module_name in cls.modules:
            logger.info("reloading {}".format(filename))
            cls.modules[module_name] = reload(cls.modules[module_name])
        else:
            logger.info("loading {}".format(filename))
            if os.sep in filename:
                path = os.path.dirname(filename)
                logger.log(100,"chdir {}".format(path))
                os.chdir(path)
            try:
                cls.modules[module_name] = cls._load_module(module_name, filename)
            finally:
                logger.log(100,"chdir {}".format(cls.cwd))
                os.chdir(cls.cwd)
        return cls.modules[module_name]

    @classmethod
    def _load_module(cls, module_name, filepath):
        """ a helper function to make load_plugin pretty. Assumes 'module_name' is in sys.path"""
        global logger
        logger.log(44, 'pwd: {}'.format(os.getcwd()))
        spec = spec_from_file_location(module_name, filepath)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        if getattr(module, '_test', None) and ( type(module._test) is FuncType ):
            module._test_result = module._test()
            if module._test_result == SUCCESS:
                logger.info("Imported and tested {} from {}".format(module.__name__, module_name))
            else:
                logger.error("plugin {} from file {} failed its own test".format(module.__name__, module_name))
                return None
            pass
        else:
            logger.info("Imported {} from {}".format(module.__name__, module_name))

        if hasattr(module, 'doc'):
            from doc import Doc
            if type(module.doc) is not dict:
                raise ValueError("a plugin's 'doc' should be a dictionary")
            else:
                try:
                    Doc(**module.doc)
                except Exception as e:
                    logger.exception("Failed to load Doc from {}".format(filepath))
        return module

    @classmethod
    def _setup_loggers(cls, verbosity=0):
        cls.log_level = log_level(verbosity or cls.config['LOG_LEVEL'])
        cls.formatter = logging.Formatter(fmt=cls.config['LOG_MSG_FORMAT'],
                                          datefmt=cls.config['LOG_DATE_FORMAT'])

        logging.basicConfig(level=cls.log_level)  # I really need to figure out flask <-> logging

        handler = None
        if not cls.file_handler and cls.get('LOG_FILE', None):
            from logging.handlers import TimedRotatingFileHandler
            handler = TimedRotatingFileHandler(
                cls.config['LOG_FILE'],
                when='midnight',
                backupCount=cls.config['LOG_FILE_BACKUPS'],
                utc=cls.config['LOG_DATE_UTC']
            )
            file_fmt = logging.Formatter(fmt=cls.config['LOG_FILE_MSG_FORMAT'],
                                         datefmt=cls.config['LOG_FILE_DATE_FORMAT'])
            handler.setLevel(log_level(cls.config['LOG_FILE_LEVEL']))
            handler.setFormatter(file_fmt)
            cls.file_handler = handler
            logging.info("Logging to {}:{}".format(cls.config['LOG_FILE'], cls.config['LOG_FILE_LEVEL']))

        cls.logger = cls.getLogger()
        global logger
        logger = cls.logger

    @classmethod
    def getLogger(cls, name='root', level=None):
        rv = logging.getLogger(name)
        if level:
            cls.setdefault(name + "_LOG_LEVEL", level)
            rv.setLevel(cls.get(name + "_LOG_LEVEL"))
            #logger.addHandler(cls.file_handler)
        return rv 

    @classmethod
    def set_flask(cls, flask_app):
        if Config.get('SECRET_KEY').find('CHANGE_THIS') >= 0:
            global logger
            logger.warning('Insecure SECRET_KEY detected! Using a randomized key.')
            # this randomization breaks sessions, but we don't have any.
            import os
            flask_app.secret_key = os.urandom(57)

        flask_app.config.from_mapping(Config.config)
        cls.flask = flask_app


    @classmethod
    def _set(cls, key, default, minval=None):
        """ _set checks for consistent 'default' values and enforces minimum value """
        old = cls._default.get(key)
        if old is not None and old != default:  # find programmers providing conflicting defaults
            raise ValueError("Config [{}] - disagreement in defaults: {}:{}".format(key, old, default))
        if type(minval) in (int, float):
            if default < minval:
                raise ValueError("Config [{}] - default < minval: {}:{}".format(key, default, minval))
        cls._default[key] = default
        if not key in cls.config:
            cls.config[key] = default
        elif type(minval) in (int, float):
            cls.config[key] = max(minval, cls.config[key])

    @classmethod
    def setdefault(cls, key, default, minval=None):
        cls._set(key, default, minval)
        return cls.config[key]

    @classmethod
    def get(cls, key, default=None, minval=None):
        if default is not None:
            return cls.setdefault(key, default, minval)
        if type(minval) in (int, float):
            cls.config[key] = max(cls.config.get(key), minval)
        return cls.config.get(key)
