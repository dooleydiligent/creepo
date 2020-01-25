from flask import Blueprint
from flask import request
from flask.helpers import send_from_directory

import os

bp = Blueprint("ui", __name__, url_prefix='/ui', static_folder='ui'   )

@bp.route("/")
def index():
    """Show the creepo ui."""
#    exists = "Getting {url} from {static}".format(url=request.url, static=bp.static_folder)
#    exists = 'exists is {exists}'.format(exists=os.path.isfile(os.path.join('/home/lane/git/creepo-py/creepo/ui', 'ui.html')))
    # return make_response(exists)
    static_folder = bp.static_folder
#    print('bp.static_folder={fldr}'.format(fldr=static_folder))
    return send_from_directory(static_folder, 'ui.html')

