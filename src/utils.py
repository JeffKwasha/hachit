from datetime import datetime, timedelta
from fcntl import flock, LOCK_EX, LOCK_NB
from collections import OrderedDict, Mapping, namedtuple
from socket import inet_pton, AF_INET6, AF_INET, error as SocketError
import os
import yaml
import re
import logging

logging.basicConfig()
logger = logging.getLogger()

# types appears deprecated. make our own
NoneType = type(None)
FuncType = type(lambda v: v)

FreeSpace = namedtuple('FreeSpace', ['bytes', 'nodes'] )
ISOFORMAT = '%Y-%m-%dT%H:%M:%SZ'


try:
    basestring
    def is_str(s):
        return isinstance(s, basestring)
except NameError:
    def is_str(s):
        return isinstance(s, str)


DURATIONS= {'US': 0.000001,
            'MS': 0.001,
            'S' : 1,
            'M' : 60, 
            'H' : 60*60,
            'D' : 60*60*24,
            'W' : 60*60*24*7, }
RX_DURATION = re.compile(r'|'.join([r'(?:(?P<{}>[\d.]+)\s*'
                                    r'(?:{}|{}))'.format(k, k, k.lower())
                                    for k,v in DURATIONS.items()]))
def parse_duration(s):
    total = 0
    if type(s) in (int, float):
        total, s = s, ''
    elif not is_str(s):
        return None
    for it in RX_DURATION.finditer(s):
        for k,v in it.groupdict().items():
            if v:
                total += DURATIONS[k] * float(v)
    return timedelta(seconds=total or float(s))


CAPACITIES = {'B': 1,
              'KB':1024, 
              'MB':1024**2, 
              'GB':1024**3,
              'TB':1024**4,
              'PB':1024**5, }
RX_CAPACITY = re.compile(r'|'.join([r'(?:(?P<{}>[\d.]+)\s*'
                                    r'(?:{}|{}))'.format(k, k, k.lower())
                                    for k,v in CAPACITIES.items()]))
def parse_capacity(s):
    total = 0
    if type(s) in (int, float):
        return int(s)
    elif not is_str(s):
        return None
    for it in RX_CAPACITY.finditer(s):
        for k,v in it.groupdict().items():
            if v:
                total += CAPACITIES[k] * float(v)
    return total or int(s)

def epoch(when):
    return int((when - datetime(1970,1,1)).total_seconds())

def from_epoch(epoch):
    return datetime(1970,1,1) + timedelta(seconds=epoch)

def readdir(path, startswith=None, endswith=None):
    files = []
    for i in os.listdir(path):
        if i[0] == '.':
            continue
        if endswith and not i.endswith(endswith):
            continue
        if startswith and not i.startswith(startswith):
            continue
        file_path = os.path.join(path, i)
        stats = os.stat(file_path)
        if stats.st_size < 1:
            continue
        files.append(i)
    return files

def file_modified(path, format=None):
    """ return the modified datetime of the file at path
        if format is specified - use strftime and return a string instead
    """
    t = from_epoch(os.path.getmtime(path))
    if format:
        return t.strftime(format)
    return t

def is_sequence(arg):
    return not is_str(arg) and (
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__")
    )

def is_dict(arg):
    return (hasattr(arg, '__getitem__') and
            hasattr(arg, '__setitem__') and
            hasattr(arg, 'keys') and
            hasattr(arg, 'values')
           )

_merge_types = {
    str: lambda a, b: {a, b},
    int: lambda a, b: {a, b},
    float: lambda a, b: {a, b},
    list: lambda a, b: merge_lists(a,b),
    set: lambda a,b: merge_sets(a,b),
    dict: lambda a,b: merge_dicts(a,b),
}
def merge_dicts(a, b):
    rv = {}
    for k in set(a) | set(b):
        ak = a.get(k)
        bk = b.get(k)
        ak_t = type(ak)
        bk_t = type(bk)
        if ak and bk:
            func = _merge_types.get(ak)
            if dict in (ak_t, bk_t):
                rv[k] = merge_dicts(ak, bk)
            elif list in (ak_t, bk_t):
                rv[k] = merge_lists(ak, bk)
            else:
                func = _merge_types.get(ak)
                rv[k] = func(ak, bk)
        else:
            rv[k] = ak or bk
    return rv

