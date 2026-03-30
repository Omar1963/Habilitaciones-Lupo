import sqlite3, os
from datetime import datetime

project_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_dir, "sql_app.db")

conn = sqlite3.connect(db_path)
c = conn.cursor()

print("Ejecutando Migración v6...")

# 1. Crear tabla de Usuarios
try:
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        role TEXT NOT NULL, -- 'Admin', 'Cliente', 'Consultor'
        empresa_id INTEGER,
        FOREIGN KEY (empresa_id) REFERENCES empresas (id)
    )
    """)
    print("✅ Tabla 'usuarios' creada.")
except Exception as e:
    print(f"❌ Error al crear 'usuarios': {e}")

# 2. Añadir 'fecha_creacion' a 'documento_tramites'
try:
    # SQLite no soporta CURRENT_TIMESTAMP por defecto en ALTER TABLE de forma simple en versiones viejas, 
    # pero podemos hacerlo TEXT o DATETIME y luego poblarlo.
    c.execute("ALTER TABLE documento_tramites ADD COLUMN fecha_creacion DATETIME")
    # Poblar registros existentes con la fecha actual
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE documento_tramites SET fecha_creacion = ? WHERE fecha_creacion IS NULL", (now,))
    print("✅ Columna 'fecha_creacion' añadida y poblada.")
except Exception as e:
    print(f"❌ Error o ya existe 'fecha_creacion': {e}")

conn.commit()
conn.close()
print("✅ Migración v6 finalizada.")
