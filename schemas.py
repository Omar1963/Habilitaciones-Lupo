from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class UsuarioBase(BaseModel):
    username: str
    role: str
    privilege: Optional[str] = 'Ver'  # 'Admin', 'Editar', 'Ver'
    empresa_id: Optional[int] = None

class UsuarioCreate(UsuarioBase):
    password: str

class Usuario(UsuarioBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

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
    fecha_vencimiento: Optional[str] = None
    estado: str = "Faltante"

class DocumentoRequisito(DocumentoRequisitoBase):
    id: int
    tramite_id: int
    plantilla_id: int
    descripcion_requisito: Optional[str] = None  # filled from RequisitoPlantilla.descripcion
    
    class Config:
        from_attributes = True

class DocumentoAdjuntoBase(BaseModel):
    empresa_id: Optional[int] = None
    vigilador_id: Optional[int] = None
    tramite_id: Optional[int] = None
    requisito_id: Optional[int] = None
    usuario_carga_id: Optional[int] = None
    tipo_documento: str
    nombre_original: str
    nombre_archivo: str
    mime_type: Optional[str] = None
    ruta_archivo: str
    hash_sha256: Optional[str] = None
    jurisdiccion_referencia: Optional[str] = None
    tags: Optional[str] = None
    estado_extraccion: Optional[str] = "Pendiente"
    texto_extraido: Optional[str] = None
    observaciones: Optional[str] = None
    activo: Optional[bool] = True

class DocumentoAdjuntoCreate(DocumentoAdjuntoBase):
    pass

class DocumentoAdjunto(DocumentoAdjuntoBase):
    id: int
    fecha_carga: Optional[str] = None

    class Config:
        from_attributes = True


class BibliotecaDocumentoBase(BaseModel):
    titulo: str
    categoria: str
    jurisdiccion: Optional[str] = None
    organismo: Optional[str] = None
    tema: Optional[str] = None
    fecha_documento: Optional[str] = None
    vigencia: Optional[str] = None
    tags: Optional[str] = None
    empresa_id: Optional[int] = None
    vigilador_id: Optional[int] = None
    usuario_carga_id: Optional[int] = None
    nombre_original: str
    nombre_archivo: str
    mime_type: Optional[str] = None
    ruta_archivo: str
    hash_sha256: Optional[str] = None
    estado_extraccion: Optional[str] = "Pendiente"
    texto_extraido: Optional[str] = None
    resumen_referencia: Optional[str] = None
    observaciones: Optional[str] = None
    activo: Optional[bool] = True


class BibliotecaDocumentoCreate(BibliotecaDocumentoBase):
    pass


class BibliotecaDocumento(BibliotecaDocumentoBase):
    id: int
    fecha_carga: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentoTramiteBase(BaseModel):
    estado: str = "Pendiente"

class DocumentoTramite(DocumentoTramiteBase):
    id: int
    estado: str
    activo: bool
    fecha_creacion: Optional[str] = None
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
