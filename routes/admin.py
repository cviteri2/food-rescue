from datetime import datetime, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from models import Publicacion, Usuario, db
from utils import sync_estado

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _requiere_admin():
    if current_user.tipo != "admin":
        abort(403)


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    _requiere_admin()

    for p in Publicacion.query.filter(Publicacion.estado.in_(["disponible", "reclamado"])).all():
        sync_estado(p)

    hace_30_dias = datetime.utcnow() - timedelta(days=30)

    metricas = {
        "publicaciones_activas": Publicacion.query.filter_by(estado="disponible").count(),
        "total_entregadas": Publicacion.query.filter_by(estado="entregado").count(),
        "comercios_activos_30d": (
            db.session.query(Publicacion.comercio_id)
            .filter(Publicacion.creado_en >= hace_30_dias)
            .distinct()
            .count()
        ),
        "organizaciones_registradas": Usuario.query.filter_by(tipo="organizacion").count(),
        "personas_registradas": Usuario.query.filter_by(tipo="persona").count(),
        "comercios_registrados": Usuario.query.filter_by(tipo="comercio").count(),
    }

    usuarios = (
        Usuario.query.filter(Usuario.tipo.in_(["comercio", "organizacion", "persona"]))
        .order_by(Usuario.creado_en.desc())
        .all()
    )

    return render_template("admin_dashboard.html", usuarios=usuarios, metricas=metricas)


@admin_bp.route("/usuarios/<int:usuario_id>/toggle", methods=["POST"])
@login_required
def toggle_usuario(usuario_id):
    _requiere_admin()
    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None:
        abort(404)
    usuario.activo = not usuario.activo
    db.session.commit()
    flash(f"{usuario.nombre} ahora esta {'activo' if usuario.activo else 'suspendido'}.", "success")
    return redirect(url_for("admin.dashboard"))
