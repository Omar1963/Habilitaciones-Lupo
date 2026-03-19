import sqlite3, os

project_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_dir, "sql_app.db")

conn = sqlite3.connect(db_path)
c = conn.cursor()

print("Añadiendo columna 'activo' a 'documento_tramites'...")
try:
    c.execute("ALTER TABLE documento_tramites ADD COLUMN activo BOOLEAN DEFAULT 1")
    conn.commit()
    print("✅ Columna añadida correctamente.")
except Exception as e:
    print(f"❌ Error o ya existe: {e}")

conn.close()
