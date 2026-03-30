"""
migrate_v9.py - Crea la tabla biblioteca_documentos para la biblioteca documental y normativa
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sql_app.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS biblioteca_documentos (
            id INTEGER PRIMARY KEY,
            titulo VARCHAR NOT NULL,
            categoria VARCHAR NOT NULL,
            jurisdiccion VARCHAR,
            organismo VARCHAR,
            tema VARCHAR,
            fecha_documento VARCHAR,
            vigencia VARCHAR,
            tags VARCHAR,
            empresa_id INTEGER,
            vigilador_id INTEGER,
            usuario_carga_id INTEGER,
            nombre_original VARCHAR NOT NULL,
            nombre_archivo VARCHAR NOT NULL,
            mime_type VARCHAR,
            ruta_archivo VARCHAR NOT NULL,
            fecha_carga VARCHAR DEFAULT CURRENT_TIMESTAMP,
            observaciones VARCHAR,
            activo BOOLEAN DEFAULT 1,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id),
            FOREIGN KEY(vigilador_id) REFERENCES vigiladores(id),
            FOREIGN KEY(usuario_carga_id) REFERENCES usuarios(id)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS ix_biblioteca_documentos_id ON biblioteca_documentos(id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_biblioteca_documentos_titulo ON biblioteca_documentos(titulo)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_biblioteca_documentos_categoria ON biblioteca_documentos(categoria)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_biblioteca_documentos_empresa_id ON biblioteca_documentos(empresa_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_biblioteca_documentos_vigilador_id ON biblioteca_documentos(vigilador_id)")

    conn.commit()
    conn.close()
    print("Migracion v9 completada: tabla biblioteca_documentos lista.")


if __name__ == "__main__":
    migrate()
