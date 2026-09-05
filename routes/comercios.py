from flask import Blueprint, abort, render_template
from flask_login import current_user, login_required

from models import Publicacion
from utils import sync_estado

comercios_bp = Blueprint("comercios", __name__, url_prefix="/comercio")


def _requiere_comercio():
    if current_user.tipo != "comercio":
        abort(403)


@comercios_bp.route("/dashboard")
@login_required
def dashboard():
    _requiere_comercio()
    publicaciones = current_user.publicaciones.order_by(Publicacion.creado_en.desc()).all()
    for p in publicaciones:
        sync_estado(p)
    return render_template("comercio_dashboard.html", publicaciones=publicaciones)


@comercios_bp.route("/historial")
@login_required
def historial():
    _requiere_comercio()
    publicaciones = (
        current_user.publicaciones.filter(Publicacion.estado.in_(["entregado", "expirado"]))
        .order_by(Publicacion.creado_en.desc())
        .all()
    )
    total_entregadas = current_user.publicaciones.filter_by(estado="entregado").count()
    return render_template(
        "comercio_historial.html", publicaciones=publicaciones, total_entregadas=total_entregadas
    )
