"""
Esquemas de entrada/salida para la API (no son tablas de la base de datos,
son solo "formas" de los datos que entran y salen por los endpoints).

Separarlos de los modelos de tabla (models.py) evita, por ejemplo, que el
password_hash de un usuario se devuelva por accidente en una respuesta.
"""

from datetime import date
from typing import Optional

from sqlmodel import SQLModel

from models import RolUsuario


class UsuarioRegistro(SQLModel):
    """Lo que el cliente envía al registrarse."""
    nombre_completo: str
    email: str
    password: str
    celular: Optional[str] = None
    direccion_envio: Optional[str] = None


class UsuarioLogin(SQLModel):
    """Lo que el cliente envía para iniciar sesión."""
    email: str
    password: str


class UsuarioPublico(SQLModel):
    """Lo que la API devuelve sobre un usuario -- nunca incluye el password_hash."""
    id: int
    nombre_completo: str
    email: str
    rol: RolUsuario
    celular: Optional[str] = None
    direccion_envio: Optional[str] = None
    porcentaje_descuento: float
    fecha_registro: date
    activo: bool


class TokenRespuesta(SQLModel):
    """Lo que la API devuelve tras un login exitoso."""
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioPublico
