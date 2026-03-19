"""
seed_data.py - Versión 4
Incluye Requisitos de EMPRESA vs PERSONAL y plazos de validez.
"""
import sqlite3, os

project_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_dir, "sql_app.db")

conn = sqlite3.connect(db_path)
c = conn.cursor()

# ── Tipos de Tramite ─────────────────────────────────────────────────
tipos_tramite = ["CABA", "PBA", "ANMAC", "PNA", "PSA-SICOP"]
for tipo in tipos_tramite:
    existing = c.execute("SELECT id FROM tipo_tramites WHERE nombre = ?", (tipo,)).fetchone()
    if not existing:
        c.execute("INSERT INTO tipo_tramites (nombre) VALUES (?)", (tipo,))

conn.commit()

# ── Cargar IDs ──────────────────────────────────────────────────────
roles_db = {r[1]: r[0] for r in c.execute("SELECT id, nombre FROM roles").fetchall()}
tipos_db = {t[1]: t[0] for t in c.execute("SELECT id, nombre FROM tipo_tramites").fetchall()}

# Helper para seedear plantillas mejorado
def seed_plantilla(tipo_name, requisitos, rol_name=None, es_empresa=False):
    tipo_id = tipos_db.get(tipo_name)
    rol_id = roles_db.get(rol_name) if rol_name else None
    
    if not tipo_id:
        print(f"  ! Error: No se encontro tipo {tipo_name}")
        return
        
    for req_desc, dias in requisitos:
        # Buscamos si existe la plantilla para evitar duplicados
        # Si es de empresa, rol_id es irrelevante o nulo
        if es_empresa:
            existing = c.execute(
                "SELECT id FROM requisitos_plantilla WHERE tipo_tramite_id=? AND descripcion=? AND es_para_empresa=1",
                (tipo_id, req_desc)
            ).fetchone()
        else:
            existing = c.execute(
                "SELECT id FROM requisitos_plantilla WHERE rol_id=? AND tipo_tramite_id=? AND descripcion=? AND es_para_empresa=0",
                (rol_id, tipo_id, req_desc)
            ).fetchone()
            
        if not existing:
            c.execute(
                "INSERT INTO requisitos_plantilla (rol_id, tipo_tramite_id, descripcion, dias_validez, es_para_empresa) VALUES (?,?,?,?,?)",
                (rol_id, tipo_id, req_desc, dias, 1 if es_empresa else 0)
            )
        else:
            c.execute(
                "UPDATE requisitos_plantilla SET dias_validez=? WHERE id=?",
                (dias, existing[0])
            )

# ── REQUISITOS DE VIGILADOR (PERSONAL) ─────────────────
vig_general_comun = [
    ("DNI (Frente y Dorso)", None),
    ("Certificado de Reincidencia (Nacional)", 60),
    ("Constancia de CUIL", None),
    ("Comprobante de Domicilio", 90),
]

caba_vig = vig_general_comun + [
    ("Apto Psicofisico CABA (Ley 5688)", 365),
    ("Datos Biométricos (Huellas/Firma/Foto)", 730),
    ("Certificado de Estudios Secundarios (Legalizado)", None),
    ("Antecedentes Penales CABA (60 días)", 60),
    ("Certificado de Capacitación CABA", 730),
]

pba_vig = vig_general_comun + [
    ("Apto Psicofisico PBA (Ley 12297)", 365),
    ("Título Secundario Obligatorio (PBA)", None),
    ("Certificado de Curso PBA (Centros Autorizados)", 730),
    ("Certificado Antecedentes PBA", 90),
]

anmac_vig = [
    ("Nota de Solicitud de Portación", None),
    ("Certificado de Antecedentes Penales (ANMAC)", 60),
    ("Certificado de Idoneidad de Tiro", 60),
    ("Examen Psicofísico (Sistema Abierto ANMAC)", 365),
    ("Seguro de Responsabilidad Civil (Portación)", 365),
]

psa_vig = [
    ("Apto Médico General (SICOP)", 365),
    ("Curso de Inducción S&Y (Planta)", 365),
    ("Recibo de Sueldo Firmado (Digitalizado)", 30),
    ("Seguro de Accidentes Personales (o ART)", 30),
    ("Certificación de Trabajo en Altura (si aplica)", 365),
]

pna_vig = [
    ("Apto Psicofisico PNA", 365),
    ("Curso Proteccion Buques e Instalaciones Portuarias", 730),
    ("Certificado Reincidencia (PNA)", 60),
]

# ── REQUISITOS DE EMPRESA (HABILITACION CORPORATIVA) ─────────────────
caba_emp = [
    ("Pago de Tasa PJ CABA ($1.5M aprox.)", 365),
    ("Biometría de Representantes (H/F/F)", 730),
    ("Estatuto Social Inscripto", None),
    ("Póliza de Responsabilidad Civil (PJ CABA)", 365),
    ("Inscripción Registro de Empresas", 365),
]

pba_emp = [
    ("Contrato Social / Estatuto", None),
    ("Inscripcion en Personas Juridicas", None),
    ("Habilitacion Municipal PBA", None),
    ("Libre Deuda Previsional", 180),
    ("Poliza de Responsabilidad Civil", 365),
    ("Certificado de Seguridad contra Incendio", 365),
]

