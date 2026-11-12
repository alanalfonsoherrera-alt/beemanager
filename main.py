from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import SQLModel, create_engine, Session, select

from auth import crear_token_acceso, hashear_password, leer_token, verificar_password
from models import Producto, RolUsuario, Usuario
from schemas import TokenRespuesta, UsuarioLogin, UsuarioPublico, UsuarioRegistro

sqlite_file_name = "almic.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)


def crear_tablas():
    SQLModel.metadata.create_all(engine)


app = FastAPI(title="Almic - Bee Manager API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    crear_tablas()


# ---------------------------------------------------------------------------
# DEPENDENCIAS DE AUTENTICACION
# ---------------------------------------------------------------------------

# Le dice a FastAPI: "el token viene en el header Authorization: Bearer <token>"
# y que se obtiene llamando a /api/usuarios/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/usuarios/login")


def obtener_usuario_actual(token: str = Depends(oauth2_scheme)) -> Usuario:
    """Lee el token enviado por el cliente y devuelve el Usuario correspondiente."""
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = leer_token(token)
    if payload is None:
        raise credenciales_invalidas

    email = payload.get("sub")
    if email is None:
        raise credenciales_invalidas

    with Session(engine) as session:
        usuario = session.exec(select(Usuario).where(Usuario.email == email)).first()
        if usuario is None or not usuario.activo:
            raise credenciales_invalidas
        return usuario


def requiere_rol(*roles_permitidos: RolUsuario):
    """
    Genera una dependencia que solo deja pasar si el usuario logueado tiene
    uno de los roles indicados. Uso: Depends(requiere_rol(RolUsuario.administrador))
    """
    def verificar(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción",
            )
        return usuario
    return verificar


# ---------------------------------------------------------------------------
# USUARIOS: REGISTRO Y LOGIN
# ---------------------------------------------------------------------------

@app.post("/api/usuarios/registro", response_model=UsuarioPublico)
def registrar_usuario(datos: UsuarioRegistro):
    with Session(engine) as session:
        existente = session.exec(select(Usuario).where(Usuario.email == datos.email)).first()
        if existente:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con ese correo")

        nuevo_usuario = Usuario(
            nombre_completo=datos.nombre_completo,
            email=datos.email,
            password_hash=hashear_password(datos.password),
            rol=RolUsuario.cliente,          # quien se registra desde la web siempre es cliente
            celular=datos.celular,
            direccion_envio=datos.direccion_envio,
            porcentaje_descuento=0.05,       # beneficio por registrarse
        )
        session.add(nuevo_usuario)
        session.commit()
        session.refresh(nuevo_usuario)
        return nuevo_usuario


@app.post("/api/usuarios/login", response_model=TokenRespuesta)
def iniciar_sesion(datos: UsuarioLogin):
    with Session(engine) as session:
        usuario = session.exec(select(Usuario).where(Usuario.email == datos.email)).first()

        credenciales_invalidas = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )

        if not usuario or not usuario.password_hash:
            raise credenciales_invalidas
        if not verificar_password(datos.password, usuario.password_hash):
            raise credenciales_invalidas
        if not usuario.activo:
            raise HTTPException(status_code=403, detail="Usuario inactivo")

        token = crear_token_acceso({"sub": usuario.email, "rol": usuario.rol})
        return TokenRespuesta(access_token=token, usuario=usuario)


@app.get("/api/usuarios/yo", response_model=UsuarioPublico)
def usuario_autenticado(usuario: Usuario = Depends(obtener_usuario_actual)):
    """Útil para que el frontend confirme quién está logueado y con qué rol."""
    return usuario


# ---------------------------------------------------------------------------
# PRODUCTOS
# ---------------------------------------------------------------------------

@app.get("/api/productos")
def obtener_productos():
    with Session(engine) as session:
        productos = session.exec(select(Producto)).all()
        return productos


@app.post("/api/productos")
def crear_producto(
    producto: Producto,
    usuario: Usuario = Depends(requiere_rol(RolUsuario.administrador, RolUsuario.empleado)),
):
    with Session(engine) as session:
        session.add(producto)
        session.commit()
        session.refresh(producto)
        return {"mensaje": "Producto guardado con éxito en SQLite", "producto": producto}


@app.delete("/api/productos/{producto_id}")
def eliminar_producto(
    producto_id: int,
    usuario: Usuario = Depends(requiere_rol(RolUsuario.administrador)),
):
    with Session(engine) as session:
        producto = session.get(Producto, producto_id)
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        session.delete(producto)
        session.commit()
        return {"mensaje": "Producto eliminado con éxito"}
