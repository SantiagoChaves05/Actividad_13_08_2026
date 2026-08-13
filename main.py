from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models, schema, auth
import jwt

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title= "Actividad usando jwt"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/registro")
def registrar(usuario: schema.UsuarioCrear, db: Session = Depends(get_db)):
    existe = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    
    if existe:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    nuevo = models.Usuario(
        email=usuario.email,
        hashed_password=auth.hash_password(usuario.password)
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return {"mensaje": "Usuario creado"}


@app.post("/login", response_model=schema.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == form_data.username).first()

    if not usuario or not auth.verificar_password(form_data.password, usuario.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = auth.crear_token_acceso({"sub": usuario.email})
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return usuario

@app.post("/compras/procesar")
def procesar_compra(
    compra: schema.Compra,
    usuario: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    monto_total = compra.precio_unitario * compra.cantidad


    if compra.cantidad >= 5:
        descuento = monto_total * 0.12
    elif compra.cantidad >= 3:
        descuento = monto_total * 0.05
    else:
        descuento = 0

    monto_final = monto_total - descuento

    if usuario.saldo_cuenta < monto_final:
        raise HTTPException(
            status_code=400,
            detail=f"Saldo insuficiente. Requiere {monto_final} y su saldo actual es {usuario.saldo_cuenta}"
        )

    usuario.saldo_cuenta -= monto_final
    db.commit()

    return {
        "mensaje": "Compra exitosa",
        "producto": compra.nombre_producto,
        "cantidad": compra.cantidad,
        "total_pagado": monto_final,
        "nuevo_saldo": usuario.saldo_cuenta
    }