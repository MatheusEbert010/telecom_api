import requests

# Endereco da API
base_url = "http://localhost:8000"

# Dados do usuario administrador
user_data = {
    "name": "Usuario Administrador",
    "email": "admin@telecom.com",
    "password": "Admin123!",
}

# Criar usuario
response = requests.post(f"{base_url}/users/", json=user_data)

print(f"Codigo de status: {response.status_code}")
try:
    print(f"Resposta: {response.json()}")
except Exception as exc:
    print(f"Texto da resposta: {response.text}")
    print(f"Erro ao decodificar JSON: {str(exc)}")
