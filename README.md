# Telecom API

[![CI](https://github.com/MatheusEbert010/telecom_api/actions/workflows/ci.yml/badge.svg)](https://github.com/MatheusEbert010/telecom_api/actions/workflows/ci.yml)
![Licenca](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![Testes](https://img.shields.io/badge/tests-35%20passing-2EA44F)

API REST para gerenciamento de usuarios, autenticacao e planos de telecomunicacoes.

O projeto foi construido com foco em fundamentos que pesam bastante em backend profissional: separacao por camadas, validacao forte de entrada, RBAC, migrations com Alembic, cache opcional com Redis, testes automatizados e CI no GitHub Actions.

## Sumario

- [Visao Geral](#visao-geral)
- [Principais Diferenciais](#principais-diferenciais)
- [Tecnologias](#tecnologias)
- [Arquitetura](#arquitetura)
- [Seguranca Aplicada](#seguranca-aplicada)
- [Rotas Principais](#rotas-principais)
- [Fluxo de Autenticacao](#fluxo-de-autenticacao)
- [Variaveis de Ambiente](#variaveis-de-ambiente)
- [Como Rodar Localmente](#como-rodar-localmente)
- [Rodando com Docker](#rodando-com-docker)
- [Primeiros Passos com Docker](#primeiros-passos-com-docker)
- [Qualidade e Testes](#qualidade-e-testes)
- [Exemplos de Uso](#exemplos-de-uso)
- [Postman](#postman)
- [CI](#ci)
- [Publicacoes](#publicacoes)
- [Pendencias](#pendencias)
- [Decisoes Tecnicas](#decisoes-tecnicas)
- [Proximos Passos](#proximos-passos)

## Visao Geral

Esta API permite:

- cadastrar usuarios com validacao de dados
- autenticar com `access token` e `refresh token`
- aplicar controle de acesso por perfil (`user` e `admin`)
- listar usuarios com busca, filtros, ordenacao e paginacao
- criar e consultar planos
- associar usuarios a planos
- expor um endpoint de saude para monitoramento

## Principais Diferenciais

- arquitetura em camadas: `routers`, `services`, `crud`, `schemas` e `models`
- protecao contra escalada de privilegio no fluxo publico de usuarios
- refresh token com persistencia em banco e armazenamento em hash
- respostas tipadas com `response_model`, evitando vazamento de campos sensiveis
- cache opcional com fallback seguro quando o Redis nao esta disponivel
- migrations validadas por teste automatizado em banco limpo
- pipeline de CI rodando lint e testes

## Tecnologias

- Python 3.11+
- FastAPI
- SQLAlchemy
- Alembic
- MySQL
- Redis
- JWT
- Pytest
- Ruff
- Docker e Docker Compose

## Arquitetura

```text
telecom_api/
|-- app/
|   |-- crud/           # acesso direto ao banco
|   |-- dependencies/   # dependencias de autenticacao e autorizacao
|   |-- routers/        # endpoints HTTP
|   |-- services/       # regras de negocio
|   |-- cache.py        # camada de cache com Redis
|   |-- config.py       # configuracoes do projeto
|   |-- logging_config.py
|   |-- main.py         # bootstrap da aplicacao
|   |-- models.py       # modelos ORM
|   |-- schemas.py      # validacao e contratos da API
|   |-- security.py     # hash de senha e tokens
|   |-- telecom_db.py   # conexao e sessao do banco
|   `-- time_utils.py   # helpers de data/hora em UTC
|-- alembic/            # migrations
|-- tests/              # testes unitarios, de integracao e migrations
|-- postman/            # recursos para testes manuais
|-- .github/workflows/  # CI
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
|-- requirements-dev.txt
`-- README.md
```

### Fluxo da Aplicacao

```mermaid
flowchart LR
    A[Cliente HTTP] --> B[Routers FastAPI]
    B --> C[Services]
    C --> D[CRUD / Repositories]
    D --> E[(MySQL)]
    C --> F[(Redis Cache)]
    B --> G[Dependencias de Autenticacao]
    G --> C
```

## Seguranca Aplicada

- `role` nao pode ser enviado no cadastro publico nem na atualizacao comum
- troca de papel acontece apenas por `PATCH /users/{user_id}/role`
- `GET /users/me` fica protegido contra conflito de rota com `/{user_id}`
- refresh tokens sao persistidos em hash
- logout e refresh invalidam e rotacionam tokens corretamente
- rotas sensiveis usam RBAC com dependencias especificas
- respostas de usuario nunca retornam hash de senha
- middleware adiciona cabecalhos de seguranca e endurece politicas em producao

## Rotas Principais

### Autenticacao

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`

### Usuarios

- `POST /users`
- `GET /users`
- `GET /users/me`
- `GET /users/me/plan`
- `GET /users/{user_id}`
- `PUT /users/{user_id}`
- `PATCH /users/{user_id}/role`
- `DELETE /users/{user_id}`
- `POST /users/{user_id}/subscribe`
- `DELETE /users/{user_id}/subscribe`

### Planos

- `POST /plans`
- `GET /plans`

### Administracao

- `GET /admin/stats`

### Observabilidade

- `GET /health`
- `GET /docs`
- `GET /redoc`

Observacao:
`/docs` e `/redoc` ficam desabilitados quando `ENVIRONMENT=production`.

## Fluxo de Autenticacao

1. O usuario faz login em `POST /auth/login`.
2. A API retorna `access_token` e `refresh_token`.
3. O `access_token` e usado nas rotas protegidas via header `Authorization: Bearer ...`.
4. Quando o `access_token` expira, o cliente chama `POST /auth/refresh`.
5. O refresh token antigo e invalidado e um novo par de tokens e emitido.
6. No logout, o refresh token e removido da base.

## Contrato de Erro

Os erros da API agora seguem um formato mais consistente para facilitar consumo no frontend:

```json
{
  "code": "requisicao_invalida",
  "detail": "Mensagem de erro"
}
```

Em erros de validacao, a resposta tambem inclui `errors` com a lista detalhada dos campos rejeitados.

## Variaveis de Ambiente

O projeto usa um arquivo `.env`. Existe um exemplo em [`.env.example`](/c:/Users/MATHEUS-PC/telecom_api/.env.example).

Variaveis principais:

- `SECRET_KEY`: chave usada para assinar JWTs
- `ALGORITHM`: algoritmo do JWT, por padrao `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES`: expiracao do access token
- `REFRESH_TOKEN_EXPIRE_DAYS`: expiracao do refresh token
- `DATABASE_URL`: string de conexao do banco
- `MYSQL_ROOT_PASSWORD`: senha do usuario `root` do MySQL em Docker
- `MYSQL_DATABASE`: banco criado automaticamente no container
- `MYSQL_USER`: usuario usado pela aplicacao no MySQL em Docker
- `MYSQL_PASSWORD`: senha do usuario da aplicacao no MySQL em Docker
- `MYSQL_PORT`: porta exposta do MySQL no host, limitada a `127.0.0.1`
- `REDIS_HOST`: host do Redis
- `REDIS_PORT`: porta do Redis
- `REDIS_DB`: indice logico do Redis
- `REDIS_PORT_HOST`: porta exposta do Redis no host, limitada a `127.0.0.1`
- `API_PORT`: porta exposta da API no host, limitada a `127.0.0.1`
- `CORS_ORIGINS`: lista CSV ou JSON de origens liberadas para browser
- `ENVIRONMENT`: `development`, `test` ou `production`
- `LOG_LEVEL`: nivel de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- `LOG_DIR`: pasta onde os logs serao gravados
- `LOG_FILE_NAME`: nome do arquivo principal de logs
- `LOG_TO_FILE`: habilita ou desabilita escrita em arquivo
- `BACKUP_INTERVAL_HOURS`: intervalo entre backups automaticos do MySQL em Docker
- `BACKUP_RETENTION_DAYS`: quantidade de dias mantida para os arquivos de backup
- `ADMIN_BOOTSTRAP_NOME`: nome usado pelo script de bootstrap do administrador em Docker
- `ADMIN_BOOTSTRAP_EMAIL`: email usado pelo script de bootstrap do administrador em Docker
- `ADMIN_BOOTSTRAP_SENHA`: senha usada pelo script de bootstrap do administrador em Docker
- `ADMIN_BOOTSTRAP_TELEFONE`: telefone usado pelo script de bootstrap do administrador em Docker

Exemplo:

```env
SECRET_KEY=replace_with_a_secret_key_that_has_at_least_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DATABASE_URL=mysql+pymysql://user:password@localhost/database_name
MYSQL_ROOT_PASSWORD=troque_esta_senha_root
MYSQL_DATABASE=telecom_api
MYSQL_USER=telecom_user
MYSQL_PASSWORD=troque_esta_senha_do_app
MYSQL_PORT=3306
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PORT_HOST=6379
API_PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_FILE_NAME=telecom_api.log
LOG_TO_FILE=true
BACKUP_INTERVAL_HOURS=24
BACKUP_RETENTION_DAYS=7
ADMIN_BOOTSTRAP_NOME=Administrador Docker
ADMIN_BOOTSTRAP_EMAIL=admin@telecom.com
ADMIN_BOOTSTRAP_SENHA=troque_esta_senha_do_admin
ADMIN_BOOTSTRAP_TELEFONE=11999990000
```

## Como Rodar Localmente

### 1. Criar e ativar ambiente virtual

```powershell
python -m venv venv
venv\Scripts\activate
```

### 2. Instalar dependencias

```powershell
pip install -r requirements-dev.txt
```

### 3. Criar o `.env`

```powershell
Copy-Item .env.example .env
```

Depois, ajuste a `DATABASE_URL` e a `SECRET_KEY`.

### 4. Aplicar migrations

```powershell
venv\Scripts\python.exe -m alembic upgrade head
```

### 5. Subir a aplicacao

```powershell
venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### 6. Criar ou promover um administrador local

```powershell
venv\Scripts\python.exe -m app.scripts.criar_admin `
  --nome "Administrador Local" `
  --email "admin@telecom.com" `
  --senha "Admin123!" `
  --telefone "11999990000"
```

API local:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

## Rodando com Docker

```powershell
docker-compose up -d --build
```

Observacoes:

- o container da API executa `alembic upgrade head` antes de subir o Uvicorn
- os logs ficam disponiveis em `./logs/telecom_api.log` quando `LOG_TO_FILE=true`
- a API, o MySQL e o Redis ficam publicados apenas em `127.0.0.1` no host local
- o MySQL fica exposto apenas em `127.0.0.1:${MYSQL_PORT}` para reduzir superficie local
- a configuracao do MySQL fica em [`docker/mysql/conf.d/my.cnf`](/c:/Users/MATHEUS-PC/telecom_api/docker/mysql/conf.d/my.cnf)
- os backups sao gerados em `./backups/mysql` pelo servico `db_backup`
- o Compose agora falha cedo quando `SECRET_KEY` ou credenciais do MySQL nao estiverem definidas no `.env`

Fluxo sugerido para usar MySQL em Docker local:

1. Copie [`.env.example`](/c:/Users/MATHEUS-PC/telecom_api/.env.example) para `.env`.
2. Ajuste `SECRET_KEY`, `MYSQL_ROOT_PASSWORD` e `MYSQL_PASSWORD`.
3. Ajuste `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PORT`, `REDIS_PORT_HOST` e `API_PORT` se precisar.
4. Defina `DATABASE_URL` apontando para `127.0.0.1:${MYSQL_PORT}` se for acessar o banco pelo host.
5. Execute `docker-compose up -d --build`.
6. Acompanhe os logs com `docker-compose logs -f api db db_backup`.
7. Crie ou promova um administrador com:

```powershell
docker compose exec api python -m app.scripts.criar_admin `
  --nome "Administrador Docker" `
  --email "admin@telecom.com" `
  --senha "Admin123!" `
  --telefone "11999990000"
```

## Primeiros Passos com Docker

Se quiser reduzir o setup manual, o projeto agora possui um bootstrap unico em PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_docker_local.ps1
```

O script faz o seguinte:

1. le as configuracoes do `.env`
2. executa `docker compose up -d --build`
3. aguarda a API responder em `/health`
4. cria ou promove o administrador configurado no `.env`

Variaveis opcionais para esse fluxo no [`.env.example`](/c:/Users/MATHEUS-PC/telecom_api/.env.example):

- `ADMIN_BOOTSTRAP_NOME`
- `ADMIN_BOOTSTRAP_EMAIL`
- `ADMIN_BOOTSTRAP_SENHA`
- `ADMIN_BOOTSTRAP_TELEFONE`

Exemplo de uso passando os dados do admin pela linha de comando:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_docker_local.ps1 `
  -EmailAdmin "admin@telecom.com" `
  -SenhaAdmin "Admin123!" `
  -NomeAdmin "Administrador Docker" `
  -TelefoneAdmin "11999990000"
```

Se quiser apenas subir os containers, sem criar administrador:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_docker_local.ps1 -SemAdmin
```

## Qualidade e Testes

Lint:

```powershell
venv\Scripts\python.exe -m ruff check app tests alembic
```

Testes:

```powershell
venv\Scripts\python.exe -m pytest
```

Compilacao rapida:

```powershell
venv\Scripts\python.exe -m compileall app tests alembic
```

Cobertura atual de qualidade:

- testes de seguranca
- testes de integracao HTTP
- teste de upgrade e downgrade das migrations
- CI com GitHub Actions em push para `main` e em `pull_request`

## Exemplos de Uso

### Login

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@example.com\",\"password\":\"Admin123!\"}"
```

Resposta esperada:

```json
{
  "access_token": "jwt_aqui",
  "refresh_token": "jwt_aqui",
  "token_type": "bearer"
}
```

### Buscar usuario autenticado

```bash
curl http://127.0.0.1:8000/users/me \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

### Buscar plano do usuario autenticado

```bash
curl http://127.0.0.1:8000/users/me/plan \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

### Criar plano como administrador

```bash
curl -X POST http://127.0.0.1:8000/plans \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Fibra 600\",\"price\":129.9,\"speed\":600}"
```

## Postman

O repositorio possui estrutura para testes manuais em [`postman/`](/c:/Users/MATHEUS-PC/telecom_api/postman) e agora inclui uma collection inicial em [telecom_api.collection.json](/c:/Users/MATHEUS-PC/telecom_api/postman/collections/telecom_api.collection.json).

Fluxo sugerido:

1. Importe a collection no Postman.
2. Defina a variavel `base_url` como `http://127.0.0.1:8000`.
3. Execute o request de login.
4. Copie os tokens retornados para as variaveis `access_token` e `refresh_token`.
5. Use os requests autenticados para explorar usuarios e planos.

## CI

O pipeline esta configurado em [ci.yml](/c:/Users/MATHEUS-PC/telecom_api/.github/workflows/ci.yml#L1) e executa:

- instalacao de dependencias
- lint com Ruff
- testes com Pytest

## Publicacoes

O projeto agora possui dois arquivos de apoio para versao e publicacao:

- [CHANGELOG.md](/c:/Users/MATHEUS-PC/telecom_api/CHANGELOG.md), com historico das mudancas relevantes
- [RELEASE.md](/c:/Users/MATHEUS-PC/telecom_api/RELEASE.md), com o passo a passo para criar commit, tag e release no GitHub

Tambem foi adicionada a configuracao [release.yml](/c:/Users/MATHEUS-PC/telecom_api/.github/release.yml#L1) para organizar release notes automáticas no GitHub por categoria.

## Pendencias

As pendencias priorizadas do projeto estao em [BACKLOG.md](/c:/Users/MATHEUS-PC/telecom_api/BACKLOG.md) com itens concluidos nesta rodada e proximos passos sugeridos.

## Decisoes Tecnicas

Algumas decisoes do projeto foram pensadas para equilibrar simplicidade com maturidade tecnica:

- `services` concentram regras de negocio e deixam os `routers` mais finos e previsiveis
- `schemas` com `extra="forbid"` evitam entrada silenciosa de campos indevidos
- refresh tokens sao persistidos em hash para reduzir risco de exposicao de credenciais
- cache e opcional e falha de forma segura quando o Redis nao esta disponivel
- datas usam helpers centralizados em UTC para evitar inconsistencias entre ambiente, banco e tokens
- migrations sao validadas por teste automatizado em banco limpo, nao apenas por execucao manual

## Aprendizados

Este projeto ajuda a demonstrar evolucao em pontos importantes de backend:

- como estruturar uma API FastAPI em camadas mais claras
- como aplicar RBAC e evitar escalada de privilegio
- como proteger respostas e contratos de API com schemas tipados
- como testar fluxo HTTP, seguranca e migrations no mesmo repositorio
- como transformar um projeto funcional em um repositorio mais profissional para GitHub

## Proximos Passos

Proximos passos recomendados para continuar amadurecendo o projeto:

- separar dominios em pacotes mais explicitos dentro de `app`
- ampliar testes negativos e cenarios de concorrencia
- adicionar observabilidade mais rica com logs estruturados
- criar testes de integracao com MySQL real via Docker
- evoluir a documentacao com diagramas de sequencia e exemplos reais de deploy

## Autor

- Matheus de Souza Ebert
- GitHub: <https://github.com/MatheusEbert010>
- LinkedIn: <https://linkedin.com/in/matheusebert>
