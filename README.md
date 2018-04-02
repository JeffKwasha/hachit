HACHIT: Hachit is an Aggregating Caching Hierarchical Information Tool
--------

Hachit is a data middleman that simplifies getting and massaging data from multiple sources.<br>
Hachit's RESTful API is defined by little python plugins that describe how data is retrieved and presented.

Table of Contents
- [Why](#why)
- [Is it Easy](#is-it-easy)
- [Plugins](#plugins)
- [Features](#features)
- [Installation](#installation)

## Why
Troublesome structured data provided by a 3rd party.<br>
Tons of duplicate queries made by an application you can't (or don't want to) change.<br>
Multiple source data is hard to obtain or aggregate in your use case.<br>
Maintenance of data client scripts is itself a problem?

With Hachit you can build a custom web api in minutes using simple declarative python data structures.<br>
Your API can combine data from multiple sources, cache the data in elasticsearch, and return it in whatever structure you like.
All your plugins live in one directory, so version control is easy. 
You can even import data from another plugin, to tweak the structure, enrich the data with other sources, or perform additional processing!

## Is it Easy?
Hachit is written in Python 3 and uses [Flask](http://flask.pocoo.org/) and [Requests](http://docs.python-requests.org/en/master/).<br>
Hachit's elasticcache plugin requires [elasticsearch-py](http://docs.python-requests.org/en/master/) and connects to an elasticsearch instance on localhost.<br>
For test or one-off purposes you can run it with `cd hachit/src; python3 flask_app.py`<br>
For production you'll probably want a performant webserver like nginx + gunicorn or uwsgi.<br>
Point your wsgi compatible server at `src/flask_app.py:app`

Presently there's not much to configure, but in the future Hachit will take its configuration from /etc/hachit/hachit.yaml

Once it works you just need to define your 'document types' with plugins.

## Plugins
A Plugin defines a 'Doc' (think ElasticSearch Document Type).
It has a **name** which becomes its API path, and it defines one or more **inputs** and optionally a **cache**.
Inputs can have a 'data' parameter that describes how to present the retrieved data.

```python
from datetime import datetime

def counter(*_):
    global count
    try:
        count += 1
    except:
        count = 1
    return count

doc={'name':'whitelist',	# a Doc's name is it's api path.
    'inputs': {             # Here we use a dict to define a single input.
        'type': 'csv'       # currently HACHIT supports 'REST'ful web apis and 'csv' files
        
        # a unique name is required. This prevents duplicates and allows re-use
        'name' : 'whitelist_csv',   
       
        # location contains all the data needed to access the input. 
        'location' : 'whitelist.csv',  # whitelist.csv will be found in the same directory as this plugin file
        
        # id - a record's unique identifier.
        'id':'hash',

        # 'data' uses a 'Mapper' to massage our csv's fields into common fields in this 'Doc'
        'data': {
            #REMAP instructs the Mapper to make output fields directly from inputs
            'REMAP': {      # Our input data arrives as tuples, which are indexed, so...
                'name': 0,  # output a 'name' field taken from column 0
                'hash': 1,  # output a 'hash' field taken from column 1 NOTE: this CREATES the 'id'
                'comment': 3,
                'date.created': 2,  
                },
            # 'normal' fields are simply added to the result
            'from_whitelist.csv': True,
            'counter': counter,                                 # THIS, IS, PYTHON
            'date.retrieved': lambda v: str(datetime.utcnow()), # yes, we can
            },
    },
    cache=None,
}
```
We can now make requests to '/whitelist' by providing a hash.

`> curl localhost:5000/whitelist?hash=41e25e514d90e9c8bc570484dbaff62b`<br>
Returns:
```
{
  "comment": "Found in HKLM\\SYSTEM\\CurrentControlSet\\Control\\SafeBoot\\AlternateShell.",
  "date.created": "2018-02-20T11:23:00Z",
  "from_whitelist.csv": True,
  "hash": "41e25e514d90e9c8bc570484dbaff62b",
  "name": "cmd.exe",
  "date.retrieved": '2018-03-21 18:52:18.633003',
  "counter": 1,
}
```
## Features
* Simple, copy-paste friendly syntax
* Retrieve and combine multiple data sources easily
* Caches upstream API usage

## Installation
1. Install and start ElasticSearch
1. Install python3.6 or newer
1. Install required modules: `pip install flask requests pyaml`
1. Test hachit `python3.6 flask_app.py` (hachit runs a few basic tests as it loads)

To really improve things, use a real webserver stack like nginx + gunicorn:

Install python 3.6 or newer:
https://danieleriksson.net/2017/02/08/how-to-install-latest-python-on-centos/
```
sudo yum install -y gcc zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel expat-devel
./configure --prefix=/usr/local --enable-shared  --enable-optimizations LDFLAGS="-Wl,-rpath /usr/local/lib"
make -j
sudo make altinstall
```

```
python3.6 -m venv $HOME/venv 
. ~/venv/bin/activate
pip install -U pip
pip install gunicorn
pip install flask requests
```

