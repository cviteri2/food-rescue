import sys

# En PythonAnywhere, reemplaza esta ruta por la ruta real de tu proyecto,
# por ejemplo: /home/tuusuario/food-rescue
path = "/home/tuusuario/food-rescue"
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application  # noqa: E402
