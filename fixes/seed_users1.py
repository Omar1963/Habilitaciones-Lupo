import models
from database import SessionLocal, engine
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    admin = db.query(models.Usuario).filter(models.Usuario.username == "admin").first()
    if admin:
        print("Actualizando usuario admin...")
        admin.hashed_password = get_password_hash("admin12345")
    else:
        print("Creando usuario admin...")
        db.add(models.Usuario(username="admin", hashed_password=get_password_hash("admin12345"), role="Admin"))
    
    # Jose (Consultor)
    jose = db.query(models.Usuario).filter(models.Usuario.username == "Jose").first()
    if not jose:
        print("Creando usuario Jose...")
        db.add(models.Usuario(username="Jose", hashed_password=get_password_hash("jose123"), role="Consultor"))
    
    db.commit()
    db.close()
    print("Seed finalizado.")

if __name__ == "__main__":
    seed()
