from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String) # 'Admin', 'Cliente', 'Consultor'
    privilege = Column(String, default='Ver') # 'Admin', 'Editar', 'Ver'
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=True)
    
    empresa = relationship("Empresa")
    documentos_cargados = relationship("DocumentoAdjunto", back_populates="usuario_carga")
    biblioteca_documentos = relationship("BibliotecaDocumento", back_populates="usuario_carga")


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    cuit = Column(String, unique=True, index=True)
    direccion = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    fecha_alta = Column(String, nullable=True)
    fecha_vencimiento_hab = Column(String, nullable=True)
    activo = Column(Boolean, default=True)  # False = archivado (soft-delete)
    jurisdicciones = Column(String, nullable=True) # Comma separated list like "CABA,PBA,PSA"

    asignaciones = relationship("Asignacion", back_populates="empresa")
    tramites_propios = relationship("DocumentoTramite", back_populates="empresa")
    documentos_adjuntos = relationship("DocumentoAdjunto", back_populates="empresa")
    biblioteca_documentos = relationship("BibliotecaDocumento", back_populates="empresa")

class Vigilador(Base):
    __tablename__ = "vigiladores"

    id = Column(Integer, primary_key=True, index=True)
    dni = Column(String, unique=True, index=True)
    nombre_completo = Column(String)
    domicilio = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    legajo = Column(String, nullable=True)
    fecha_alta = Column(String, nullable=True)
    fecha_vencimiento_hab = Column(String, nullable=True)
    activo = Column(Boolean, default=True)  # False = archivado (soft-delete)
    
    asignaciones = relationship("Asignacion", back_populates="vigilador")
    documentos_adjuntos = relationship("DocumentoAdjunto", back_populates="vigilador")
    biblioteca_documentos = relationship("BibliotecaDocumento", back_populates="vigilador")

class Asignacion(Base):
    __tablename__ = "asignaciones"

    id = Column(Integer, primary_key=True, index=True)
    vigilador_id = Column(Integer, ForeignKey("vigiladores.id"))
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    activa = Column(Boolean, default=True)

    vigilador = relationship("Vigilador", back_populates="asignaciones")
    empresa = relationship("Empresa", back_populates="asignaciones")
    roles = relationship("AsignacionRol", back_populates="asignacion")

class Rol(Base):
    __tablename__ = "roles"
    # Operador, Vigilador, Tecnico
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)

class AsignacionRol(Base):
    __tablename__ = "asignacion_roles"

    id = Column(Integer, primary_key=True, index=True)
    asignacion_id = Column(Integer, ForeignKey("asignaciones.id"))
    rol_id = Column(Integer, ForeignKey("roles.id"))
    activo = Column(Boolean, default=True)

    asignacion = relationship("Asignacion", back_populates="roles")
    rol = relationship("Rol")
    tramites = relationship("DocumentoTramite", back_populates="asignacion_rol")

class TipoTramite(Base):
    __tablename__ = "tipo_tramites"
    # PBA, CABA, ANMAC, PNA
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)

class RequisitoPlantilla(Base):
    __tablename__ = "requisitos_plantilla"
    
    id = Column(Integer, primary_key=True, index=True)
    rol_id = Column(Integer, ForeignKey("roles.id"))
    tipo_tramite_id = Column(Integer, ForeignKey("tipo_tramites.id"))
    descripcion = Column(String)
    dias_validez = Column(Integer, nullable=True) # For legal defaults
    es_para_empresa = Column(Boolean, default=False)

    rol = relationship("Rol")
    tipo_tramite = relationship("TipoTramite")

class DocumentoTramite(Base):
    __tablename__ = "documento_tramites"

    id = Column(Integer, primary_key=True, index=True)
    asignacion_rol_id = Column(Integer, ForeignKey("asignacion_roles.id"), nullable=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=True)
    tipo_tramite_id = Column(Integer, ForeignKey("tipo_tramites.id"))
    estado = Column(String, default="Pendiente") # Pendiente, Completo
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))

    asignacion_rol = relationship("AsignacionRol", back_populates="tramites")
    empresa = relationship("Empresa", back_populates="tramites_propios")
    tipo_tramite = relationship("TipoTramite")
    requisitos = relationship("DocumentoRequisito", back_populates="tramite")
    documentos_adjuntos = relationship("DocumentoAdjunto", back_populates="tramite")

class DocumentoRequisito(Base):
    __tablename__ = "documento_requisitos"

    id = Column(Integer, primary_key=True, index=True)
    tramite_id = Column(Integer, ForeignKey("documento_tramites.id"))
    plantilla_id = Column(Integer, ForeignKey("requisitos_plantilla.id"))
    archivo_url = Column(String, nullable=True)
    fecha_vencimiento = Column(String, nullable=True)
    estado = Column(String, default="Faltante") # Faltante, Subido, Aprobado

    tramite = relationship("DocumentoTramite", back_populates="requisitos")
    plantilla = relationship("RequisitoPlantilla")
    documentos_adjuntos = relationship("DocumentoAdjunto", back_populates="requisito")

class DocumentoAdjunto(Base):
    __tablename__ = "documento_adjuntos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=True)
    vigilador_id = Column(Integer, ForeignKey("vigiladores.id"), nullable=True)
    tramite_id = Column(Integer, ForeignKey("documento_tramites.id"), nullable=True)
    requisito_id = Column(Integer, ForeignKey("documento_requisitos.id"), nullable=True)
    usuario_carga_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    tipo_documento = Column(String, nullable=False)
    nombre_original = Column(String, nullable=False)
    nombre_archivo = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    ruta_archivo = Column(String, nullable=False)
    hash_sha256 = Column(String, nullable=True)
    jurisdiccion_referencia = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    estado_extraccion = Column(String, default="Pendiente")
    texto_extraido = Column(String, nullable=True)
    fecha_carga = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    observaciones = Column(String, nullable=True)
    activo = Column(Boolean, default=True)

    empresa = relationship("Empresa", back_populates="documentos_adjuntos")
    vigilador = relationship("Vigilador", back_populates="documentos_adjuntos")
    tramite = relationship("DocumentoTramite", back_populates="documentos_adjuntos")
    requisito = relationship("DocumentoRequisito", back_populates="documentos_adjuntos")
    usuario_carga = relationship("Usuario", back_populates="documentos_cargados")


class BibliotecaDocumento(Base):
    __tablename__ = "biblioteca_documentos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False, index=True)
    categoria = Column(String, nullable=False, index=True)  # Normativa / Biblioteca documental
    jurisdiccion = Column(String, nullable=True)
    organismo = Column(String, nullable=True)
    tema = Column(String, nullable=True)
    fecha_documento = Column(String, nullable=True)
    vigencia = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=True)
    vigilador_id = Column(Integer, ForeignKey("vigiladores.id"), nullable=True)
    usuario_carga_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    nombre_original = Column(String, nullable=False)
    nombre_archivo = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    ruta_archivo = Column(String, nullable=False)
    hash_sha256 = Column(String, nullable=True)
    estado_extraccion = Column(String, default="Pendiente")
    texto_extraido = Column(String, nullable=True)
    resumen_referencia = Column(String, nullable=True)
    fecha_carga = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    observaciones = Column(String, nullable=True)
    activo = Column(Boolean, default=True)

    empresa = relationship("Empresa", back_populates="biblioteca_documentos")
    vigilador = relationship("Vigilador", back_populates="biblioteca_documentos")
    usuario_carga = relationship("Usuario", back_populates="biblioteca_documentos")
