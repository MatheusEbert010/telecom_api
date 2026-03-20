# 🚀 Telecom API

API REST robusta para gerenciamento de usuários e planos de telecomunicações, construída com foco em **segurança, performance e escalabilidade**.

---

## 📌 Visão Geral

A Telecom API simula um sistema real de operadoras de telecom, permitindo:

- Gestão de usuários
- Gestão de planos de internet
- Associação de usuários a planos
- Autenticação segura com JWT
- Filtros, paginação e busca avançada

Projeto desenvolvido com foco em **boas práticas de backend moderno**.

---

## 🧠 Principais Features

- 🔐 Autenticação JWT (access + refresh token)
- 👥 RBAC (controle de acesso por roles)
- 🔍 Filtros, busca e ordenação
- 📄 Paginação com metadados
- ⚡ Cache com Redis
- 🚦 Rate limiting (proteção contra abuso)
- 🧾 Logs de auditoria com dados mascarados
- 🐳 Docker + Docker Compose
- 📊 Health check endpoint
- 📚 Documentação automática (Swagger)

---

## 🏗️ Stack Tecnológica

| Camada        | Tecnologia        |
|--------------|------------------|
| Backend      | FastAPI          |
| ORM          | SQLAlchemy       |
| Banco        | MySQL            |
| Cache        | Redis            |
| Auth         | JWT + Bcrypt     |
| Validação    | Pydantic         |
| Migrations   | Alembic          |
| Rate Limit   | SlowAPI          |

---

## 📂 Estrutura do Projeto
```bash
telecom_api/
├── app/
│ ├── main.py
│ ├── models.py
│ ├── schemas.py
│ ├── config.py
│ ├── security.py
│ ├── cache.py
│ ├── telecom_db.py
│ ├── routers/
│ ├── services/
│ ├── crud/
│ └── dependencies/
├── alembic/
├── logs/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🔐 Segurança

- Senhas criptografadas com **bcrypt**
- Tokens JWT com expiração
- Refresh tokens
- Rate limiting em endpoints sensíveis
- Headers de segurança (HSTS, CSP, XSS Protection)
- Validação rigorosa de entrada

---

## ⚡ Performance

- Cache Redis (TTL configurável)
- Queries otimizadas com índices
- Paginação eficiente
- Connection pooling
- Fallback automático se Redis indisponível

---

## 🚀 Como Rodar o Projeto

### 🔧 Pré-requisitos
- Python 3.11+
- MySQL 8+
- Redis (opcional)

---

### ▶️ Execução local

```bash
git clone https://github.com/MatheusEbert010/telecom-api.git
cd telecom-api

python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt

cp .env.example .env
# configure o .env

alembic upgrade head

uvicorn app.main:app --reload
```

### 🐳 Com Docker
```bash
docker-compose up -d
```

---

## 📡 Endpoints Principais
🔐 Auth
POST /auth/login
POST /auth/refresh
POST /auth/logout

---

## 👥 Usuários
GET    /users
POST   /users
GET    /users/{id}
PUT    /users/{id}
DELETE /users/{id}

---

## 📶 Planos
GET    /plans
POST   /plans
GET    /plans/{id}
PUT    /plans/{id}
DELETE /plans/{id}

---

## 🔗 Assinaturas
POST /users/{user_id}/subscribe

---

## Exemplos de uso
```Bash
curl -X POST http://localhost:8000/auth/login \
-H "Content-Type: application/json" \
-d '{"email":"admin@telecom.com","password":"Admin123!"}'
```

---

## Buscar Planos
```Bash
GET /plans?min_price=50&max_price=200&sort_by=price
```

---

## Health Check
```Bash 
GET /health
```

---

## 📚 Documentação
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🎯 Objetivo do Projeto

- Este projeto foi desenvolvido para:
- Consolidar conhecimentos em backend
- Aplicar arquitetura REST
- Trabalhar com autenticação e segurança
- Simular um sistema real de telecom
- Servir como projeto de portfólio

---

## 📈 Próximas Melhorias

 -  2FA (Two-Factor Authentication)
 -  WebSockets (notificações)
 -  Dashboard administrativo
 -  Testes automatizados completos

---

## 👨‍💻 Autor

- Matheus de Souza Ebert
- GitHub: https://github.com/MatheusEbert010
- LinkedIn: https://linkedin.com/in/matheusebert
- Email: dev.matheusebert@gmail.com