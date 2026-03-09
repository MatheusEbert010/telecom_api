# Telecom API
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

---

## Arquitetura do Projeto

```
telecom_api
│
|── app
│   |── routers
│   │   |── users.py
|   |   |── plans.py
│   │
│   |── crud_completo.py
│   |── models.py
│   |── schemas.py
│   |── telecom_db.py
│   |── main.py
│
|── venv
|── requirements.txt
|── README.md
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
| routers/plans.py | Planos disponíveis              |

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

---

# Documentação da API

A documentação interativa é gerada automaticamente pelo **Swagger**.

Após rodar o projeto, acesse:

```

http://127.0.0.1:8000/docs

```

---

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

- Contratação de planos pelos usuários
- Paginação de usuários
- Filtro de usuários por email
- Autenticação com JWT
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

Matheus Ebert

LinkedIn:  
www.linkedin.com/in/matheus-ebert

GitHub:  
https://github.com/MatheusEbert010
```

---

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