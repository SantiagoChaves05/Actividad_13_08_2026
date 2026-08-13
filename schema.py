from pydantic import BaseModel

class UsuarioCrear(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Compra(BaseModel):
    nombre_producto: str
    precio_unitario: float
    cantidad: int