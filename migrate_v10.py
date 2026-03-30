"""
migrate_v10.py - Agrega metadata de preparacion IA a documento_adjuntos y biblioteca_documentos
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sql_app.db")


def add_column_if_missing(cursor, table_name: str, column_name: str, column_sql: str):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    add_column_if_missing(cursor, "documento_adjuntos", "hash_sha256", "VARCHAR")
    add_column_if_missing(cursor, "documento_adjuntos", "jurisdiccion_referencia", "VARCHAR")
    add_column_if_missing(cursor, "documento_adjuntos", "tags", "VARCHAR")
    add_column_if_missing(cursor, "documento_adjuntos", "estado_extraccion", "VARCHAR DEFAULT 'Pendiente'")
    add_column_if_missing(cursor, "documento_adjuntos", "texto_extraido", "VARCHAR")

    add_column_if_missing(cursor, "biblioteca_documentos", "hash_sha256", "VARCHAR")
    add_column_if_missing(cursor, "biblioteca_documentos", "estado_extraccion", "VARCHAR DEFAULT 'Pendiente'")
    add_column_if_missing(cursor, "biblioteca_documentos", "texto_extraido", "VARCHAR")
    add_column_if_missing(cursor, "biblioteca_documentos", "resumen_referencia", "VARCHAR")

    conn.commit()
    conn.close()
    print("Migracion v10 completada: metadata IA agregada.")


if __name__ == "__main__":
    migrate()
