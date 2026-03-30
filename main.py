from fastapi import FastAPI, Depends, HTTPException, status, Header, Request, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from security import get_password_hash, verify_password
from storage import ensure_storage_dirs
import os
import re
import shutil

import models
import schemas
from database import engine, get_db
from storage import (
    ensure_storage_dirs,
    build_document_path,
    build_library_document_path,
    compute_file_sha256,
    validate_pdf_metadata,
)

# Inicialización de DB y App
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Habilitaciones Lupo", description="Administración de Seguridad y Trámites")

# Rutas absolutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

# Estáticos y Plantillas
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)
ensure_storage_dirs()

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# ── SEGURIDAD ──────────────────────────────────────────────────────────
SECRET_KEY = "SUPER_SECRET_KEY_LUPO" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# get_password_hash y verify_password importadas desde security.py (linea 11)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.Usuario).filter(models.Usuario.username == username).first()
    if user is None:
        raise credentials_exception
    return user

async def admin_required(current_user: models.Usuario = Depends(get_current_user)):
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de administrador")
    return current_user

# ── Endpoints Auth ──────────────────────────────────────────────────────
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.username == form_data.username).first()
    if user:
        print(f"Intento login: {form_data.username}, Hash en DB: {user.hashed_password[:10]}...")
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.Usuario)
async def read_users_me(current_user: models.Usuario = Depends(get_current_user)):
    return current_user

@app.get("/users/", response_model=list[schemas.Usuario])
def read_users(db: Session = Depends(get_db), current_user: models.Usuario = Depends(admin_required)):
    return db.query(models.Usuario).all()

