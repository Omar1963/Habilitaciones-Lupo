"""
migrate_v7.py - Agrega columna 'privilege' a la tabla usuarios
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sql_app.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar si la columna ya existe
    cursor.execute("PRAGMA table_info(usuarios)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'privilege' not in columns:
        print("Agregando columna 'privilege' a tabla usuarios...")
        cursor.execute("ALTER TABLE usuarios ADD COLUMN privilege TEXT DEFAULT 'Ver'")
        # Actualizar admin existente para que tenga privilegio Admin
        cursor.execute("UPDATE usuarios SET privilege = 'Admin' WHERE role = 'Admin'")
        conn.commit()
        print("Migracion v7 completada.")
    else:
        print("La columna 'privilege' ya existe. No se requiere migracion.")

    conn.close()

if __name__ == "__main__":
    migrate()
