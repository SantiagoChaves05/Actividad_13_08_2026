from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from datetime import datetime, timedelta
from schemas import CompraInput
from models import USUARIOS_DB

app = FastAPI()

SECRET_KEY = "MI_CLAVE_SECRETA_SUPER_SIMPLE"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    usuario = USUARIOS_DB.get(form_data.username)
    if not usuario or form_data.password != "clave123":
        raise HTTPException(status_code=400, detail="Correo o contraseña incorrectos")
    
    expiracion = datetime.utcnow() + timedelta(minutes=30)
    payload = {"sub": usuario["email"], "exp": expiracion}
    token_generado = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": token_generado, "token_type": "bearer"}


@app.post("/compras/procesar")
def procesar_compra(compra: CompraInput, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email_usuario = payload.get("sub")
        if email_usuario is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
        
    usuario = USUARIOS_DB.get(email_usuario)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    monto_total = compra.precio_unitario * compra.cantidad
    
    if compra.cantidad >= 5:
        descuento = monto_total * 0.12
    elif compra.cantidad >= 3 and compra.cantidad <= 4:
        descuento = monto_total * 0.05
    else:
        descuento = 0.0

    monto_total_con_descuento = monto_total - descuento

    if usuario["saldo_cuenta"] < monto_total_con_descuento:
        raise HTTPException(
            status_code=400, 
            detail=f"Saldo insuficiente. Requiere ${monto_total_con_descuento} y su saldo actual es ${usuario['saldo_cuenta']}"
        )

    usuario["saldo_cuenta"] = usuario["saldo_cuenta"] - monto_total_con_descuento

    return {
        "mensaje": "Compra procesada con éxito",
        "nuevo_saldo": usuario["saldo_cuenta"],
        "resumen_compra": {
            "producto": compra.nombre_producto,
            "cantidad": compra.cantidad,
            "precio_original": monto_total,
            "descuento_aplicado": descuento,
            "total_pagado": monto_total_con_descuento
        }
    }
