from pydantic import BaseModel

class CompraInput(BaseModel):
    nombre_producto: str
    precio_unitario: float
    cantidad: int
