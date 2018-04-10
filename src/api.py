"""
Flask api for Hachit.
- Simply asks Doc for an instance from the url path,
  then queries, that instance and returns the jsonified response data
"""

from werkzeug.exceptions import BadRequest
from flask import Blueprint, request
from doc import Doc
from pprint import pformat
from datetime import datetime, date, time
from config import Config
import json

#from config import Config
#logger = Config.getLogger(__name__)

bp = Blueprint('api', __name__)

def _isoformat(v): return v.isoformat()

_json_encoders = {
    date: _isoformat,
    time: _isoformat,
    datetime: lambda v: v.isoformat('T', 'seconds'),
}
def custom_json_encoder(d):
    fn = _json_encoders.get(type(d))
    if fn:
        return fn(d)
    raise TypeError("{} is not a datetime. I only do datetimes".format(d))

@bp.route('/<path:path>')
def query(path):
    # simple and it works
    src = None
    try:
        src = Doc.from_url(path)
    except ValueError as e:
        return "Error: <{}>".format(e)
    except BadRequest as e:
        return json.dumps({ "Error": "Bad Request <{}>".format(e) })
    if not src:
        return json.dumps([ "Error: Unknown API endpoint <{}>".format(path),
                         Doc.urls()])
    #logger.info(pformat(request.values))
    rv = src.query(request.values)
    #logger.info(pformat(rv))
    return json.dumps(rv, indent=Config.get("JSON_PRETTY"), default=custom_json_encoder)

