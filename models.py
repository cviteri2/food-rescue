from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # comercio | organizacion | admin
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    direccion = db.Column(db.String(255))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    activo = db.Column(db.Boolean, default=False, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # especificos de comercio
    categoria = db.Column(db.String(100))
    horario = db.Column(db.String(150))

    # especificos de organizacion
    tipo_organizacion = db.Column(db.String(100))
    capacidad_estimada = db.Column(db.Integer)

    publicaciones = db.relationship(
        "Publicacion", backref="comercio", lazy="dynamic", foreign_keys="Publicacion.comercio_id"
    )
    reclamos = db.relationship(
        "Reclamo", backref="organizacion", lazy="dynamic", foreign_keys="Reclamo.organizacion_id"
    )

    @property
    def is_active(self):
        return self.activo

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Publicacion(db.Model):
    __tablename__ = "publicaciones"

    id = db.Column(db.Integer, primary_key=True)
    comercio_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    cantidad = db.Column(db.String(100))
    foto_url = db.Column(db.String(255))
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    expira_en = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(20), default="disponible", nullable=False)

    reclamos = db.relationship("Reclamo", backref="publicacion", lazy="dynamic")

    def to_dict(self, distancia_km=None):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "cantidad": self.cantidad,
            "foto_url": self.foto_url,
            "lat": self.lat,
            "lng": self.lng,
            "creado_en": self.creado_en.isoformat(),
            "expira_en": self.expira_en.isoformat(),
            "estado": self.estado,
            "comercio_id": self.comercio_id,
            "comercio_nombre": self.comercio.nombre,
            "distancia_km": round(distancia_km, 2) if distancia_km is not None else None,
        }


class Reclamo(db.Model):
    __tablename__ = "reclamos"

    id = db.Column(db.Integer, primary_key=True)
    publicacion_id = db.Column(db.Integer, db.ForeignKey("publicaciones.id"), nullable=False)
    organizacion_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    reclamado_en = db.Column(db.DateTime, default=datetime.utcnow)
    entregado_en = db.Column(db.DateTime)


class Notificacion(db.Model):
    __tablename__ = "notificaciones"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    mensaje = db.Column(db.String(255), nullable=False)
    publicacion_id = db.Column(db.Integer, db.ForeignKey("publicaciones.id"))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    leida = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "mensaje": self.mensaje,
            "publicacion_id": self.publicacion_id,
            "creado_en": self.creado_en.isoformat(),
            "leida": self.leida,
        }
