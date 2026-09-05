from flask import Blueprint, abort, render_template
from flask_login import current_user, login_required

from models import Reclamo

organizaciones_bp = Blueprint("organizaciones", __name__, url_prefix="/organizacion")


def _requiere_organizacion():
    if current_user.tipo != "organizacion":
        abort(403)


@organizaciones_bp.route("/dashboard")
@login_required
def dashboard():
    _requiere_organizacion()
    return render_template("organizacion_dashboard.html")


@organizaciones_bp.route("/reclamos")
@login_required
def reclamos():
    _requiere_organizacion()
    mis_reclamos = current_user.reclamos.order_by(Reclamo.reclamado_en.desc()).all()
    return render_template("organizacion_reclamos.html", reclamos=mis_reclamos)