def merge(a, b):
    func = _merge_types(type(a), type(b))
    if func: 
        return func(a, b)
    else:
        logger.info("Couldn't merge: {}/{}".format(type(a), type(b)))

def eval_field(dst, src, args):
    """ Programming is just recursion with different lambda functions 
        here we focus on simple value assignment
    """
    src_t = type(src)
    if src_t is FuncType:
        return src(args)
    if src_t is dict:
        for k,v in src.items():
            dst[k] = eval_field({}, v, args)
        return dst
    if src_t is list:
        return [ eval_field(dst, i, args) for i in src ]
    if src_t in (str, int, float, bytes, tuple):
        return src
    return dst

def searchStr(needle, haystack):
    # str : (lambda k,v: v.get(k) if type(v) is dict else v.index(k)),
    haytype = type(haystack)
    if haytype is dict:
        return haystack.get(needle)
    elif haytype in (list, tuple):
        raise ValueError("Don't use a string '{}', to index a list: {} ".format(needle, haystack))
    elif isinstance(haystack, tuple):
        # haystack is_not tuple, but isinstance, therefore namedtuple
        return getattr(haystack, needle, None)

def search_all(needle, *haystacks):
    from copy import copy
    haystack = copy(haystacks[0])
    for i in haystacks[1:]: haystack.update(i)
    return search(needle, haystack)

def search(needle, haystack):
    from mapper import Mapper
    types = {
        str: searchStr,
        int: searchInt,
        dict: searchDict,
        tuple: searchTuple,
    }

    logger.debug("search: {} in {}".format(needle, haystack))
    ndl_t = type(needle)
    try:
        t = types[ndl_t]
        logger.debug("search: {}({}) on {}".format(t, needle,haystack))
        return t(needle, haystack)
    except KeyError:
        if callable(needle):
            return needle(haystack)
        elif isinstance(needle, tuple):
            # needle is a special tuple, a namedtuple
            logger.debug("search: {}({}) on {}".format(t, needle,haystack))
            return searchNamedTuple(needle, haystack)

def searchNamedTuple(needle, haystack):
    logger.error("I haven't implemented namedtuples yet. They can't easily be specified.")
    pass

def searchInt(needle, haystack):
    """ needle is an Int. Haystack better be iterable """
    try:
        return haystack[needle]
    except IndexError:
        return None

def searchFunction(func, haystack):
    """ an almost useless wrapper around a function """
    logger.debug("searchFunction {}( {} )".format(func, haystack))
    return func(haystack)

def searchTuple(needle, haystack):
    """ needle is a iterable of haystack's progeny ie: needle=('a', 'b', 'c'), haystack={ 'a' : { 'b' : { 'c' : "RETURN VAL" }}}
        return a value or None
    """
    assert(type(needle) is tuple)
    current = haystack
    for n in needle:
        if None in (n, current):
            break

        curr_t = type(current)
        ndl_t = type(n)

        if ndl_t not in (int, str):
            current = search(n, current)
        elif curr_t in (list, tuple):
            if ndl_t is int and n < len(current):
                current = current[n]
            else:
                return None
        elif curr_t is dict:
            current = current.get(n, None)
    
    if needle[-1] == n:
        return current
    return None

def searchDict(needle, haystack):
    rv = {}
    for k,v in needle.items():
        rv[k] = search(v, haystack)
    return rv

def recurse_update(a, b, ignore_none = False):
    """ add everything in b to a
        _overwrites_ existing values unless the new value is None and ignore_none is True
        you might think deepcopy for this, but it can't merge two dictionaries
    """
    for key,bVal in b.items():
        if isinstance(bVal, Mapping):
            if (ignore_none):
                a[key] = recurse_update(a.get(key, {}), {k:v for k,v in bVal.items() if v}, True)
            else:
                a[key] = recurse_update(a.get(key, {}), bVal)
        elif is_sequence(bVal):
            if not is_sequence(a[key]):
                a[key] = bVal if a[key] in bVal else bVal.append(a[key])
            else:
                a[key].extend([v for v in bVal if v not in a[key] ])
        else:
            a[key] = bVal if bVal or not ignore_none else a[key]
    return a

