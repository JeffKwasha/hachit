"""
Flask api for Hachit.
- Simply asks Doc for an instance from the url path,
  then queries, that instance and returns the jsonified response data
"""

from werkzeug.exceptions import BadRequest
from flask import Blueprint, request
from doc import Doc
from pprint import pformat
from datetime import datetime, date
import json

#from config import Config
#logger = Config.getLogger(__name__)

bp = Blueprint('api', __name__)


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
    return json.dumps(rv, default=lambda v: v.isoformat() if type(v) in (datetime, date) else None)   # TODO I need to jsonify dates, but not the way jsonify does it.

