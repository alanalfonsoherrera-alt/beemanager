from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, SQLModel, create_engine, Session, select

class Producto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: str
    precio: float
    stock: int

sqlite_file_name = "almic.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

def crear_tablas():
    SQLModel.metadata.create_all(engine)

app = FastAPI(title="Almic - Bee Manager API", version="1.0")

# Permitir conexiones desde el navegador (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite cualquier origen para pruebas locales
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    crear_tablas()

@app.get("/api/productos")
def obtener_productos():
    with Session(engine) as session:
        productos = session.exec(select(Producto)).all()
        return productos

@app.post("/api/productos")
def crear_producto(producto: Producto):
    with Session(engine) as session:
        session.add(producto)
        session.commit()
        session.refresh(producto)
        return {"mensaje": "Producto guardado con éxito en SQLite", "producto": producto}

@app.delete("/api/productos/{producto_id}")
def eliminar_producto(producto_id: int):
    with Session(engine) as session:
        producto = session.get(Producto, producto_id)
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        session.delete(producto)
        session.commit()
        return {"mensaje": "Producto eliminado con éxito"}