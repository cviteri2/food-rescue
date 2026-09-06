from flask import Blueprint, abort, render_template
from flask_login import current_user, login_required

from models import Reclamo

# Organizaciones (comedores, fundaciones) y personas individuales son ambos
# "beneficiarios": ven el mismo mapa de publicaciones cercanas y reclaman de
# la misma forma. Lo unico que las distingue es el formulario de registro.
beneficiarios_bp = Blueprint("beneficiarios", __name__, url_prefix="/beneficiario")

TIPOS_BENEFICIARIO = ("organizacion", "persona")


def _requiere_beneficiario():
    if current_user.tipo not in TIPOS_BENEFICIARIO:
        abort(403)


@beneficiarios_bp.route("/dashboard")
@login_required
def dashboard():
    _requiere_beneficiario()
    return render_template("beneficiario_dashboard.html")


@beneficiarios_bp.route("/reclamos")
@login_required
def reclamos():
    _requiere_beneficiario()
    mis_reclamos = current_user.reclamos.order_by(Reclamo.reclamado_en.desc()).all()
    return render_template("beneficiario_reclamos.html", reclamos=mis_reclamos)