anmac_emp = [
    ("Nota de Solicitud (Usuario Colectivo)", 365),
    ("Antecedentes Penales de Titulares", 60),
    ("Habilitación Jurisdiccional (PBA/CABA)", 365),
    ("Acreditación de Medidas de Seguridad (Guarda)", None),
    ("Pago de Aranceles Ley 23.979", None),
    ("Designación de Director Técnico / Jefe Seg.", 365),
]

psa_emp = [
    ("Certificado de ART con Nómina", 30),
    ("Cláusula de No Repetición (PSA/SICOP)", 30),
    ("Formulario AFIP 931", 30),
    ("Pago de Cargas Sociales (VEP)", 30),
    ("Póliza de Resp. Civil General", 365),
    ("Seguro de Vida Obligatorio", 365),
]

pna_emp = [
    ("Habilitacion Empresa Vigilancia (PNA)", 365),
    ("Inscripcion Registro Proveedores Portuarios", 365),
    ("Seguro Responsabilidad Civil (Portuario)", 365),
]

print("Seeding plantillas de PERSONAL...")
seed_plantilla("CABA", caba_vig, "Vigilador General")
seed_plantilla("PBA", pba_vig, "Vigilador General")
seed_plantilla("ANMAC", anmac_vig, "Vigilador con Arma de Fuego")
seed_plantilla("PSA-SICOP", psa_vig, rol_name=None)
seed_plantilla("PNA", pna_vig, "Vigilador Portuario")

print("Seeding plantillas de EMPRESA...")
seed_plantilla("CABA", caba_emp, es_empresa=True)
seed_plantilla("PBA", pba_emp, es_empresa=True)
seed_plantilla("ANMAC", anmac_emp, es_empresa=True)
seed_plantilla("PSA-SICOP", psa_emp, es_empresa=True)
seed_plantilla("PNA", pna_emp, es_empresa=True)

# ── DATOS FICTICIOS (15 PERSONAS, 4 EMPRESAS) ───────────────────────
print("Generando datos ficticios...")

empresas_ficticias = [
    ("SEGURIDAD PRO S.A.", "30-71111111-9", "Av. Corrientes 1234, CABA"),
    ("VIGILANCIA MODERNA S.R.L.", "30-72222222-8", "Calle Falsa 123, PBA"),
    ("GUARDIANES DEL SUR", "30-73333333-7", "Ruta 3 Km 50, PBA"),
    ("ALFA SECURITY SOLUTIONS", "33-74444444-6", "Florida 500, CABA")
]

for nom, cuit, dir in empresas_ficticias:
    if not c.execute("SELECT id FROM empresas WHERE cuit = ?", (cuit,)).fetchone():
        c.execute("INSERT INTO empresas (nombre, cuit, direccion, activo, jurisdicciones) VALUES (?,?,?,?,?)",
                  (nom, cuit, dir, 1, "CABA,PBA,PSA-SICOP"))

vigiladores_ficticios = [
    ("Juan Perez", "30123456"), ("Maria Garcia", "31234567"), ("Carlos Gonzalez", "32345678"),
    ("Ana Martinez", "33456789"), ("Luis Rodriguez", "34567890"), ("Jose Lopez", "35678901"),
    ("Marta Sanchez", "36789012"), ("Pedro Fernandez", "37890123"), ("Elena Ruiz", "38901234"),
    ("Diego Gomez", "39012345"), ("Sofia Bravo", "40123456"), ("Javier Castro", "41234567"),
    ("Lucía Diaz", "42345678"), ("Manuel Flores", "43456789"), ("Patricia Herrera", "44567890")
]

for nom, dni in vigiladores_ficticios:
    if not c.execute("SELECT id FROM vigiladores WHERE dni = ?", (dni,)).fetchone():
        c.execute("INSERT INTO vigiladores (nombre_completo, dni, activo) VALUES (?,?,?)", (nom, dni, 1))

conn.commit()

# Crear algunas asignaciones aleatorias
print("Creando asignaciones y roles...")
emp_ids = [r[0] for r in c.execute("SELECT id FROM empresas").fetchall()]
vig_ids = [r[0] for r in c.execute("SELECT id FROM vigiladores").fetchall()]
rol_vig_id = roles_db.get("Vigilador General")

for i, v_id in enumerate(vig_ids):
    e_id = emp_ids[i % len(emp_ids)]
    # Asignacion
    existing_asig = c.execute("SELECT id FROM asignaciones WHERE vigilador_id=? AND empresa_id=?", (v_id, e_id)).fetchone()
    if not existing_asig:
        c.execute("INSERT INTO asignaciones (vigilador_id, empresa_id, activa) VALUES (?,?,?)", (v_id, e_id, 1))
        asig_id = c.lastrowid
        # Rol
        if rol_vig_id:
            c.execute("INSERT INTO asignacion_roles (asignacion_id, rol_id, activo) VALUES (?,?,?)", (asig_id, rol_vig_id, 1))

conn.commit()
conn.close()
print("✅ Base de datos actualizada con datos ficticios.")
