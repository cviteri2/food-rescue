# FoodRescue Guayaquil

MVP web que conecta comercios con excedentes de alimentos (restaurantes,
panaderías, supermercados) con organizaciones benéficas, comedores
comunitarios y personas individuales, para redistribuir alimentos antes de
que se desperdicien. Inspirado en el modelo de
[Too Good To Go](https://www.toogoodtogo.com/es), adaptado a un esquema
benéfico (sin pagos) y diseñado desde cero para correr en el **plan
gratuito (Beginner) de PythonAnywhere**.

Hay tres roles: **comercio** (dona excedentes), **organización** o
**persona** (ambos son "beneficiarios": ven el mapa de publicaciones
cercanas y reclaman) y **admin** (aprueba comercios/organizaciones y ve
métricas).

## Restricciones de diseño (por qué el código es como es)

- **Sin WebSockets.** Notificaciones y actualizaciones de mapa se resuelven
  con *polling* HTTP desde el navegador (`/api/notificaciones` cada 15-20s,
  `/api/publicaciones-cercanas` cada 20s).
- **Sin cron confiable.** El estado de una publicación (`disponible` /
  `reclamado` / `entregado` / `expirado`) se calcula siempre al momento de
  la consulta comparando contra `expira_en` (ver `utils.sync_estado`), nunca
  con un job periódico.
- **Sin llamadas salientes a APIs externas desde el backend.** El mapa usa
  Leaflet.js + tiles de OpenStreetMap cargados directamente por el
  navegador del usuario. La distancia entre organización y publicación se
  calcula con la fórmula de Haversine en Python puro (`utils.haversine_km`).
- **Fotos:** se comprimen en el navegador con `<canvas>` antes de subirse, y
  el backend rechaza cualquier archivo mayor a 500KB (`MAX_CONTENT_LENGTH`).
- **Reclamos concurrentes:** se usa un `UPDATE ... WHERE estado='disponible'`
  atómico y se verifica `rowcount` para decidir quién ganó la carrera.

## Estructura del proyecto

```
food-rescue/
  app.py              # application factory + registro de blueprints
  config.py           # configuracion (SQLite por defecto; MySQL opcional via env vars)
  models.py           # Usuario, Publicacion, Reclamo, Notificacion
  utils.py            # Haversine + sincronizacion perezosa de estado
  wsgi.py              # punto de entrada para PythonAnywhere
  seed.py              # datos de prueba para la sustentacion
  routes/
    auth.py            # login, logout, registro
    comercios.py        # dashboard e historial del comercio
    beneficiarios.py    # dashboard y reclamos (organizacion o persona)
    admin.py            # panel de administracion
    api.py              # endpoints JSON (polling, crear/reclamar/entregar)
  templates/
  static/
    css/
    js/
    uploads/            # fotos subidas (gitignored)
  requirements.txt
  MIGRACION_APP.md       # que endpoints ya son JSON puro para una futura app movil
```

## Correr localmente (SQLite)

```bash
python -m venv .venv
source .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Cargar datos de prueba (crea las tablas y borra cualquier dato previo):
python seed.py

# Levantar el servidor de desarrollo:
python app.py
```

Abre `http://127.0.0.1:5000`. Credenciales de prueba creadas por `seed.py`:

| Rol | Email | Contraseña |
|---|---|---|
| Admin | `admin@foodrescue.gy` | `admin123` |
| Comercio | `panaderia@demo.com` / `restaurante@demo.com` / `supermercado@demo.com` | `demo123` |
| Organización | `comedor@demo.com` / `fundacion@demo.com` / `albergue@demo.com` | `demo123` |
| Persona | `persona1@demo.com` / `persona2@demo.com` | `demo123` |

Los usuarios de `seed.py` ya quedan `activo=True`. Los registros nuevos por
`/auth/registro/comercio` o `/auth/registro/organizacion` quedan pendientes
de aprobación en el panel de admin (representan una institución que hay que
verificar). `/auth/registro/persona` en cambio se activa de inmediato, sin
aprobación manual: es el consumidor final individual, igual que en Too Good
To Go no hay verificación institucional para quien solo va a recoger comida.

## Despliegue en PythonAnywhere (plan free "Beginner")

### 1. Subir el código

Desde una consola Bash de PythonAnywhere (`Consoles` → `Bash`):

```bash
git clone https://github.com/<tu-usuario>/food-rescue.git
cd food-rescue
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Base de datos: SQLite en producción (ruta por defecto, sin MySQL)

`config.py` solo arma una URI de MySQL cuando encuentra `MYSQL_HOST` (o
`DATABASE_URL`) como variable de entorno. Si no defines ninguna de las dos,
la app usa SQLite en producción exactamente igual que en local — no hay que
tocar código ni crear nada en la pestaña **Databases**. El archivo vive en
`instance/foodrescue.db`, dentro de tu propio directorio del proyecto, y
cuenta contra la cuota de 512MB de disco (igual que si fuera MySQL).

Es una opción perfectamente válida para la escala de un taller: el free
tier corre con un solo worker web, así que no hay riesgo de que dos
procesos escriban el archivo SQLite al mismo tiempo. Si el proyecto crece a
uso real con más tráfico concurrente, migrar a MySQL más adelante es
agregar las variables del recuadro de abajo — el código no cambia.

<details>
<summary>Opcional: usar MySQL en vez de SQLite</summary>

En el dashboard: pestaña **Databases** → define una contraseña para MySQL →
crea una base con el nombre que te sugiere PythonAnywhere (normalmente
`tuusuario$foodrescue`). Anota el host que te muestra la misma página
(normalmente `tuusuario.mysql.pythonanywhere-services.com`). Luego agrega
estas variables de entorno en el paso 3, además de `SECRET_KEY`:

| Variable | Valor |
|---|---|
| `MYSQL_HOST` | `tuusuario.mysql.pythonanywhere-services.com` |
| `MYSQL_USER` | `tuusuario` |
| `MYSQL_PASSWORD` | la contraseña que definiste arriba |
| `MYSQL_DB` | `tuusuario$foodrescue` |

</details>

### 3. Variables de entorno

Pestaña **Web** → tu app → sección **Environment variables**, agrega al
menos:

| Variable | Valor |
|---|---|
| `SECRET_KEY` | una cadena aleatoria larga (no la del repo); genérala con `python3 -c "import secrets; print(secrets.token_hex(32))"` |

Si vas a usar MySQL (paso 2, opcional), agrega también las cuatro variables
`MYSQL_*` de ese recuadro. Si tu cuenta no muestra esta sección, exporta las
mismas variables al inicio de `wsgi.py` con `os.environ["..."] = "..."`
(menos prolijo, pero funciona igual en el free tier).

### 4. Crear la app web

Pestaña **Web** → **Add a new web app** → elige **Flask** manualmente (o
"Manual configuration" con el mismo Python que tu virtualenv) → cuando
pregunte por el WSGI file, edítalo para que apunte a este proyecto:

- **Source code / working directory:** `/home/tuusuario/food-rescue`
- **Virtualenv:** `/home/tuusuario/food-rescue/.venv`
- **WSGI configuration file:** reemplaza su contenido por el de `wsgi.py`
  de este repo, ajustando la variable `path` a tu ruta real.
- **Static files:** mapea la URL `/static/` a
  `/home/tuusuario/food-rescue/static/`.

### 5. Crear las tablas

Desde una consola Bash, con el virtualenv activado:

```bash
# Opción A: con datos de demostración para la sustentación
python seed.py

# Opción B: tablas vacías, sin datos de prueba
python -c "from app import app; from models import db; app.app_context().push(); db.create_all()"
```

### 6. Recargar la app

Pestaña **Web** → botón verde **Reload**. Cada vez que hagas `git pull` con
cambios nuevos, repite este paso — PythonAnywhere no recarga solo.

### ⚠️ Advertencia específica del plan free que no es obvia

Las apps web del plan gratuito **expiran cada 3 meses** si nadie entra al
dashboard a renovarlas manualmente (botón "Run until 3 months from today" en
la pestaña Web). Si este proyecto sigue como producto real después del
taller, alguien tiene que acordarse de entrar a renovarla — de lo contrario
la app deja de responder sin que haya ningún error de código de por medio.

### Otras limitaciones a tener presentes

- Disco: 512MB compartidos entre código, base de datos y fotos subidas. Con
  volumen real de uso, decide pronto si las fotos siguen en filesystem o se
  limita cuántas publicaciones activas pueden llevar foto.
- El acceso saliente a internet del free tier está restringido a una
  whitelist — por diseño, este backend no hace ninguna llamada saliente a
  APIs de terceros, así que esto no debería afectarte mientras no agregues
  una dependencia nueva que sí lo requiera (por ejemplo, un SMTP externo).
- Solo se permite 1 tarea programada diaria (máx. 2h) — el proyecto no
  depende de ninguna para funcionar correctamente (ver sección de
  restricciones de diseño arriba).
