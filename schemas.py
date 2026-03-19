from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class EmpresaBase(BaseModel):
    nombre: str
    cuit: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    fecha_alta: Optional[date] = None
    fecha_vencimiento_hab: Optional[date] = None
    activo: Optional[bool] = True
    jurisdicciones: Optional[str] = None

class EmpresaCreate(EmpresaBase):
    pass

class Empresa(EmpresaBase):
    id: int

    class Config:
        from_attributes = True

class VigiladorBase(BaseModel):
    dni: str
    nombre_completo: str
    domicilio: Optional[str] = None
    telefono: Optional[str] = None
    legajo: Optional[str] = None
    fecha_alta: Optional[date] = None
    fecha_vencimiento_hab: Optional[date] = None
    activo: Optional[bool] = True

class VigiladorCreate(VigiladorBase):
    pass

class Vigilador(VigiladorBase):
    id: int

    class Config:
        from_attributes = True

class RolBase(BaseModel):
    nombre: str

class Rol(RolBase):
    id: int
    class Config:
        from_attributes = True

class TipoTramiteBase(BaseModel):
    nombre: str

class TipoTramite(TipoTramiteBase):
    id: int
    class Config:
        from_attributes = True

class DocumentoRequisitoBase(BaseModel):
    archivo_url: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    estado: str = "Faltante"

class DocumentoRequisito(DocumentoRequisitoBase):
    id: int
    tramite_id: int
    plantilla_id: int
    descripcion_requisito: Optional[str] = None  # filled from RequisitoPlantilla.descripcion
    
    class Config:
        from_attributes = True

class DocumentoTramiteBase(BaseModel):
    estado: str = "Pendiente"

class DocumentoTramite(DocumentoTramiteBase):
    id: int
    asignacion_rol_id: Optional[int] = None
    empresa_id: Optional[int] = None
    tipo_tramite_id: int
    requisitos: List[DocumentoRequisito] = []

    class Config:
        from_attributes = True

class AsignacionRolBase(BaseModel):
    activo: bool = True

class AsignacionRol(AsignacionRolBase):
    id: int
    asignacion_id: int
    rol_id: int
    tramites: List[DocumentoTramite] = []

    class Config:
        from_attributes = True

class AsignacionBase(BaseModel):
    activa: bool = True

class AsignacionCreate(AsignacionBase):
    empresa_id: int
    vigilador_id: int

class Asignacion(AsignacionBase):
    id: int
    vigilador_id: int
    empresa_id: int
    roles: List[AsignacionRol] = []

    class Config:
        from_attributes = True
