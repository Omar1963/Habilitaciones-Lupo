"""
migrate_v8.py - Crea la tabla documento_adjuntos para la trazabilidad documental
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sql_app.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documento_adjuntos (
            id INTEGER PRIMARY KEY,
            empresa_id INTEGER,
            vigilador_id INTEGER,
            tramite_id INTEGER,
            requisito_id INTEGER,
            usuario_carga_id INTEGER,
            tipo_documento VARCHAR NOT NULL,
            nombre_original VARCHAR NOT NULL,
            nombre_archivo VARCHAR NOT NULL,
            mime_type VARCHAR,
            ruta_archivo VARCHAR NOT NULL,
            fecha_carga VARCHAR DEFAULT CURRENT_TIMESTAMP,
            observaciones VARCHAR,
            activo BOOLEAN DEFAULT 1,
            FOREIGN KEY(empresa_id) REFERENCES empresas(id),
            FOREIGN KEY(vigilador_id) REFERENCES vigiladores(id),
            FOREIGN KEY(tramite_id) REFERENCES documento_tramites(id),
            FOREIGN KEY(requisito_id) REFERENCES documento_requisitos(id),
            FOREIGN KEY(usuario_carga_id) REFERENCES usuarios(id)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS ix_documento_adjuntos_id ON documento_adjuntos(id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_documento_adjuntos_empresa_id ON documento_adjuntos(empresa_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_documento_adjuntos_vigilador_id ON documento_adjuntos(vigilador_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_documento_adjuntos_tramite_id ON documento_adjuntos(tramite_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_documento_adjuntos_requisito_id ON documento_adjuntos(requisito_id)")

    conn.commit()
    conn.close()
    print("Migracion v8 completada: tabla documento_adjuntos lista.")


if __name__ == "__main__":
    migrate()
