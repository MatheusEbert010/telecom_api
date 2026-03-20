import requests

# URL da API
base_url = "http://localhost:8000"

# Dados do usuário admin
user_data = {
    "name": "Admin User",
    "email": "admin@telecom.com",
    "password": "Admin123!"
}

# Criar usuário
response = requests.post(f"{base_url}/users/", json=user_data)

print(f"Status Code: {response.status_code}")
try:
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Response text: {response.text}")
    print(f"JSON decode error: {str(e)}")