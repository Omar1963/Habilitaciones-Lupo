from database import SessionLocal
import models

def check_users():
    db = SessionLocal()
    users = db.query(models.Usuario).all()
    print(f"Total usuarios: {len(users)}")
    for u in users:
        print(f"User: {u.username}, Role: {u.role}, Hash: {u.hashed_password[:10]}...")
    db.close()

if __name__ == "__main__":
    check_users()
