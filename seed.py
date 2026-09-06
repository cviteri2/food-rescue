"""Carga datos de prueba para demostrar el flujo completo en la sustentacion.

ADVERTENCIA: este script borra y recrea todas las tablas (db.drop_all()).
No ejecutarlo contra una base de datos con datos reales.
"""

from datetime import datetime, timedelta

from app import create_app
from models import Notificacion, Publicacion, Reclamo, Usuario, db

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    admin = Usuario(tipo="admin", email="admin@foodrescue.gy", nombre="Administrador", activo=True)
    admin.set_password("admin123")

    comercio1 = Usuario(
        tipo="comercio",
        email="panaderia@demo.com",
        nombre="Panaderia Los Ceibos",
        direccion="Av. Francisco de Orellana, Guayaquil",
        categoria="Panaderia",
        horario="Lun-Sab 7am-8pm",
        lat=-2.148700,
        lng=-79.906000,
        activo=True,
    )
    comercio1.set_password("demo123")

    comercio2 = Usuario(
        tipo="comercio",
        email="restaurante@demo.com",
        nombre="Restaurante El Fortin",
        direccion="Malecon 2000, Guayaquil",
        categoria="Restaurante",
        horario="Todos los dias 11am-10pm",
        lat=-2.194200,
        lng=-79.883300,
        activo=True,
    )
    comercio2.set_password("demo123")

    comercio3 = Usuario(
        tipo="comercio",
        email="supermercado@demo.com",
        nombre="Supermercado La Rebaja",
        direccion="Av. de las Americas, Guayaquil",
        categoria="Supermercado",
        horario="Todos los dias 8am-9pm",
        lat=-2.156600,
        lng=-79.897700,
        activo=True,
    )
    comercio3.set_password("demo123")

    org1 = Usuario(
        tipo="organizacion",
        email="comedor@demo.com",
        nombre="Comedor Comunitario Esperanza",
        direccion="Cdla. Sauces, Guayaquil",
        tipo_organizacion="Comedor comunitario",
        capacidad_estimada=80,
        lat=-2.145000,
        lng=-79.910000,
        activo=True,
    )
    org1.set_password("demo123")

    org2 = Usuario(
        tipo="organizacion",
        email="fundacion@demo.com",
        nombre="Fundacion Manos Solidarias",
        direccion="Centro de Guayaquil",
        tipo_organizacion="Fundacion",
        capacidad_estimada=150,
        lat=-2.190000,
        lng=-79.887000,
        activo=True,
    )
    org2.set_password("demo123")

    org3 = Usuario(
        tipo="organizacion",
        email="albergue@demo.com",
        nombre="Albergue Nueva Vida",
        direccion="Norte de Guayaquil",
        tipo_organizacion="Albergue",
        capacidad_estimada=40,
        lat=-2.130000,
        lng=-79.915000,
        activo=True,
    )
    org3.set_password("demo123")

    persona1 = Usuario(
        tipo="persona",
        email="persona1@demo.com",
        nombre="Maria Fernanda Solis",
        direccion="Urdesa, Guayaquil",
        lat=-2.161000,
        lng=-79.899000,
        activo=True,
    )
    persona1.set_password("demo123")

    persona2 = Usuario(
        tipo="persona",
        email="persona2@demo.com",
        nombre="Jorge Andrade",
        direccion="Alborada, Guayaquil",
        lat=-2.140000,
        lng=-79.903000,
        activo=True,
    )
    persona2.set_password("demo123")

    db.session.add_all(
        [admin, comercio1, comercio2, comercio3, org1, org2, org3, persona1, persona2]
    )
    db.session.commit()

    ahora = datetime.utcnow()

    publicaciones = [
        Publicacion(
            comercio_id=comercio1.id,
            titulo="Pan del dia sin vender",
            descripcion="20 unidades de pan variado",
            cantidad="20 unidades",
            lat=comercio1.lat,
            lng=comercio1.lng,
            expira_en=ahora + timedelta(hours=3),
            estado="disponible",
        ),
        Publicacion(
            comercio_id=comercio2.id,
            titulo="Almuerzos preparados no servidos",
            descripcion="Menu del dia sobrante",
            cantidad="15 porciones",
            lat=comercio2.lat,
            lng=comercio2.lng,
            expira_en=ahora + timedelta(hours=1, minutes=30),
            estado="disponible",
        ),
        Publicacion(
            comercio_id=comercio3.id,
            titulo="Frutas y verduras cerca de vencer",
            descripcion="Cajas de producto fresco",
            cantidad="3 cajas (~15kg)",
            lat=comercio3.lat,
            lng=comercio3.lng,
            expira_en=ahora + timedelta(hours=5),
            estado="disponible",
        ),
        Publicacion(
            # A proposito ya expiro: demuestra estado_actual()/sync_estado() sin cron.
            comercio_id=comercio1.id,
            titulo="Pasteles del fin de semana",
            descripcion="Sobrantes de reposteria",
            cantidad="10 unidades",
            lat=comercio1.lat,
            lng=comercio1.lng,
            expira_en=ahora - timedelta(hours=2),
            estado="disponible",
        ),
        Publicacion(
            comercio_id=comercio2.id,
            titulo="Sopa del dia sobrante",
            descripcion="Olla grande de sopa",
            cantidad="8 litros",
            lat=comercio2.lat,
            lng=comercio2.lng,
            expira_en=ahora + timedelta(hours=2),
            estado="disponible",
        ),
    ]
    db.session.add_all(publicaciones)
    db.session.commit()

    reclamo_entregado = Reclamo(
        publicacion_id=publicaciones[4].id,
        beneficiario_id=org1.id,
        reclamado_en=ahora - timedelta(hours=1),
        entregado_en=ahora - timedelta(minutes=30),
    )
    publicaciones[4].estado = "entregado"

    # Este lo reclama una persona individual, no una organizacion, para
    # demostrar que ambos tipos de beneficiario comparten el mismo flujo.
    reclamo_activo = Reclamo(
        publicacion_id=publicaciones[2].id,
        beneficiario_id=persona1.id,
        reclamado_en=ahora - timedelta(minutes=10),
    )
    publicaciones[2].estado = "reclamado"

    db.session.add_all([reclamo_entregado, reclamo_activo])
    db.session.commit()

    for beneficiario in (org1, org2, org3, persona1, persona2):
        db.session.add(
            Notificacion(
                usuario_id=beneficiario.id,
                mensaje="Nueva publicacion cerca de ti: Pan del dia sin vender",
                publicacion_id=publicaciones[0].id,
            )
        )
    db.session.commit()

    print("Seed completo.")
    print("Admin:          admin@foodrescue.gy / admin123")
    print("Comercios:      panaderia@demo.com, restaurante@demo.com, supermercado@demo.com (clave: demo123)")
    print("Organizaciones: comedor@demo.com, fundacion@demo.com, albergue@demo.com (clave: demo123)")
    print("Personas:       persona1@demo.com, persona2@demo.com (clave: demo123)")
