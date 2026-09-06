# Notas de migración hacia una app móvil (React Native / Flutter)

Este documento existe para no duplicar trabajo cuando la v1 (server-rendered
con Jinja2) crezca hacia una app móvil nativa. La regla que se siguió desde
el principio: **toda acción que cambia estado, y toda consulta que alimenta
un mapa o una lista, ya devuelve JSON puro**, aunque hoy solo la consuma
JavaScript vanilla desde el navegador. Solo las páginas de "primera carga"
(login, dashboards, formularios) son server-rendered.

## Endpoints listos para consumir tal cual desde una app móvil

Todos bajo el prefijo `/api`, autenticados con la cookie de sesión de
Flask-Login. **Importante:** si la app móvil no puede usar cookies de
sesión de forma nativa, el único cambio necesario es reemplazar
Flask-Login por un esquema de token (JWT o similar) — la forma de los
endpoints (rutas, payloads, respuestas) no cambia.

| Método | Ruta | Rol requerido | Descripción |
|---|---|---|---|
| `POST` | `/api/publicaciones` | comercio | Crea una publicación. Recibe `multipart/form-data` (titulo, descripcion, cantidad, lat, lng, expira_en, foto opcional). Devuelve la publicación creada en JSON. |
| `GET` | `/api/publicaciones-cercanas` | organizacion o persona | Devuelve publicaciones disponibles cerca de una ubicación (`lat`, `lng`, `radio_km` opcionales en query string; por defecto usa la ubicación registrada del beneficiario), ordenadas por distancia (Haversine). |
| `POST` | `/api/publicaciones/<id>/reclamar` | organizacion o persona | Reclama una publicación de forma atómica (evita condiciones de carrera entre dos beneficiarios, sean organizaciones o personas). |
| `POST` | `/api/publicaciones/<id>/entregar` | comercio (dueño) | Marca una publicación reclamada como entregada. |
| `GET` | `/api/notificaciones` | cualquier usuario autenticado | Notificaciones no leídas del usuario actual. Pensado para polling cada 15-20s; en una app móvil esto se reemplaza directamente por push nativo (FCM/APNs) sin tocar el resto del modelo de datos. |
| `POST` | `/api/notificaciones/<id>/leer` | cualquier usuario autenticado | Marca una notificación como leída. |

Todas las respuestas de error usan el mismo formato: `{"error": "mensaje"}`
con el código HTTP correspondiente (400, 403, 404, 409). Los códigos `409`
son intencionales: indican una condición de carrera perdida (publicación ya
reclamada, o publicación no está en el estado esperado para la acción), no
un error del cliente.

## Endpoints que siguen siendo server-rendered (no diseñados para consumo JSON)

- `GET/POST /auth/login`, `/auth/registro/comercio`, `/auth/registro/organizacion`, `/auth/registro/persona`
- `GET /comercio/dashboard`, `/comercio/historial`
- `GET /beneficiario/dashboard`, `/beneficiario/reclamos` (sirve tanto a organizacion como a persona)
- `GET /admin/dashboard`, `POST /admin/usuarios/<id>/toggle`

Si la app móvil también necesita registro/login, lo más simple es agregar un
`/api/auth/login` y `/api/auth/registro` que reutilicen las mismas funciones
de validación ya escritas en `routes/auth.py` (están separadas de la lógica
de renderizado justamente para esto), devolviendo JSON en vez de redirigir.
El panel de administración no necesita versión móvil.

## Lo que NO hay que rehacer

- El cálculo de distancia (Haversine, en `utils.py`) y la sincronización
  perezosa de estado (`sync_estado`, también en `utils.py`) son lógica de
  dominio pura, sin ninguna dependencia de Flask/Jinja. Se reutilizan tal
  cual desde cualquier cliente.
- El modelo de datos (`models.py`) no necesita cambios para servir a una app
  móvil: los métodos `to_dict()` en `Publicacion` y `Notificacion` son el
  contrato JSON, y ya están.