@app.post("/users/", response_model=schemas.Usuario)
def create_user(user: schemas.UsuarioCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(admin_required)):
    db_user = db.query(models.Usuario).filter(models.Usuario.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    hashed = get_password_hash(user.password)
    new_user = models.Usuario(
        username=user.username,
        hashed_password=hashed,
        role=user.role,
        privilege=user.privilege or 'Ver',
        empresa_id=user.empresa_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

class UsuarioUpdate(BaseModel):
    username: str
    role: str
    privilege: str = 'Ver'
    empresa_id: Optional[int] = None

@app.put("/users/{user_id}", response_model=schemas.Usuario)
def update_user(user_id: int, user: UsuarioUpdate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(admin_required)):
    db_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    # Verificar que el nuevo username no lo tenga otro usuario
    existing = db.query(models.Usuario).filter(models.Usuario.username == user.username, models.Usuario.id != user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    db_user.username = user.username
    db_user.role = user.role
    db_user.privilege = user.privilege
    db_user.empresa_id = user.empresa_id
    db.commit()
    db.refresh(db_user)
    return db_user

class ResetPasswordRequest(BaseModel):
    new_password: str

@app.patch("/users/{user_id}/reset-password", response_model=schemas.Usuario)
def reset_user_password(user_id: int, req: ResetPasswordRequest, db: Session = Depends(get_db), current_user: models.Usuario = Depends(admin_required)):
    db_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db_user.hashed_password = get_password_hash(req.new_password)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(admin_required)):
    db_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(db_user)
    db.commit()
    return None

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

def text_formatter(text: str) -> str:
    """Convierte a MAYUSCULAS y elimina puntuacion"""
    if not text:
        return text
    text = text.upper()
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

@app.get("/empresas/", response_model=list[schemas.Empresa])
def read_empresas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    empresas = db.query(models.Empresa).filter(models.Empresa.activo == True).offset(skip).limit(limit).all()
    return empresas

@app.get("/empresas/informe/")
def search_informe(q: str = "", db: Session = Depends(get_db)):
    """Search endpoint for the Informe de Estado selector."""
    query = db.query(models.Empresa)
    if q:
        query = query.filter(models.Empresa.nombre.ilike(f"%{q}%") | models.Empresa.cuit.ilike(f"%{q}%"))
    empresas = query.limit(20).all()
    return [{"id": e.id, "nombre": e.nombre, "cuit": e.cuit} for e in empresas]

@app.get("/empresas/{empresa_id}/informe")
def get_empresa_informe(empresa_id: int, db: Session = Depends(get_db)):
    """Full company dashboard: company + vigiladores with license status + tramites per jurisdiction."""
    from datetime import date, timedelta, datetime

    def normalize_date(value):
        if value in (None, ""):
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None

    hoy = date.today()
    umbral = hoy + timedelta(days=30)

    emp = db.query(models.Empresa).filter(models.Empresa.id == empresa_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    tipos_tramite = db.query(models.TipoTramite).all()

    asignaciones = db.query(models.Asignacion).filter(models.Asignacion.empresa_id == empresa_id, models.Asignacion.activa == True).all()

    vigiladores_detalle = []
    for asig in asignaciones:
        vig = asig.vigilador
        if not vig or not vig.activo:
            continue
        vto = normalize_date(vig.fecha_vencimiento_hab)
        if vto is None:
            estado_hab = "Sin fecha"
        elif vto < hoy:
            estado_hab = "VENCIDO"
        elif vto <= umbral:
            estado_hab = "POR VENCER"
        else:
            estado_hab = "HABILITADO"

        # Collect roles and tramites for this vigilador in this company
        roles_info = []
        for ar in asig.roles:
            if not ar.activo:
                continue
            rol_nombre = ar.rol.nombre if ar.rol else "?"
            tramites_info = []
            for t in ar.tramites:
                tipo_nombre = t.tipo_tramite.nombre if t.tipo_tramite else "?"
                total = len(t.requisitos)
                aprobados = sum(1 for r in t.requisitos if r.estado == "Aprobado")
                tramites_info.append({
                    "tipo": tipo_nombre,
                    "estado": t.estado,
                    "total_requisitos": total,
                    "aprobados": aprobados
                })
            roles_info.append({"rol": rol_nombre, "tramites": tramites_info})

        vigiladores_detalle.append({
            "id": vig.id,
            "nombre_completo": vig.nombre_completo,
            "dni": vig.dni,
            "legajo": vig.legajo,
            "fecha_vencimiento_hab": str(vto) if vto else None,
            "estado_habilitacion": estado_hab,
            "roles": roles_info
        })

    # Company tramites summary across jurisdictions
    # 1. Start with Company's own habilitations
    juris_dict = {}
    for t in tipos_tramite:
        juris_dict[t.nombre] = {
            "estado": "Sin trámite",
            "id": None,
            "pendientes": [], # Show all pending strings
            "tipo": "Empresa"
        }

    # Company-level tramites
    company_tramites = db.query(models.DocumentoTramite).filter(models.DocumentoTramite.empresa_id == empresa_id).all()
    for tram in company_tramites:
        tipo = tram.tipo_tramite.nombre if tram.tipo_tramite else "?"
        pendientes = []
        if tram.estado != "Completo":
            for req in tram.requisitos:
                if req.estado != "Aprobado":
                    desc = req.plantilla.descripcion if req.plantilla else f"Requisito #{req.id}"
                    pendientes.append(f"[Empresa] {desc}")
        
        juris_dict[tipo] = {
            "estado": tram.estado,
            "id": tram.id,
            "pendientes": pendientes,
            "tipo": "Empresa"
        }

    # 2. Add Personnel tramites summary
    for asig in asignaciones:
        vig = db.query(models.Vigilador).filter(models.Vigilador.id == asig.vigilador_id).first()
        vig_nombre = vig.nombre_completo if vig else "Personal"
        for ar in asig.roles:
            for tram in ar.tramites:
                tipo = tram.tipo_tramite.nombre if tram.tipo_tramite else "?"
                if tipo not in juris_dict: continue # Should be seeded

                if tram.estado != "Completo":
                    for req in tram.requisitos:
                        if req.estado != "Aprobado":
                            desc = req.plantilla.descripcion if req.plantilla else f"Req #{req.id}"
                            juris_dict[tipo]["pendientes"].append(f"[{vig_nombre}] {desc}")
                
                # If company status is "Sin trámite", maybe show personnel status
                if juris_dict[tipo]["estado"] == "Sin trámite":
                    juris_dict[tipo]["estado"] = f"Personal: {tram.estado}"
                    juris_dict[tipo]["id"] = tram.id # Link to personnel if no company one exists

    # Format for easy frontend consumption
    jurisdicciones = []
    for name, info in juris_dict.items():
        jurisdicciones.append({"nombre": name, **info})

    # Company license status
    vto_emp = normalize_date(emp.fecha_vencimiento_hab)
    if vto_emp is None:
        estado_emp = "Sin fecha"
    elif vto_emp < hoy:
        estado_emp = "VENCIDO"
    elif vto_emp <= umbral:
        estado_emp = "POR VENCER"
    else:
        estado_emp = "HABILITADO"

    return {
        "empresa": {
            "id": emp.id,
            "nombre": emp.nombre,
            "cuit": emp.cuit,
            "direccion": emp.direccion,
            "telefono": emp.telefono,
            "email": emp.email,
            "fecha_alta": str(emp.fecha_alta) if emp.fecha_alta else None,
            "fecha_vencimiento_hab": str(emp.fecha_vencimiento_hab) if emp.fecha_vencimiento_hab else None,
            "estado_habilitacion": estado_emp,
            "jurisdicciones": emp.jurisdicciones # New field
        },
        "vigiladores": vigiladores_detalle,
        "jurisdicciones": jurisdicciones
    }

@app.get("/empresas/todos/", response_model=list[schemas.Empresa])
def read_todas_empresas(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    """Devuelve todas las empresas incluyendo archivadas - para el buscador global"""
    return db.query(models.Empresa).offset(skip).limit(limit).all()

@app.patch("/empresas/{empresa_id}/toggle-activo", response_model=schemas.Empresa)
def toggle_empresa_activo(empresa_id: int, db: Session = Depends(get_db)):
    db_emp = db.query(models.Empresa).filter(models.Empresa.id == empresa_id).first()
    if not db_emp:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    db_emp.activo = not db_emp.activo
    db.commit()
    db.refresh(db_emp)
    return db_emp

@app.post("/empresas/", response_model=schemas.Empresa)
def create_empresa(empresa: schemas.EmpresaCreate, db: Session = Depends(get_db)):
    db_empresa = db.query(models.Empresa).filter(models.Empresa.cuit == empresa.cuit).first()
    if db_empresa:
        raise HTTPException(status_code=400, detail="Empresa ya registrada")
    
    # Formateo de mayusculas y sin puntuacion
    nombre_formateado = text_formatter(empresa.nombre)
    
    new_empresa = models.Empresa(
        nombre=nombre_formateado, 
        cuit=empresa.cuit,
        direccion=empresa.direccion,
        telefono=empresa.telefono,
        email=empresa.email,
        fecha_alta=empresa.fecha_alta,
        fecha_vencimiento_hab=empresa.fecha_vencimiento_hab,
        jurisdicciones=empresa.jurisdicciones
    )
    db.add(new_empresa)
    db.commit()
    db.refresh(new_empresa)
    return new_empresa

@app.put("/empresas/{empresa_id}", response_model=schemas.Empresa)
def update_empresa(empresa_id: int, empresa: schemas.EmpresaCreate, db: Session = Depends(get_db)):
    db_empresa = db.query(models.Empresa).filter(models.Empresa.id == empresa_id).first()
    if not db_empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    db_empresa.nombre = text_formatter(empresa.nombre)
    db_empresa.cuit = empresa.cuit
    db_empresa.direccion = empresa.direccion
    db_empresa.telefono = empresa.telefono
    db_empresa.email = empresa.email
    db_empresa.fecha_alta = empresa.fecha_alta
    db_empresa.fecha_vencimiento_hab = empresa.fecha_vencimiento_hab
    db_empresa.jurisdicciones = empresa.jurisdicciones
    db.commit()
    db.refresh(db_empresa)
    return db_empresa

@app.delete("/empresas/{empresa_id}")
def delete_empresa(empresa_id: int, db: Session = Depends(get_db)):
    db_emp = db.query(models.Empresa).filter(models.Empresa.id == empresa_id).first()
    if not db_emp:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    db_emp.activo = False  # soft-delete
    db.commit()
    return {"ok": True}

@app.post("/empresas/{empresa_id}/tramites/{tipo_tramite_id}", response_model=schemas.DocumentoTramite)
def create_empresa_tramite(empresa_id: int, tipo_tramite_id: int, db: Session = Depends(get_db)):
    # Check if exists
    existing = db.query(models.DocumentoTramite).filter(
        models.DocumentoTramite.empresa_id == empresa_id,
        models.DocumentoTramite.tipo_tramite_id == tipo_tramite_id
    ).first()
    if existing:
        return existing
        
    db_tramite = models.DocumentoTramite(
        empresa_id=empresa_id,
        tipo_tramite_id=tipo_tramite_id,
        estado="Pendiente"
    )
    db.add(db_tramite)
    db.commit()
    db.refresh(db_tramite)
    
    # Auto-generate requirements based on plantillas for Empresa
    plantillas = db.query(models.RequisitoPlantilla).filter(
        models.RequisitoPlantilla.tipo_tramite_id == tipo_tramite_id,
        models.RequisitoPlantilla.es_para_empresa == True
    ).all()
    
    for p in plantillas:
        db_req = models.DocumentoRequisito(
            tramite_id=db_tramite.id,
            plantilla_id=p.id,
            estado="Faltante"
        )
        db.add(db_req)
    
    db.commit()
    db.refresh(db_tramite)
    return db_tramite

@app.get("/vigiladores/", response_model=list[schemas.Vigilador])
def read_vigiladores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    vigiladores = db.query(models.Vigilador).filter(models.Vigilador.activo == True).offset(skip).limit(limit).all()
    return vigiladores

@app.get("/vigiladores/todos/", response_model=list[schemas.Vigilador])
def read_todos_vigiladores(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    """Devuelve todos los vigiladores incluyendo archivados - para el buscador global"""
    return db.query(models.Vigilador).offset(skip).limit(limit).all()

@app.patch("/vigiladores/{vigilador_id}/toggle-activo", response_model=schemas.Vigilador)
def toggle_vigilador_activo(vigilador_id: int, db: Session = Depends(get_db)):
    db_vig = db.query(models.Vigilador).filter(models.Vigilador.id == vigilador_id).first()
    if not db_vig:
        raise HTTPException(status_code=404, detail="Vigilador no encontrado")
    db_vig.activo = not db_vig.activo
    db.commit()
    db.refresh(db_vig)
    return db_vig

@app.delete("/vigiladores/{vigilador_id}")
def delete_vigilador(vigilador_id: int, db: Session = Depends(get_db)):
    db_vig = db.query(models.Vigilador).filter(models.Vigilador.id == vigilador_id).first()
    if not db_vig:
        raise HTTPException(status_code=404, detail="Vigilador no encontrado")
    db_vig.activo = False  # soft-delete
    db.commit()
    return {"ok": True}

@app.post("/vigiladores/", response_model=schemas.Vigilador)
def create_vigilador(vigilador: schemas.VigiladorCreate, db: Session = Depends(get_db)):
    db_vigilador = db.query(models.Vigilador).filter(models.Vigilador.dni == vigilador.dni).first()
    if db_vigilador:
        raise HTTPException(status_code=400, detail="Vigilador ya registrado con ese DNI")
        
    nombre_formateado = text_formatter(vigilador.nombre_completo)
    
    new_vigilador = models.Vigilador(
        dni=vigilador.dni, 
        nombre_completo=nombre_formateado,
        domicilio=vigilador.domicilio,
        telefono=vigilador.telefono,
        legajo=vigilador.legajo,
        fecha_alta=vigilador.fecha_alta,
        fecha_vencimiento_hab=vigilador.fecha_vencimiento_hab
    )
    db.add(new_vigilador)
    db.commit()
    db.refresh(new_vigilador)
    return new_vigilador

@app.put("/vigiladores/{vigilador_id}", response_model=schemas.Vigilador)
def update_vigilador(vigilador_id: int, vigilador: schemas.VigiladorCreate, db: Session = Depends(get_db)):
    db_vig = db.query(models.Vigilador).filter(models.Vigilador.id == vigilador_id).first()
    if not db_vig:
        raise HTTPException(status_code=404, detail="Vigilador no encontrado")
    db_vig.nombre_completo = text_formatter(vigilador.nombre_completo)
    db_vig.dni = vigilador.dni
    db_vig.domicilio = vigilador.domicilio
    db_vig.telefono = vigilador.telefono
    db_vig.legajo = vigilador.legajo
    db_vig.fecha_alta = vigilador.fecha_alta
    db_vig.fecha_vencimiento_hab = vigilador.fecha_vencimiento_hab
    db.commit()
    db.refresh(db_vig)
    return db_vig

# --- ROLES ---
@app.get("/roles/", response_model=list[schemas.Rol])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Rol).offset(skip).limit(limit).all()

@app.post("/roles/", response_model=schemas.Rol)
def create_rol(rol: schemas.RolBase, db: Session = Depends(get_db)):
    db_rol = db.query(models.Rol).filter(models.Rol.nombre == rol.nombre).first()
    if db_rol:
        raise HTTPException(status_code=400, detail="Rol ya existe")
    new_rol = models.Rol(nombre=rol.nombre)
    db.add(new_rol)
    db.commit()
    db.refresh(new_rol)
    return new_rol

# --- ASIGNACIONES (Empresa - Vigilador) ---
@app.get("/asignaciones/", response_model=list[schemas.Asignacion])
def read_asignaciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Asignacion).offset(skip).limit(limit).all()

@app.post("/asignaciones/", response_model=schemas.Asignacion)
def create_asignacion(asignacion: schemas.AsignacionCreate, db: Session = Depends(get_db)):
    # 1. Validar que no haya una asignación activa igual
    db_asignacion = db.query(models.Asignacion).filter(
        models.Asignacion.vigilador_id == asignacion.vigilador_id,
        models.Asignacion.empresa_id == asignacion.empresa_id,
        models.Asignacion.activa == True
    ).first()
    if db_asignacion:
        raise HTTPException(status_code=400, detail="Ya existe una asignación activa para este vigilador en esta empresa")
    
    new_asignacion = models.Asignacion(
        vigilador_id=asignacion.vigilador_id, 
        empresa_id=asignacion.empresa_id,
        activa=asignacion.activa
    )
    db.add(new_asignacion)
    db.commit()
    db.refresh(new_asignacion)
    return new_asignacion

# --- ASIGNACIÓN DE ROL ---
class AsignacionRolCreateReq(schemas.AsignacionRolBase):
    asignacion_id: int
    rol_id: int

@app.post("/asignaciones/{asignacion_id}/roles/", response_model=schemas.AsignacionRol)
def create_asignacion_rol(asignacion_id: int, req: AsignacionRolCreateReq, db: Session = Depends(get_db)):
    # Validar si ya lo tiene activo
    db_rol_activo = db.query(models.AsignacionRol).filter(
        models.AsignacionRol.asignacion_id == asignacion_id,
        models.AsignacionRol.rol_id == req.rol_id,
        models.AsignacionRol.activo == True
    ).first()
    
    if db_rol_activo:
         raise HTTPException(status_code=400, detail="Este rol ya está asignado de forma activa")

    new_asig_rol = models.AsignacionRol(
        asignacion_id=asignacion_id,
        rol_id=req.rol_id,
        activo=req.activo
    )
    db.add(new_asig_rol)
    db.commit()
    db.refresh(new_asig_rol)
    return new_asig_rol

# --- TIPOS DE TRAMITE Y PLANTILLAS ---
@app.get("/tipos-tramites/", response_model=list[schemas.TipoTramite])
def read_tipos_tramites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.TipoTramite).offset(skip).limit(limit).all()

@app.post("/tipos-tramites/", response_model=schemas.TipoTramite)
def create_tipo_tramite(tipo: schemas.TipoTramiteBase, db: Session = Depends(get_db)):
    db_tipo = db.query(models.TipoTramite).filter(models.TipoTramite.nombre == tipo.nombre).first()
    if db_tipo:
        raise HTTPException(status_code=400, detail="Tipo de trámite ya existe")
    new_tipo = models.TipoTramite(nombre=tipo.nombre)
    db.add(new_tipo)
    db.commit()
    db.refresh(new_tipo)
    return new_tipo

# Endpoint para crear una plantilla (solo setup administrativo)
class RequisitoPlantillaCreate(BaseModel):
    rol_id: int
    tipo_tramite_id: int
    descripcion: str

@app.post("/plantillas/")
def create_plantilla(req: RequisitoPlantillaCreate, db: Session = Depends(get_db)):
    new_plantilla = models.RequisitoPlantilla(**req.model_dump())
    db.add(new_plantilla)
    db.commit()
    db.refresh(new_plantilla)
    return new_plantilla

# --- TRAMITES Y CHECKLIST ---
class DocumentoTramiteCreateReq(schemas.DocumentoTramiteBase):
    asignacion_rol_id: int | None = None
    empresa_id: int | None = None
    tipo_tramite_id: int

@app.get("/tramites/", response_model=list[schemas.DocumentoTramite])
def read_tramites(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    # Solo trámites activos, ordenados por fecha de creación desc
    tramites = db.query(models.DocumentoTramite).filter(
        models.DocumentoTramite.activo == True
    ).order_by(models.DocumentoTramite.fecha_creacion.desc()).offset(skip).limit(limit).all()
    
    # Inyectar descripción de la plantilla para el checklist (Crucial para EMPRESAS también)
    for t in tramites:
        for req in t.requisitos:
            if req.plantilla:
                req.descripcion_requisito = req.plantilla.descripcion # type: ignore
                
    return tramites

@app.patch("/tramites/{tramite_id}/toggle-activo", response_model=schemas.DocumentoTramite)
def toggle_tramite_activo(tramite_id: int, db: Session = Depends(get_db)):
    db_tram = db.query(models.DocumentoTramite).filter(models.DocumentoTramite.id == tramite_id).first()
    if not db_tram:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")
    db_tram.activo = not db_tram.activo
    db.commit()
    db.refresh(db_tram)
    return db_tram

@app.post("/tramites/", response_model=schemas.DocumentoTramite)
def create_tramite(req: DocumentoTramiteCreateReq, db: Session = Depends(get_db)):
    # 1. Verificar si ya existe un trámite idéntico
    query = db.query(models.DocumentoTramite).filter(
        models.DocumentoTramite.tipo_tramite_id == req.tipo_tramite_id
    )
    if req.asignacion_rol_id:
        query = query.filter(models.DocumentoTramite.asignacion_rol_id == req.asignacion_rol_id)
    elif req.empresa_id:
        query = query.filter(models.DocumentoTramite.empresa_id == req.empresa_id)
    else:
        raise HTTPException(status_code=400, detail="Debe proporcionar asignacion_rol_id o empresa_id")

    db_tramite = query.filter(models.DocumentoTramite.activo == True).first()
    if db_tramite:
        return db_tramite
        
    # 1.1 Validacion de Restriccion: Si es Personal, la Empresa debe tener tramite iniciado
    if req.asignacion_rol_id:
        asig_rol = db.query(models.AsignacionRol).get(req.asignacion_rol_id)
        if not asig_rol:
            raise HTTPException(status_code=404, detail="Asignación de rol no encontrada")
        empresa_id = asig_rol.asignacion.empresa_id
        
        # Buscar tramite de la empresa para esa jurisdiccion
        company_tramite = db.query(models.DocumentoTramite).filter(
            models.DocumentoTramite.empresa_id == empresa_id,
            models.DocumentoTramite.tipo_tramite_id == req.tipo_tramite_id,
            models.DocumentoTramite.activo == True
        ).first()
        
        if not company_tramite:
            # Informar al frontend para el popup sugerido
            # Aunque la logica de popup es frontend, aqui bloqueamos el proceso
            raise HTTPException(
                status_code=403, 
                detail="LA EMPRESA DEBE TENER INICIADOS SUS TRAMITES DE HABILITACION"
            )

    # 2. Crear el objeto Trámite
    new_tramite = models.DocumentoTramite(
        asignacion_rol_id=req.asignacion_rol_id,
        empresa_id=req.empresa_id,
        tipo_tramite_id=req.tipo_tramite_id,
        estado=req.estado
    )
    db.add(new_tramite)
    db.commit()
    db.refresh(new_tramite)

    # 3. Buscar Plantillas según el contexto (Empresa o Personal)
    if req.asignacion_rol_id:
        asig_rol = db.query(models.AsignacionRol).get(req.asignacion_rol_id)
        if not asig_rol:
            raise HTTPException(status_code=404, detail="Asignación de rol no encontrada")
        from sqlalchemy import or_
        plantillas = db.query(models.RequisitoPlantilla).filter(
            or_(
                models.RequisitoPlantilla.rol_id == asig_rol.rol_id,
                models.RequisitoPlantilla.rol_id == None
            ),
            models.RequisitoPlantilla.tipo_tramite_id == req.tipo_tramite_id,
            models.RequisitoPlantilla.es_para_empresa == False
        ).all()
    else:
        # Trámite de Empresa
        plantillas = db.query(models.RequisitoPlantilla).filter(
            models.RequisitoPlantilla.tipo_tramite_id == req.tipo_tramite_id,
            models.RequisitoPlantilla.es_para_empresa == True
        ).all()

    # 4. Generar DocumentoRequisito (Checklist)
    for p in plantillas:
        new_req = models.DocumentoRequisito(
            tramite_id=new_tramite.id,
            plantilla_id=p.id,
            estado="Faltante"
        )
        db.add(new_req)
    
    db.commit()
    db.refresh(new_tramite)
    return new_tramite

class RequisitoUpdate(BaseModel):
    archivo_url: str | None = None
    fecha_vencimiento: str | None = None # Date strings
    estado: str | None = None

@app.put("/requisitos/{requisito_id}")
def update_requisito(
    requisito_id: int,
    req: RequisitoUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    from datetime import datetime
    db_req = db.query(models.DocumentoRequisito).filter(models.DocumentoRequisito.id == requisito_id).first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requisito no encontrado")

    if req.estado == "Aprobado":
        has_attachment = db.query(models.DocumentoAdjunto).filter(
            models.DocumentoAdjunto.requisito_id == requisito_id,
            models.DocumentoAdjunto.activo == True
        ).first()
        if not has_attachment:
            raise HTTPException(
                status_code=400,
                detail="Debe adjuntar documentacion PDF antes de aprobar este requisito"
            )
    
    if req.archivo_url is not None:
        db_req.archivo_url = req.archivo_url
    if req.estado is not None:
        db_req.estado = req.estado
    if req.fecha_vencimiento:
        db_req.fecha_vencimiento = datetime.strptime(req.fecha_vencimiento, "%Y-%m-%d").date()
        
    db.commit()
    db.refresh(db_req)
    return db_req


def save_uploaded_pdf(file: UploadFile, target_path: str):
    mime_type = file.content_type or "application/octet-stream"
    validate_pdf_metadata(file.filename or "", mime_type=mime_type)
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)


def build_adjunto_payload(
    *,
    file: UploadFile,
    target_path: str,
    tipo_documento: str,
    current_user: models.Usuario,
    empresa_id: int | None = None,
    vigilador_id: int | None = None,
    tramite_id: int | None = None,
    requisito_id: int | None = None,
    jurisdiccion_referencia: str | None = None,
    tags: str | None = None,
    observaciones: str | None = None,
):
    return models.DocumentoAdjunto(
        empresa_id=empresa_id,
        vigilador_id=vigilador_id,
        tramite_id=tramite_id,
        requisito_id=requisito_id,
        usuario_carga_id=current_user.id if current_user else None,
        tipo_documento=tipo_documento,
        nombre_original=file.filename or "documento.pdf",
        nombre_archivo=os.path.basename(target_path),
        mime_type=file.content_type or "application/pdf",
        ruta_archivo=target_path,
        hash_sha256=compute_file_sha256(target_path),
        jurisdiccion_referencia=jurisdiccion_referencia,
        tags=tags,
        estado_extraccion="Pendiente",
        observaciones=observaciones
    )


def build_biblioteca_payload(
    *,
    file: UploadFile,
    target_path: str,
    titulo: str,
    categoria: str,
    current_user: models.Usuario,
    jurisdiccion: str | None = None,
    organismo: str | None = None,
    tema: str | None = None,
    fecha_documento: str | None = None,
    vigencia: str | None = None,
    tags: str | None = None,
    empresa_id: int | None = None,
    vigilador_id: int | None = None,
    observaciones: str | None = None,
):
    resumen_referencia = " / ".join(part for part in [categoria, jurisdiccion, tema or titulo] if part)
    return models.BibliotecaDocumento(
        titulo=titulo,
        categoria=categoria,
        jurisdiccion=jurisdiccion,
        organismo=organismo,
        tema=tema,
        fecha_documento=fecha_documento,
        vigencia=vigencia,
        tags=tags,
        empresa_id=empresa_id,
        vigilador_id=vigilador_id,
        usuario_carga_id=current_user.id if current_user else None,
        nombre_original=file.filename or "documento.pdf",
        nombre_archivo=os.path.basename(target_path),
        mime_type=file.content_type or "application/pdf",
        ruta_archivo=target_path,
        hash_sha256=compute_file_sha256(target_path),
        estado_extraccion="Pendiente",
        resumen_referencia=resumen_referencia,
        observaciones=observaciones,
    )


@app.get("/biblioteca/", response_model=list[schemas.BibliotecaDocumento])
def list_biblioteca_documentos(
    q: str | None = None,
    categoria: str | None = None,
    jurisdiccion: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    query = db.query(models.BibliotecaDocumento).filter(models.BibliotecaDocumento.activo == True)

    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            models.BibliotecaDocumento.titulo.ilike(search)
            | models.BibliotecaDocumento.tema.ilike(search)
            | models.BibliotecaDocumento.organismo.ilike(search)
            | models.BibliotecaDocumento.tags.ilike(search)
            | models.BibliotecaDocumento.resumen_referencia.ilike(search)
            | models.BibliotecaDocumento.texto_extraido.ilike(search)
        )

    if categoria:
        query = query.filter(models.BibliotecaDocumento.categoria == categoria)

    if jurisdiccion:
        query = query.filter(models.BibliotecaDocumento.jurisdiccion == jurisdiccion)

    return query.order_by(models.BibliotecaDocumento.fecha_carga.desc()).all()


@app.post("/biblioteca/upload", response_model=schemas.BibliotecaDocumento)
def upload_biblioteca_documento(
    titulo: str = Form(...),
    categoria: str = Form(...),
    jurisdiccion: str | None = Form(None),
    organismo: str | None = Form(None),
    tema: str | None = Form(None),
    fecha_documento: str | None = Form(None),
    vigencia: str | None = Form(None),
    tags: str | None = Form(None),
    empresa_id: int | None = Form(None),
    vigilador_id: int | None = Form(None),
    observaciones: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    categoria_normalizada = (categoria or "").strip() or "Biblioteca documental"
    target_path = build_library_document_path(categoria_normalizada, file.filename or "documento.pdf")
    save_uploaded_pdf(file, target_path)

    documento = build_biblioteca_payload(
        file=file,
        target_path=target_path,
        titulo=titulo.strip(),
        categoria=categoria_normalizada,
        jurisdiccion=jurisdiccion.strip() if jurisdiccion else None,
        organismo=organismo.strip() if organismo else None,
        tema=tema.strip() if tema else None,
        fecha_documento=fecha_documento.strip() if fecha_documento else None,
        vigencia=vigencia.strip() if vigencia else None,
        tags=tags.strip() if tags else None,
        empresa_id=empresa_id,
        vigilador_id=vigilador_id,
        observaciones=observaciones.strip() if observaciones else None,
        current_user=current_user
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento


@app.get("/biblioteca/{documento_id}/view")
def view_biblioteca_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    documento = db.query(models.BibliotecaDocumento).filter(
        models.BibliotecaDocumento.id == documento_id,
        models.BibliotecaDocumento.activo == True
    ).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento de biblioteca no encontrado")
    if not os.path.exists(documento.ruta_archivo):
        raise HTTPException(status_code=404, detail="El archivo asociado no existe en storage")

    return FileResponse(
        documento.ruta_archivo,
        media_type=documento.mime_type or "application/pdf",
        filename=documento.nombre_original
    )


@app.get("/documentos/empresa/{empresa_id}", response_model=list[schemas.DocumentoAdjunto])
def list_empresa_documents(empresa_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    return db.query(models.DocumentoAdjunto).filter(
        models.DocumentoAdjunto.empresa_id == empresa_id,
        models.DocumentoAdjunto.activo == True
    ).order_by(models.DocumentoAdjunto.fecha_carga.desc()).all()


@app.get("/documentos/vigilador/{vigilador_id}", response_model=list[schemas.DocumentoAdjunto])
def list_vigilador_documents(vigilador_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    return db.query(models.DocumentoAdjunto).filter(
        models.DocumentoAdjunto.vigilador_id == vigilador_id,
        models.DocumentoAdjunto.activo == True
    ).order_by(models.DocumentoAdjunto.fecha_carga.desc()).all()


@app.get("/documentos/requisito/{requisito_id}", response_model=list[schemas.DocumentoAdjunto])
def list_requisito_documents(requisito_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    return db.query(models.DocumentoAdjunto).filter(
        models.DocumentoAdjunto.requisito_id == requisito_id,
        models.DocumentoAdjunto.activo == True
    ).order_by(models.DocumentoAdjunto.fecha_carga.desc()).all()


@app.get("/documentos/{documento_id}/view")
def view_documento_adjunto(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    documento = db.query(models.DocumentoAdjunto).filter(
        models.DocumentoAdjunto.id == documento_id,
        models.DocumentoAdjunto.activo == True
    ).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento adjunto no encontrado")
    if not os.path.exists(documento.ruta_archivo):
        raise HTTPException(status_code=404, detail="El archivo asociado no existe en storage")

    return FileResponse(
        documento.ruta_archivo,
        media_type=documento.mime_type or "application/pdf",
        filename=documento.nombre_original
    )


@app.post("/documentos/empresa/{empresa_id}/upload", response_model=schemas.DocumentoAdjunto)
def upload_empresa_document(
    empresa_id: int,
    tipo_documento: str = Form(...),
    observaciones: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    empresa = db.query(models.Empresa).filter(models.Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    target_path = build_document_path("empresa", empresa_id, file.filename or "documento.pdf")
    save_uploaded_pdf(file, target_path)
    jurisdiccion_referencia = empresa.jurisdicciones or None

    adjunto = build_adjunto_payload(
        file=file,
        target_path=target_path,
        tipo_documento=tipo_documento,
        observaciones=observaciones,
        empresa_id=empresa_id,
        jurisdiccion_referencia=jurisdiccion_referencia,
        tags=tipo_documento,
        current_user=current_user
    )
    db.add(adjunto)
    db.commit()
    db.refresh(adjunto)
    return adjunto


@app.post("/documentos/vigilador/{vigilador_id}/upload", response_model=schemas.DocumentoAdjunto)
def upload_vigilador_document(
    vigilador_id: int,
    tipo_documento: str = Form(...),
    observaciones: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    vigilador = db.query(models.Vigilador).filter(models.Vigilador.id == vigilador_id).first()
    if not vigilador:
        raise HTTPException(status_code=404, detail="Vigilador no encontrado")

    target_path = build_document_path("vigilador", vigilador_id, file.filename or "documento.pdf")
    save_uploaded_pdf(file, target_path)
    asignacion = db.query(models.Asignacion).filter(
        models.Asignacion.vigilador_id == vigilador_id,
        models.Asignacion.activa == True
    ).first()
    empresa = asignacion.empresa if asignacion else None

    adjunto = build_adjunto_payload(
        file=file,
        target_path=target_path,
        tipo_documento=tipo_documento,
        observaciones=observaciones,
        vigilador_id=vigilador_id,
        jurisdiccion_referencia=empresa.jurisdicciones if empresa else None,
        tags=tipo_documento,
        current_user=current_user
    )
    db.add(adjunto)
    db.commit()
    db.refresh(adjunto)
    return adjunto


@app.post("/documentos/requisito/{requisito_id}/upload", response_model=schemas.DocumentoAdjunto)
def upload_requisito_document(
    requisito_id: int,
    tipo_documento: str = Form(...),
    observaciones: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    requisito = db.query(models.DocumentoRequisito).filter(models.DocumentoRequisito.id == requisito_id).first()
    if not requisito:
        raise HTTPException(status_code=404, detail="Requisito no encontrado")

    tramite = requisito.tramite
    if not tramite:
        raise HTTPException(status_code=400, detail="El requisito no tiene tramite asociado")

    empresa_id = tramite.empresa_id
    vigilador_id = None

    if tramite.asignacion_rol and tramite.asignacion_rol.asignacion:
        empresa_id = tramite.asignacion_rol.asignacion.empresa_id
        vigilador_id = tramite.asignacion_rol.asignacion.vigilador_id

    tipo_tramite = tramite.tipo_tramite.nombre if tramite.tipo_tramite else None

    if vigilador_id is not None:
        target_path = build_document_path("vigilador", vigilador_id, file.filename or "documento.pdf")
    elif empresa_id is not None:
        target_path = build_document_path("empresa", empresa_id, file.filename or "documento.pdf")
    else:
        raise HTTPException(status_code=400, detail="No se pudo determinar el ente asociado al requisito")

    save_uploaded_pdf(file, target_path)

    adjunto = build_adjunto_payload(
        file=file,
        target_path=target_path,
        tipo_documento=tipo_documento,
        observaciones=observaciones,
        empresa_id=empresa_id,
        vigilador_id=vigilador_id,
        tramite_id=tramite.id,
        requisito_id=requisito_id,
        jurisdiccion_referencia=tipo_tramite,
        tags=f"{tipo_documento},{tipo_tramite}" if tipo_tramite else tipo_documento,
        current_user=current_user
    )
    db.add(adjunto)

    requisito.archivo_url = target_path
    if requisito.estado == "Faltante":
        requisito.estado = "Subido"

    db.commit()
    db.refresh(adjunto)
    return adjunto
