import models
from database import SessionLocal

db = SessionLocal()
try:
    empresa_id = 1
    # Test the problematic query
    print("Testing query for company_tramites...")
    res = db.query(models.DocumentoTramite).filter(models.DocumentoTramite.empresa_id == empresa_id).all()
    print(f"Success! Found {len(res)} tramites.")
except Exception as e:
    print(f"Error caught: {e}")
finally:
    db.close()
