import os
import uuid
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from models import Notificacion, Publicacion, Reclamo, Usuario, db
from utils import haversine_km, sync_estado

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _archivo_permitido(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


def _notificar_beneficiarios_cercanos(publicacion):
    radio = current_app.config["RADIO_NOTIFICACION_KM"]
    beneficiarios = Usuario.query.filter(
        Usuario.tipo.in_(["organizacion", "persona"]), Usuario.activo.is_(True)
    ).all()
    for beneficiario in beneficiarios:
        distancia = haversine_km(beneficiario.lat, beneficiario.lng, publicacion.lat, publicacion.lng)
        if distancia is not None and distancia <= radio:
            db.session.add(
                Notificacion(
                    usuario_id=beneficiario.id,
                    mensaje=f"Nueva publicacion cerca de ti: {publicacion.titulo}",
                    publicacion_id=publicacion.id,
                )
            )
    db.session.commit()


@api_bp.route("/publicaciones", methods=["POST"])
@login_required
def crear_publicacion():
    if current_user.tipo != "comercio":
        return jsonify({"error": "Solo un comercio puede publicar excedentes."}), 403

    titulo = request.form.get("titulo", "").strip()
    cantidad = request.form.get("cantidad", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    lat = request.form.get("lat")
    lng = request.form.get("lng")
    expira_en_raw = request.form.get("expira_en")

    if not titulo or not lat or not lng or not expira_en_raw:
        return jsonify({"error": "Titulo, ubicacion y hora limite son obligatorios."}), 400

    try:
        expira_en = datetime.fromisoformat(expira_en_raw)
    except ValueError:
        return jsonify({"error": "Formato de fecha invalido."}), 400

    if expira_en <= datetime.utcnow():
        return jsonify({"error": "La hora limite debe ser en el futuro."}), 400

    foto_url = None
    archivo = request.files.get("foto")
    if archivo and archivo.filename:
        if not _archivo_permitido(archivo.filename):
            return jsonify({"error": "Formato de imagen no permitido."}), 400
        nombre_archivo = f"{uuid.uuid4().hex}_{secure_filename(archivo.filename)}"
        archivo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_archivo))
        foto_url = url_for("static", filename=f"uploads/{nombre_archivo}")

    publicacion = Publicacion(
        comercio_id=current_user.id,
        titulo=titulo,
        descripcion=descripcion,
        cantidad=cantidad,
        foto_url=foto_url,
        lat=float(lat),
        lng=float(lng),
        expira_en=expira_en,
    )
    db.session.add(publicacion)
    db.session.commit()

    _notificar_beneficiarios_cercanos(publicacion)

    return jsonify(publicacion.to_dict()), 201


@api_bp.route("/publicaciones-cercanas")
@login_required
def publicaciones_cercanas():
    if current_user.tipo not in ("organizacion", "persona"):
        return jsonify({"error": "Solo una organizacion o persona puede ver publicaciones cercanas."}), 403

    lat = request.args.get("lat", type=float) or current_user.lat
    lng = request.args.get("lng", type=float) or current_user.lng
    radio = request.args.get("radio_km", type=float) or current_app.config["RADIO_NOTIFICACION_KM"]

    if lat is None or lng is None:
        return jsonify({"error": "No hay ubicacion disponible para calcular cercania."}), 400

    candidatas = Publicacion.query.filter(Publicacion.estado.in_(["disponible", "reclamado"])).all()

    resultado = []
    for p in candidatas:
        estado = sync_estado(p)
        if estado != "disponible":
            continue
        distancia = haversine_km(lat, lng, p.lat, p.lng)
        if distancia <= radio:
            resultado.append((distancia, p))

    resultado.sort(key=lambda par: par[0])

    return jsonify([p.to_dict(distancia_km=d) for d, p in resultado])


@api_bp.route("/publicaciones/<int:publicacion_id>/reclamar", methods=["POST"])
@login_required
def reclamar_publicacion(publicacion_id):
    if current_user.tipo not in ("organizacion", "persona"):
        return jsonify({"error": "Solo una organizacion o persona puede reclamar publicaciones."}), 403

    publicacion = db.session.get(Publicacion, publicacion_id)
    if publicacion is None:
        return jsonify({"error": "Publicacion no encontrada."}), 404

    # Sincroniza primero: si ya expiro, la siguiente actualizacion atomica
    # (que solo mueve filas en estado 'disponible') simplemente no encontrara
    # ninguna fila que actualizar.
    sync_estado(publicacion)

    resultado = db.session.execute(
        Publicacion.__table__.update()
        .where(Publicacion.id == publicacion_id, Publicacion.estado == "disponible")
        .values(estado="reclamado")
    )
    db.session.commit()

    if resultado.rowcount == 0:
        return jsonify({"error": "Esta publicacion ya no esta disponible."}), 409

    reclamo = Reclamo(publicacion_id=publicacion_id, beneficiario_id=current_user.id)
    db.session.add(reclamo)
    db.session.commit()

    return jsonify({"ok": True, "reclamo_id": reclamo.id})


@api_bp.route("/publicaciones/<int:publicacion_id>/entregar", methods=["POST"])
@login_required
def marcar_entregada(publicacion_id):
    if current_user.tipo != "comercio":
        return jsonify({"error": "Solo el comercio dueno puede marcar la entrega."}), 403

    publicacion = db.session.get(Publicacion, publicacion_id)
    if publicacion is None or publicacion.comercio_id != current_user.id:
        return jsonify({"error": "Publicacion no encontrada."}), 404

    if publicacion.estado != "reclamado":
        return jsonify({"error": "Solo se puede entregar una publicacion reclamada."}), 409

    reclamo = (
        Reclamo.query.filter_by(publicacion_id=publicacion_id, entregado_en=None)
        .order_by(Reclamo.id.desc())
        .first()
    )
    if reclamo is None:
        return jsonify({"error": "No se encontro el reclamo asociado."}), 409

    reclamo.entregado_en = datetime.utcnow()
    publicacion.estado = "entregado"
    db.session.commit()

    return jsonify({"ok": True})


@api_bp.route("/notificaciones")
@login_required
def notificaciones():
    items = (
        Notificacion.query.filter_by(usuario_id=current_user.id, leida=False)
        .order_by(Notificacion.creado_en.desc())
        .limit(30)
        .all()
    )
    return jsonify([n.to_dict() for n in items])


@api_bp.route("/notificaciones/<int:notificacion_id>/leer", methods=["POST"])
@login_required
def marcar_notificacion_leida(notificacion_id):
    notificacion = db.session.get(Notificacion, notificacion_id)
    if notificacion is None or notificacion.usuario_id != current_user.id:
        return jsonify({"error": "No encontrada."}), 404
    notificacion.leida = True
    db.session.commit()
    return jsonify({"ok": True})
