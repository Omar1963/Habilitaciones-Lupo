from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship
from database import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    cuit = Column(String, unique=True, index=True)
    direccion = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    fecha_alta = Column(Date, nullable=True)
    fecha_vencimiento_hab = Column(Date, nullable=True)
    activo = Column(Boolean, default=True)  # False = archivado (soft-delete)
    jurisdicciones = Column(String, nullable=True) # Comma separated list like "CABA,PBA,PSA"

    asignaciones = relationship("Asignacion", back_populates="empresa")
    tramites_propios = relationship("DocumentoTramite", back_populates="empresa")

class Vigilador(Base):
    __tablename__ = "vigiladores"

    id = Column(Integer, primary_key=True, index=True)
    dni = Column(String, unique=True, index=True)
    nombre_completo = Column(String)
    domicilio = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    legajo = Column(String, nullable=True)
    fecha_alta = Column(Date, nullable=True)
    fecha_vencimiento_hab = Column(Date, nullable=True)
    activo = Column(Boolean, default=True)  # False = archivado (soft-delete)
    
    asignaciones = relationship("Asignacion", back_populates="vigilador")

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

    asignacion_rol = relationship("AsignacionRol", back_populates="tramites")
    empresa = relationship("Empresa", back_populates="tramites_propios")
    tipo_tramite = relationship("TipoTramite")
    requisitos = relationship("DocumentoRequisito", back_populates="tramite")

class DocumentoRequisito(Base):
    __tablename__ = "documento_requisitos"

    id = Column(Integer, primary_key=True, index=True)
    tramite_id = Column(Integer, ForeignKey("documento_tramites.id"))
    plantilla_id = Column(Integer, ForeignKey("requisitos_plantilla.id"))
    archivo_url = Column(String, nullable=True)
    fecha_vencimiento = Column(Date, nullable=True)
    estado = Column(String, default="Faltante") # Faltante, Subido, Aprobado

    tramite = relationship("DocumentoTramite", back_populates="requisitos")
    plantilla = relationship("RequisitoPlantilla")
