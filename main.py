from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

import models
import schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app = FastAPI(title="HLConsulting API", description="API para gestión de habilitaciones")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

import re

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
    from datetime import date, timedelta
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
        vto = vig.fecha_vencimiento_hab
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
    vto_emp = emp.fecha_vencimiento_hab
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
    # Solo trámites activos
    tramites = db.query(models.DocumentoTramite).filter(models.DocumentoTramite.activo == True).offset(skip).limit(limit).all()
    # Inyectar descripción de la plantilla para el checklist si es necesario (opcional si se usa relationship)
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
def update_requisito(requisito_id: int, req: RequisitoUpdate, db: Session = Depends(get_db)):
    from datetime import datetime
    db_req = db.query(models.DocumentoRequisito).filter(models.DocumentoRequisito.id == requisito_id).first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requisito no encontrado")
    
    if req.archivo_url is not None:
        db_req.archivo_url = req.archivo_url
    if req.estado is not None:
        db_req.estado = req.estado
    if req.fecha_vencimiento:
        db_req.fecha_vencimiento = datetime.strptime(req.fecha_vencimiento, "%Y-%m-%d").date()
        
    db.commit()
    db.refresh(db_req)
    return db_req

