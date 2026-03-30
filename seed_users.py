# seed_users.py
"""
Seed de usuarios del sistema
Usa la MISMA lógica de seguridad que main.py
"""

from database import SessionLocal
from models import Usuario
from security import get_password_hash

def seed_users():
    db = SessionLocal()

    try:
        # ADMIN
        admin = db.query(Usuario).filter(Usuario.username == "admin").first()
        if admin:
            print("♻️ Actualizando usuario admin...")
            admin.hashed_password = get_password_hash("admin12345")
            admin.role = "Admin"
        else:
            print("➕ Creando usuario admin...")
            admin = Usuario(
                username="admin",
                hashed_password=get_password_hash("admin12345"),
                role="Admin"
            )
            db.add(admin)

        # USUARIO EJEMPLO
        jose = db.query(Usuario).filter(Usuario.username == "Jose").first()
        if not jose:
            print("➕ Creando usuario Jose...")
            jose = Usuario(
                username="Jose",
                hashed_password=get_password_hash("jose123"),
                role="Consultor"
            )
            db.add(jose)

        db.commit()
        print("✅ Seed de usuarios finalizado correctamente.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_users()