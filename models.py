"""
Modelos de datos para BEEMANAGER (Almic)
Basados en el MER definido en el proyecto.

Requiere: pip install sqlmodel
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


# ---------------------------------------------------------------------------
# ENUMS
# ---------------------------------------------------------------------------

class RolUsuario(str, Enum):
    administrador = "administrador"
    empleado = "empleado"
    cliente = "cliente"


class CategoriaProducto(str, Enum):
    miel = "miel"
    propoleo = "propoleo"
    polen = "polen"
    cera = "cera"
    otros = "otros"


class UnidadMedida(str, Enum):
    ml = "ml"
    g = "g"
    unidad = "unidad"


class MetodoPago(str, Enum):
    paypal = "paypal"
    transferencia_bancaria = "transferencia_bancaria"
    oxxo = "oxxo"
    efectivo_contra_entrega = "efectivo_contra_entrega"


class EstadoVenta(str, Enum):
    pendiente = "pendiente"
    pagada = "pagada"
    enviada = "enviada"
    entregada = "entregada"
    cancelada = "cancelada"


# ---------------------------------------------------------------------------
# USUARIO
# ---------------------------------------------------------------------------

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_completo: str
    email: str = Field(unique=True, index=True)
    password_hash: Optional[str] = None  # nulo si nunca se registró formalmente
    rol: RolUsuario = Field(default=RolUsuario.cliente)
    celular: Optional[str] = None
    direccion_envio: Optional[str] = None
    porcentaje_descuento: float = Field(default=0.0)  # ej. 0.05 para clientes registrados
    fecha_registro: date = Field(default_factory=date.today)
    activo: bool = Field(default=True)


# ---------------------------------------------------------------------------
# PRODUCTO
# ---------------------------------------------------------------------------

class Producto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    categoria: CategoriaProducto
    descripcion: Optional[str] = None
    unidad_medida: UnidadMedida
    contenido: float  # ej. 375 (va junto con unidad_medida -> "375 ml")
    precio: float
    disponible: bool = Field(default=True)
    imagen_url: Optional[str] = None


# ---------------------------------------------------------------------------
# LOTE
# ---------------------------------------------------------------------------

class Lote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(unique=True, index=True)  # generado automáticamente, ver utils.py
    fecha_cosecha: date
    observaciones_generales: Optional[str] = None


# ---------------------------------------------------------------------------
# PRODUCCION
# ---------------------------------------------------------------------------

class Produccion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lote_id: int = Field(foreign_key="lote.id")
    producto_id: int = Field(foreign_key="producto.id")
    fecha: date = Field(default_factory=date.today)
    cantidad_producida: float
    observaciones: Optional[str] = None


# ---------------------------------------------------------------------------
# INVENTARIO
# ---------------------------------------------------------------------------

class Inventario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    producto_id: int = Field(foreign_key="producto.id", unique=True)  # 1 a 1 con Producto
    cantidad_disponible: int = Field(default=0)
    cantidad_minima: int = Field(default=0)
    fecha_actualizacion: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# VENTA
# ---------------------------------------------------------------------------

class Venta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")  # nulo si es invitado

    # Datos del comprador invitado (solo se usan si usuario_id es None)
    nombre_comprador: Optional[str] = None
    telefono_comprador: Optional[str] = None
    direccion_envio_comprador: Optional[str] = None

    fecha: datetime = Field(default_factory=datetime.utcnow)
    metodo_pago: MetodoPago
    referencia_pago: Optional[str] = None  # ID de transacción, cuando se integre un pago real
    estado: EstadoVenta = Field(default=EstadoVenta.pendiente)

    subtotal: float
    descuento_aplicado: float = Field(default=0.0)
    total: float


# ---------------------------------------------------------------------------
# DETALLE DE VENTA
# ---------------------------------------------------------------------------

class DetalleVenta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    venta_id: int = Field(foreign_key="venta.id")
    producto_id: int = Field(foreign_key="producto.id")
    cantidad: int
    precio_unitario: float  # se guarda el precio al momento de la venta, no el actual
    subtotal: float