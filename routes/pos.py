from flask import Blueprint, render_template
from decorators import login_required

bp = Blueprint('pos', __name__, url_prefix='/pos')

@bp.route('/')
@login_required
def index():
    return render_template('pos/index.html')
