import math
from datetime import datetime


def haversine_km(lat1, lng1, lat2, lng2):
    """Distancia en linea recta entre dos puntos, sin depender de ninguna API externa."""
    if lat1 is None or lng1 is None or lat2 is None or lng2 is None:
        return None

    radio_tierra_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return radio_tierra_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def sync_estado(publicacion):
    """Calcula el estado real de una publicacion al momento de la consulta y lo
    persiste de forma perezosa si detecto que expiro. No depende de ningun cron:
    el plan gratuito de PythonAnywhere solo permite 1 tarea programada diaria,
    asi que la expiracion se evalua siempre contra `expira_en` en cada request.

    Ademas cubre el caso de una publicacion reclamada cuya hora limite de recojo
    ya paso sin que el comercio la haya marcado como entregada: se considera
    perdida (expirada) en vez de quedar "reclamado" para siempre.
    """
    from models import db, Reclamo

    ahora = datetime.utcnow()

    if publicacion.estado == "disponible" and ahora > publicacion.expira_en:
        publicacion.estado = "expirado"
        db.session.commit()
    elif publicacion.estado == "reclamado" and ahora > publicacion.expira_en:
        reclamo = (
            Reclamo.query.filter_by(publicacion_id=publicacion.id)
            .order_by(Reclamo.id.desc())
            .first()
        )
        if reclamo is None or reclamo.entregado_en is None:
            publicacion.estado = "expirado"
            db.session.commit()

    return publicacion.estado
