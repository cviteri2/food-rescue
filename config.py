import os

basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, "instance")
upload_dir = os.path.join(basedir, "static", "uploads")

os.makedirs(upload_dir, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-cambiar-en-produccion")

    _database_url = os.environ.get("DATABASE_URL")
    if _database_url:
        # Permite forzar cualquier URI (por ejemplo mysql+pymysql://...) sin tocar codigo.
        SQLALCHEMY_DATABASE_URI = _database_url
    elif os.environ.get("MYSQL_HOST"):
        # Configuracion tipica de la base MySQL gratuita de PythonAnywhere.
        SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{}:{}@{}/{}?charset=utf8mb4".format(
            os.environ["MYSQL_USER"],
            os.environ["MYSQL_PASSWORD"],
            os.environ["MYSQL_HOST"],
            os.environ["MYSQL_DB"],
        )
    else:
        os.makedirs(instance_dir, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(instance_dir, "foodrescue.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Limite duro de tamano de foto: protege la cuota de disco de 512MB del plan
    # gratuito de PythonAnywhere. El cliente ademas comprime la imagen antes de subirla.
    MAX_CONTENT_LENGTH = 500 * 1024

    UPLOAD_FOLDER = upload_dir
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    # Radio (km) dentro del cual se notifica a las organizaciones cuando se publica
    # un nuevo excedente. Calculado siempre en el momento de la consulta con Haversine,
    # nunca via un job periodico.
    RADIO_NOTIFICACION_KM = float(os.environ.get("RADIO_NOTIFICACION_KM", 5))
