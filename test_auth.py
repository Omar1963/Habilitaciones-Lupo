from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login(username, password):
    print(f"\n--- Probando login para {username} ---")
    response = client.post("/token", data={"username": username, "password": password})
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("OK: Login exitoso")
        
        # Test endpoint /users/me
        me_response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        print(f"Perfil: {me_response.json()}")
        
        # Test endpoint admin_required
        users_response = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
        if users_response.status_code == 200:
            print("OK: Acceso a /users/ permitido (Admin)")
        else:
            print(f"ERROR: Acceso a /users/ denegado: {users_response.status_code} - {users_response.json()}")
            
    else:
        print(f"ERROR: Login fallido: {response.status_code} - {response.json()}")

if __name__ == "__main__":
    test_login("admin", "admin12345")
    test_login("Jose", "jose123")
