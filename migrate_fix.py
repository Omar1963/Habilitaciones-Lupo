from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import models
import sqlite3

import os

print("Migrating schema to add new columns...")

project_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_dir, "sql_app.db")
print(f"Modifying DB at {db_path}")

# For SQLite, we can use raw sqlite3 connection to avoiding SQLAlchemy 2.0 text/commit boilerplate for simple alters
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
add_column("empresas", "direccion", "VARCHAR")
add_column("empresas", "telefono", "VARCHAR")
add_column("empresas", "email", "VARCHAR")
add_column("empresas", "fecha_alta", "DATE")
add_column("empresas", "fecha_vencimiento_hab", "DATE")

# Vigiladores
add_column("vigiladores", "domicilio", "VARCHAR")
add_column("vigiladores", "telefono", "VARCHAR")
add_column("vigiladores", "legajo", "VARCHAR")
add_column("vigiladores", "fecha_alta", "DATE")
add_column("vigiladores", "fecha_vencimiento_hab", "DATE")

conn.commit()
conn.close()

print("Migration Complete.")
