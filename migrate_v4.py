import sqlite3
import os

print("Migrating schema to add missing columns (v4 - Updated)...")

project_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_dir, "sql_app.db")
print(f"Modifying DB at {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column(table, column, type_def):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
        print(f"Added column {column} to {table}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"Column {column} already exists in {table}")
        else:
            print(f"Error adding {column} to {table}: {e}")

# Empresa
add_column("empresas", "jurisdicciones", "VARCHAR")

# DocumentoTramite
add_column("documento_tramites", "empresa_id", "INTEGER")

# RequisitoPlantilla
add_column("requisitos_plantilla", "es_para_empresa", "BOOLEAN DEFAULT 0")

conn.commit()
conn.close()

print("Migration v4 Complete.")
