from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models import Usuario, db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario is None or not usuario.check_password(password):
            flash("Email o contrasena incorrectos.", "error")
            return render_template("login.html")

        if not usuario.activo:
            flash("Tu cuenta todavia no ha sido aprobada por un administrador.", "error")
            return render_template("login.html")

        login_user(usuario)
        return redirect(url_for("index"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/registro/comercio", methods=["GET", "POST"])
def registro_comercio():
    if request.method == "POST":
        error = _validar_registro_comun()
        if error:
            flash(error, "error")
            return render_template("registro_comercio.html")

        usuario = Usuario(
            tipo="comercio",
            email=request.form["email"].strip().lower(),
            nombre=request.form["nombre"].strip(),
            direccion=request.form.get("direccion", "").strip(),
            categoria=request.form.get("categoria", "").strip(),
            horario=request.form.get("horario", "").strip(),
            lat=float(request.form["lat"]),
            lng=float(request.form["lng"]),
            activo=False,
        )
        usuario.set_password(request.form["password"])
        db.session.add(usuario)
        db.session.commit()
        flash("Registro enviado. Un administrador debe aprobar tu cuenta antes de que puedas ingresar.", "success")
        return redirect(url_for("auth.login"))

    return render_template("registro_comercio.html")


@auth_bp.route("/registro/organizacion", methods=["GET", "POST"])
def registro_organizacion():
    if request.method == "POST":
        error = _validar_registro_comun()
        if error:
            flash(error, "error")
            return render_template("registro_organizacion.html")

        capacidad = request.form.get("capacidad_estimada")

        usuario = Usuario(
            tipo="organizacion",
            email=request.form["email"].strip().lower(),
            nombre=request.form["nombre"].strip(),
            direccion=request.form.get("direccion", "").strip(),
            tipo_organizacion=request.form.get("tipo_organizacion", "").strip(),
            capacidad_estimada=int(capacidad) if capacidad else None,
            lat=float(request.form["lat"]),
            lng=float(request.form["lng"]),
            activo=False,
        )
        usuario.set_password(request.form["password"])
        db.session.add(usuario)
        db.session.commit()
        flash("Registro enviado. Un administrador debe aprobar tu cuenta antes de que puedas ingresar.", "success")
        return redirect(url_for("auth.login"))

    return render_template("registro_organizacion.html")


@auth_bp.route("/registro/persona", methods=["GET", "POST"])
def registro_persona():
    if request.method == "POST":
        error = _validar_registro_comun()
        if error:
            flash(error, "error")
            return render_template("registro_persona.html")

        usuario = Usuario(
            tipo="persona",
            email=request.form["email"].strip().lower(),
            nombre=request.form["nombre"].strip(),
            direccion=request.form.get("direccion", "").strip(),
            lat=float(request.form["lat"]),
            lng=float(request.form["lng"]),
            # A diferencia de comercio/organizacion, una persona individual no
            # representa una institucion que haya que verificar: se activa de
            # una vez, igual que en Too Good To Go no hay aprobacion manual
            # para el consumidor final.
            activo=True,
        )
        usuario.set_password(request.form["password"])
        db.session.add(usuario)
        db.session.commit()
        flash("Cuenta creada. Ya puedes ingresar.", "success")
        return redirect(url_for("auth.login"))

    return render_template("registro_persona.html")


def _validar_registro_comun():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    nombre = request.form.get("nombre", "").strip()
    lat = request.form.get("lat")
    lng = request.form.get("lng")

    if not email or not password or not nombre:
        return "Nombre, email y contrasena son obligatorios."
    if not lat or not lng:
        return "Debes marcar tu ubicacion en el mapa."
    if Usuario.query.filter_by(email=email).first():
        return "Ese email ya esta registrado."
    return None