def file_lock(f, timeout=2):
    """ True if f was locked, False otherwise """
    giveUp = datetime.utcnow() + timedelta(seconds=timeout)
    while datetime.utcnow() < giveUp:
        try:
            flock(f, LOCK_EX | LOCK_NB)
            return True
        except IOError as e:
            if e.errno == errno.EAGAIN:
                time.sleep(0.1)
    return False

def update_yaml(path, val = None):
    """ given a path to a yaml file:
            if val: update val from the file, update the file, and return val.
            else:   load the file and return that.
        returns
            False - locking failed, no update occurred
            new value - File data, updated with provided value
    """
    if not path:
        return False
    locked = False

    with open(path, 'a+b') as f:
        if not file_lock(f, timeout=1):
            logger.error("Failed to lock {}".format(path))
            return False

        f.seek(0)
        data = f.read()
        if len(data):
            tmp = yaml.load(data)
            if not val:
                logger.debug("loaded {}".format(path))
                # No changes to write.
                return tmp
            elif hasattr(tmp, 'update'):
                logger.debug("{}.update( {} )".format(tmp,val))
                tmp.update(val)
            elif hasattr(val, '__add__'):
                logger.debug("{} += {}".format(val,tmp))
                val += tmp
            else:
                logger.error("loaded {}, can't update {}".format(path,val))
                return val

        f.seek(0)
        f.truncate()
        f.write(yaml.dump(val))
    return val

def write_yaml(path, val):
    """ Once a file lock is obtained, path is overwritten with yaml encoded contents of val
    """
    if not path or val is None:
        return False
    # Even though we're just 'writing' the file, I don't want to clobber it until I get a lock
    # so I open it for append
    with open(path, 'a+b') as f:
        if not file_lock(f, timeout=2):
            logger.error("Failed to lock {}".format(path))
            return False

        f.seek(0)
        f.truncate()
        f.write(yaml.dump(val))
        return True

def free_space(f):
    """ return ( Bytes Free, Nodes free ) for the filesystem containing the provided file
        ex: free_space( open( '/tmp/nonexistant', 'w' ) ) -> ( bytes=123456789 , nodes=1234 )
    """
    vfs = os.fstatvfs(f.fileno())
    return FreeSpace(bytes = vfs.f_bavail * vfs.f_frsize, nodes = vfs.f_favail)

def space_low():
    space = spool_space()
    from config import Config
    if space.bytes < parse_capacity(Config.get('FREE_BYTES', '100MB')):
        return "Low on disk space: {} free".format(space.bytes)
    if space.nodes < Config.get('FREE_NODES', 100 ):
        return "Low on FileSystem Nodes: {} free".format(space.nodes)
    return False

def validate_ip(ip):
    """ return a tuple (string, AF_INET) for valid IP addresses
        raise an exception for bad addresses
    """
    try:
        if len(ip) > 51:
            raise ValueError("Unable to parse ip: {}".format(ip))
        version = AF_INET
        if ip.find(':') >= 0:
            version = AF_INET6
        inet_pton(version, ip)
    except SocketError:
        raise ValueError("Unable to parse ip: {}".format(ip))
    return (ip, version)

def validate_net(cidr):
    """ return a tuple (string, AF_INET) for 'IP/cidr' strings
        raise an exception if input is invalid
    """
    if not '/' in cidr:
        raise ValueError("Invalid net: {} Expects a CIDR IP/mask".format(cidr))

    ip, net = cidr.split('/')
    ip, version = validate_ip(ip)
    if version == AF_INET:
        count = 0
        for i in net.split('.'):
            if 0 <= int(i) < 256:
                count += 1
        if count == 1 and int(i) <= 32:
            return (cidr, version)
        if count == 4:
            return (cidr, version)
        raise ValueError("Invalid IPv4 netmask {}".format(net))
    elif not (re.match(r'\d+', net) and int(net) < 128):
        raise ValueError("Invalid IPv6 netmask: {}".format(net))
    return (cidr, version)

def multiple_replace(string, rep_dict):
    pattern = re.compile("|".join([re.escape(k) for k in rep_dict.keys()]), re.M)
    return pattern.sub(lambda x: rep_dict[x.group(0)], string)

def md5(val):
    from hashlib import md5
    m = md5()
    m.update(val)
    return m.hexdigest()

def sha256(val):
    from hashlib import sha256
    m = sha256()
    m.update(val)
    return m.hexdigest()

