"""
seed_data.py - FIXED VERSION
================================
✔ Usa bcrypt de forma obligatoria
✔ Compatible con main.py / verify_password
✔ Elimina cualquier fallback inseguro (SHA256)
✔ Garantiza consistencia en login
"""

import sqlite3
import os
from passlib.context import CryptContext

# -----------------------------------------------------------------------------
# Configuración de hashing (DEBE coincidir con main.py)
# -----------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Genera hash bcrypt seguro para passwords de usuarios.
    """
    return pwd_context.hash(password)

# -----------------------------------------------------------------------------
# Conexión a la base de datos
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sql_app.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# -----------------------------------------------------------------------------
# Seed de usuario ADMIN
# -----------------------------------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin12345"
ADMIN_ROLE = "Admin"

print("🔐 Verificando usuario ADMIN...")

existing_admin = cursor.execute(
    "SELECT id FROM usuarios WHERE username = ?", 
    (ADMIN_USERNAME,)
).fetchone()

if existing_admin:
    print("♻️ Usuario admin existente → actualizando contraseña con bcrypt")
    cursor.execute(
        """
        UPDATE usuarios
        SET hashed_password = ?
        WHERE username = ?
        """,
        (get_password_hash(ADMIN_PASSWORD), ADMIN_USERNAME)
    )
else:
    print("➕ Creando usuario admin con bcrypt")
    cursor.execute(
        """
        INSERT INTO usuarios (username, hashed_password, role)
        VALUES (?, ?, ?)
        """,
        (
            ADMIN_USERNAME,
            get_password_hash(ADMIN_PASSWORD),
            ADMIN_ROLE
        )
    )

conn.commit()
conn.close()

print("✅ Seed de usuarios finalizado correctamente.")
