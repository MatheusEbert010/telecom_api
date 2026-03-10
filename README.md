### Telecom API
🚀🗼🛜

API REST desenvolvida para simular o gerenciamento completo de um sistema para empresas de telecomunicações.

O projeto foi construído utilizando a linguagem **Python** **FastAPI**, **SQLAlchemy** e **MySQL**, com arquitetura modular baseada em boas práticas de desenvolvimento backend.
Esta API permite cadastrar usuários, gerenciar planos de internet e associar clientes aos planos disponíveis.

---

## Tecnologias Utilizadas

- Python
- FastAPI
- SQLAlchemy
- MySQL
- Uvicorn
- Pydantic
- Swagger (documentação automática)
- JWT (autenticação)
- Passlib / Bcrypt (criptografia de senha)

As bibliotecas envolvidas são **FastAPI, SQLAlchemy, Passlib, bcrypt** e **python-jose**.

---

## Arquitetura do Projeto

```
app
│── routers
│   |── users.py
|   |── plans.py
|   |── auth.py
│ 
|── services
│   |── user_service.py
|
|── crud
|   |── user_repository.py
|   |── plan_repository.py
|   |── crud_completo
|
│── security.py
|── models.py
|── schemas.py
|── telecom_db.py
│── main.py

```

### Responsabilidade dos módulos

| Arquivo            | Responsabilidade                            |
| ----------------   | ------------------------------------------  |
| main.py            | Inicialização da API                        |
| telecom_db.py      | Conexão com o banco de dados                |
| models.py          | Definição das tabelas                       |
| schemas.py         | Validação de dados com Pydantic             |
| crud/repository.py | Operações de banco de dados                 |
| services.py        | Regras de negócio da aplicação              |
| routers.py         | Definição dos endpoints da API              |
| security.py        | Criptografia de senha e geração de token JWT|
| auth.py            | Autenticação de usuários                    |

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

| Método | Endpoint              | Descrição                |
| ------ | --------------------- | -----------------        |
| POST   | /users                | Criar usuário            |
| POST   | /users/{id}/subscribe | Assinar plano            |
| GET    | /users                | Listar usuários          |
| GET    | /users/{id}           | Buscar usuário           |
| PUT    | /users/{id}           | Atualizar usuário        |
| DELETE | /users/{id}           | Remover usuário          |
| POST   | /auth/login           | Autenticação do usuário  |

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

# Sistema de Planos de Internet

Foi implementado um sistema de **Planos de Internet** permitindo que diferentes usuários possam estar associados a um plano.

Cada plano possui:

- id
- name
- price
- speed (Mbps)

---

# Relacionamento entre Usuário e Plano

Foi criado um relacionamento **1:N (um plano pode ter vários usuários)**.

Estrutura:

```
Plan 1 ----- N Users
```

Um usuário pode ter apenas um plano ativo.

---


# Endpoints de Planos

Criar plano:

```
POST /plans
```

Exemplo de payload:
```json
{
  "name": "Fibra 500MB",
  "price": 99,
  "speed": 500
}
```

Listar planos:

```
GET /plans
```

# Contratação de planos pelos usuários

Foi implementada a funcionalidade que permite que um usuário **contrate um plano de internet** diretamente pela API.
Essa feature adiciona uma regra de negócio real, onde o sistema **valida a existência do usuário e do plano** antes de realizar a associação entre eles.

---

# Endpoint

Contratar um plano

---

POST /users/{user_id}/subscribe

---

Body:

```json
{
  "plan_id": 1
}
```

---

# Fluxo da operação

- Verifica se o usuário existe no banco.
- Verifica se o plano existe.
- Associa o plano ao usuário.
- Salva a alteração no banco de dados.

---

---

# Paginação de usuários

- Esse padrão permite:
- Paginação real
- Frontend saber total de registros
- Criar navegação entre páginas
- Escalar para milhares de registros

---

GET /users?page=1&limit=10

---

```json
{
  "page": 1,
  "limit": 5,
  "total": 18,
  "data": [
    {
      "id": 1,
      "name": "Matheus",
      "email": "matheus@email.com",
      "phone": "33999999999"
    }
  ]
}
```

# Filtro de usuários por email

A API permite buscar usuários utilizando o email como parâmetro de consulta.

Exemplo: 

---

GET /users?email=matheus@email.com

---

Esse filtro também pode ser combinado com paginação:

---

GET /users?page=1&limit=10&email=matheus@email.com

---

# Login

Endpoint:

--- 

POST /auth/login

---

- Body

```json
{
 "email": "matheus@email.com",
 "password": "123456"
}
```

Resposta

```json

{
 "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
 "token_type": "bearer"
}

```

## Documentação da API

- A documentação interativa é gerada automaticamente pelo **Swagger**.

- Após rodar o projeto, acesse:

```

http://127.0.0.1:8000/docs

```

# Como Rodar o Projeto

## 1 Clonar o repositório

```bash
git clone https://github.com/MatheusEbert010/telecom_api.git
```

## 2 Entrar na pasta

```bash
cd telecom_api
```

## 3 Criar ambiente virtual

```bash
python -m venv venv
```

## 4 Ativar ambiente

Windows

```bash
venv\Scripts\activate
```

Linux / Mac

```bash
source venv/bin/activate
```

---

## 5 Instalar dependências

```bash
pip install -r requirements.txt
```

---

## 6 Rodar a API

```bash
uvicorn app.main:app --reload
```

---

# Próximas Implementações

O projeto continuará evoluindo com novas funcionalidades típicas de sistemas backend profissionais.

Roadmap:

- Proteção de rotas com JWT
- Middleware de autenticação
- Dockerização da API
- Deploy em ambiente cloud
- Testes automatizados

---

# Objetivo do Projeto

Este projeto foi desenvolvido com o objetivo de:

- praticar desenvolvimento backend com FastAPI
- aplicar conceitos de APIs REST
- trabalhar com ORM utilizando SQLAlchemy
- estruturar projetos backend de forma escalável
- construir um portfólio sólido para vagas de backend

---

# Autor

Matheus de Souza Ebert

LinkedIn:  
www.linkedin.com/in/matheus-ebert

GitHub:  
https://github.com/MatheusEbert010