from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

# 1. Update Schema
print("Migrating schema to add new columns...")
engine = create_engine("sqlite:///./sql_app.db", connect_args={"check_same_thread": False})
models.Base.metadata.create_all(bind=engine)

# Note: SQLite doesn't support ADD COLUMN well through SQLAlchemy create_all if the table already exists.
# Let's execute raw ALTER TABLE if the columns don't exist.
try:
    with engine.connect() as conn:
        conn.execute("ALTER TABLE empresas ADD COLUMN direccion VARCHAR")
        conn.execute("ALTER TABLE empresas ADD COLUMN telefono VARCHAR")
        conn.execute("ALTER TABLE empresas ADD COLUMN email VARCHAR")
        conn.execute("ALTER TABLE empresas ADD COLUMN fecha_alta DATE")
        conn.execute("ALTER TABLE empresas ADD COLUMN fecha_vencimiento_hab DATE")
        print("Empresa columns added.")
except Exception as e:
    print(f"Skipping Empresa columns (might already exist): {e}")
    
try:
    with engine.connect() as conn:
        conn.execute("ALTER TABLE vigiladores ADD COLUMN domicilio VARCHAR")
        conn.execute("ALTER TABLE vigiladores ADD COLUMN telefono VARCHAR")
        conn.execute("ALTER TABLE vigiladores ADD COLUMN legajo VARCHAR")
        conn.execute("ALTER TABLE vigiladores ADD COLUMN fecha_alta DATE")
        conn.execute("ALTER TABLE vigiladores ADD COLUMN fecha_vencimiento_hab DATE")
        print("Vigilador columns added.")
except Exception as e:
    print(f"Skipping Vigilador columns (might already exist): {e}")

# 2. Add new roles
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("Updating Roles list...")
roles_argentina = [
    "Vigilador General",
    "Vigilador Bombero",
    "Supervisor",
    "Jefe de Seguridad",
    "Tecnico Instalador",
    "Operador de Monitoreo",
    "Escolta Privado",
    "Director Tecnico"
]

for rol_nombre in roles_argentina:
    db_rol = db.query(models.Rol).filter(models.Rol.nombre == rol_nombre).first()
    if not db_rol:
        new_rol = models.Rol(nombre=rol_nombre)
        db.add(new_rol)
        print(f"Agregado Rol: {rol_nombre}")

db.commit()
db.close()
print("Migration Complete.")
