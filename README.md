# Telecom API
🚀🗼🛜

API REST desenvolvida para simular o gerenciamento de usuários em um sistema de telecomunicações.

O projeto foi construído utilizando **FastAPI**, **SQLAlchemy** e **MySQL**, com arquitetura modular baseada em boas práticas de desenvolvimento backend.

---

## Tecnologias Utilizadas

* Python 3.10+
* FastAPI
* SQLAlchemy
* MySQL
* Uvicorn
* Pydantic

---

## Arquitetura do Projeto

```
telecom_api
│
|── app
│   |── routers
│   │   |── users.py
│   │
│   |── crud_completo.py
│   |── models.py
│   |── schemas.py
│   |── telecom_db.py
│   |── main.py
│
|── venv
|── requirements.txt
```

### Responsabilidade dos módulos

| Arquivo          | Responsabilidade                |
| ---------------- | ------------------------------- |
| main.py          | Inicialização da API            |
| telecom_db.py    | Conexão com o banco de dados    |
| models.py        | Definição das tabelas           |
| schemas.py       | Validação de dados com Pydantic |
| crud_completo.py | Operações de banco de dados     |
| routers/users.py | Rotas da API                    |

---

## Funcionalidades da API

CRUD completo de usuários:

* Criar usuário
* Listar usuários
* Buscar usuário por ID
* Atualizar usuário
* Deletar usuário

---

## Endpoints

| Método | Endpoint    | Descrição         |
| ------ | ----------- | ----------------- |
| POST   | /users      | Criar usuário     |
| GET    | /users      | Listar usuários   |
| GET    | /users/{id} | Buscar usuário    |
| PUT    | /users/{id} | Atualizar usuário |
| DELETE | /users/{id} | Remover usuário   |

---

## Exemplo de Requisição

### Criar usuário

```
POST /users
```

Body:

```json
{
 "name": "Matheus",
 "email": "matheus@email.com",
 "phone": "33999999999"
}
```

---

## Como executar o projeto

### 1 Clonar o repositório

```
git clone https://github.com/seuusuario/telecom_api.git
```

### 2 Entrar na pasta

```
cd telecom_api
```

### 3 Criar ambiente virtual

```
python -m venv venv
```

### 4 Ativar ambiente virtual

Windows:

```
venv\Scripts\activate
```

Linux / Mac:

```
source venv/bin/activate
```

### 5 Instalar dependências

```
pip install -r requirements.txt
```

### 6 Rodar API

```
uvicorn app.main:app --reload
```

---

## Documentação automática

Após iniciar o servidor, acesse:

Swagger UI

```
http://127.0.0.1:8000/docs
```

Redoc

```
http://127.0.0.1:8000/redoc
```

---

## Próximas melhorias

* Sistema de planos de internet
* Relacionamento entre usuários e planos
* Paginação de resultados
* Filtros de busca
* Dockerização da aplicação
* Autenticação JWT

---

## Autor

Matheus De Souza Ebert

Backend Engineer | Data Engineering

Python • SQL • APIs • ETL • Data Pipelines
