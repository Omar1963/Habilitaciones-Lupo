import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_flow():
    print("=== Iniciando Prueba de Flujo Completo ===\n")
    
    # 1. Crear Empresa
    empresa = requests.post(f"{BASE_URL}/empresas/", json={"nombre": "Seguridad Beta C.A.", "cuit": "30-87654321-1"}).json()
    print(f"Empresa creada: {empresa}")
    
    # 2. Crear Vigilador
    vigilador = requests.post(f"{BASE_URL}/vigiladores/", json={"dni": "87654321", "nombre_completo": "Ana Gomez"}).json()
    print(f"Vigilador creado: {vigilador}")
    
    # 3. Crear Asignacion
    asignacion = requests.post(f"{BASE_URL}/asignaciones/", json={
        "empresa_id": empresa["id"], 
        "vigilador_id": vigilador["id"],
        "activa": True
    }).json()
    print(f"Asignacion creada: {asignacion}")
    
    # 4. Crear Roles (Catálogo)
    rol_op = requests.post(f"{BASE_URL}/roles/", json={"nombre": "Operador"}).json()
    rol_tec = requests.post(f"{BASE_URL}/roles/", json={"nombre": "Tecnico"}).json()
    
    # 5. Asignar Rol a la Asignacion
    asignacion_rol = requests.post(f"{BASE_URL}/asignaciones/{asignacion['id']}/roles/", json={
        "asignacion_id": asignacion["id"],
        "rol_id": rol_op["id"],
        "activo": True
    }).json()
    print(f"Rol asignado: {asignacion_rol}")
    
    # 6. Crear Tipos de Tramite (Catálogo)
    tramite_pba = requests.post(f"{BASE_URL}/tipos-tramites/", json={"nombre": "PBA"}).json()
    
    # 7. Crear Plantilla (Catálogo de Requisitos)
    # Ejemplo: Para Operador en PBA, se pide DNI y Certificado de Reincidencia
    plantilla1 = requests.post(f"{BASE_URL}/plantillas/", json={
        "rol_id": rol_op["id"],
        "tipo_tramite_id": tramite_pba["id"],
        "descripcion": "Copia de DNI"
    }).json()
    plantilla2 = requests.post(f"{BASE_URL}/plantillas/", json={
        "rol_id": rol_op["id"],
        "tipo_tramite_id": tramite_pba["id"],
        "descripcion": "Certificado de Reincidencia"
    }).json()
    print("Plantillas de requisitos configuradas.")
    
    # 8. Finalmente, CREAR TRAMITE (El corazón del flujo)
    print("\nGenerando Trámite PBA para Ana Gómez (Operador)...")
    tramite = requests.post(f"{BASE_URL}/tramites/", json={
        "asignacion_rol_id": asignacion_rol["id"],
        "tipo_tramite_id": tramite_pba["id"]
    }).json()
    
    print("\n--- RESULTADO DEL TRAMITE Y SU CHECKLIST ---")
    print(f"Trámite ID: {tramite['id']}, Estado: {tramite['estado']}")
    for req in tramite['requisitos']:
        descripcion = "Copia de DNI" if req['plantilla_id'] == plantilla1['id'] else "Certificado de Reincidencia"
        print(f" - Requisito ID {req['id']}: {descripcion} | Estado: {req['estado']}")
        
    print("\n=== Prueba Finalizada ===")

if __name__ == "__main__":
    test_flow()
