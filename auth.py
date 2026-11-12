"""
Utilidades de autenticación para BEEMANAGER.

Se encarga de:
- Convertir una contraseña en texto plano a un hash seguro (y viceversa, verificarla)
- Crear y leer "tokens" de acceso (JWT) que identifican a un usuario ya logueado

Requiere:
    pip install passlib[bcrypt] python-jose[cryptography]
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# ---------------------------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------------------------

# En un proyecto real esta clave NUNCA va directo en el código: se lee desde
# una variable de entorno (.env). Para el proyecto académico, por ahora
# puede quedar aquí, pero recuérdalo si algún día esto sale a producción.
SECRET_KEY = "cambia-esta-clave-por-una-larga-y-aleatoria-antes-de-entregar"
ALGORITHM = "HS256"
MINUTOS_EXPIRACION_TOKEN = 60 * 8  # 8 horas de sesión

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# CONTRASEÑAS
# ---------------------------------------------------------------------------

def hashear_password(password_plano: str) -> str:
    """Convierte una contraseña en texto plano a un hash seguro para guardar en la BD."""
    return pwd_context.hash(password_plano)


def verificar_password(password_plano: str, password_hash: str) -> bool:
    """Compara una contraseña escrita por el usuario contra el hash guardado."""
    return pwd_context.verify(password_plano, password_hash)


# ---------------------------------------------------------------------------
# TOKENS (JWT)
# ---------------------------------------------------------------------------

def crear_token_acceso(datos: dict) -> str:
    """
    Genera un token firmado que el frontend guarda (ej. en localStorage) y
    reenvía en cada petición para demostrar "ya inicié sesión".
    `datos` normalmente lleva al menos {"sub": email_del_usuario, "rol": rol}.
    """
    datos_a_codificar = datos.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=MINUTOS_EXPIRACION_TOKEN)
    datos_a_codificar.update({"exp": expiracion})
    return jwt.encode(datos_a_codificar, SECRET_KEY, algorithm=ALGORITHM)


def leer_token(token: str) -> Optional[dict]:
    """Decodifica un token y devuelve su contenido, o None si es inválido/expiró."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
