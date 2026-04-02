# Telecom API

[![CI](https://github.com/MatheusEbert010/telecom_api/actions/workflows/ci.yml/badge.svg)](https://github.com/MatheusEbert010/telecom_api/actions/workflows/ci.yml)
![Licenca](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![Testes](https://img.shields.io/badge/tests-46%20passing-2EA44F)

API REST para gerenciamento de usuarios, autenticacao e planos de telecomunicacoes.

O projeto foi construido com foco em fundamentos que pesam bastante em backend profissional: separacao por camadas, validacao forte de entrada, RBAC, migrations com Alembic, cache opcional com Redis, testes automatizados e CI no GitHub Actions.

O caminho preferencial da API agora e `/api/v1`, mantendo as rotas legadas sem prefixo por compatibilidade durante a transicao.

## Sumario

- [Visao Geral](#visao-geral)
- [Principais Diferenciais](#principais-diferenciais)
- [Tecnologias](#tecnologias)
- [Arquitetura](#arquitetura)
- [Seguranca Aplicada](#seguranca-aplicada)
- [Rotas Principais](#rotas-principais)
- [Fluxo de Autenticacao](#fluxo-de-autenticacao)
- [Versionamento da API](#versionamento-da-api)
- [Variaveis de Ambiente](#variaveis-de-ambiente)
- [Como Rodar Localmente](#como-rodar-localmente)
- [Rodando com Docker](#rodando-com-docker)
- [Deploy no Render](#deploy-no-render)
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
- associar e cancelar planos de usuarios
- expor um endpoint de saude para monitoramento

## Principais Diferenciais

- arquitetura em camadas: `routers`, `services`, `crud`, `schemas` e `models`
- protecao contra escalada de privilegio no fluxo publico de usuarios
- refresh token com persistencia em banco e armazenamento em hash
- respostas tipadas com `response_model`, evitando vazamento de campos sensiveis
- cache opcional com fallback seguro quando o Redis nao esta disponivel
- migrations validadas por teste automatizado em banco limpo
- pipeline de CI com lint, testes, auditoria de dependencias, build Docker e integracao com MySQL

## Tecnologias

- Python 3.12+
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

Organizacao principal da aplicacao:

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
flowchart TD
    cliente["Cliente HTTP"] --> rotas["Routers FastAPI"]
    rotas --> auth["Dependencias de autenticacao"]
    rotas --> servicos["Services"]
    auth --> servicos
    servicos --> repositorios["CRUD e repositories"]
    repositorios --> mysql["MySQL"]
    servicos --> redis["Redis cache"]
```

Leitura rapida da arquitetura:

- `routers` recebem a requisicao HTTP e aplicam validacao de entrada
- `dependencies` resolvem autenticacao e autorizacao antes da regra de negocio
- `services` concentram as regras de negocio e a orquestracao
- `crud` e `repositories` encapsulam o acesso ao banco
- `cache.py` reduz leituras repetidas quando o Redis esta disponivel

Se o Mermaid nao renderizar no seu preview, o fluxo acima pode ser lido como:
`Cliente HTTP -> Routers FastAPI -> Services -> CRUD e repositories -> MySQL`, com autenticacao entrando antes das regras protegidas e Redis como apoio de cache.

## Seguranca Aplicada

- `role` nao pode ser enviado no cadastro publico nem na atualizacao comum
- troca de papel acontece apenas por `PATCH /users/{user_id}/role`
- `GET /users/me` fica protegido contra conflito de rota com `/{user_id}`
- refresh tokens sao persistidos em hash
- JWTs carregam `iss`, `aud` e `token_type` para reduzir uso indevido entre fluxos
- cada resposta devolve `X-Request-ID` para correlacao entre cliente, API e logs
- logout e refresh invalidam e rotacionam tokens corretamente
- rotas sensiveis usam RBAC com dependencias especificas
- respostas de usuario nunca retornam hash de senha
- middleware adiciona cabecalhos de seguranca e endurece politicas em producao

## Rotas Principais

### Autenticacao

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

### Usuarios

- `POST /api/v1/users`
- `GET /api/v1/users`
- `GET /api/v1/users/me`
- `GET /api/v1/users/me/plan`
- `GET /api/v1/users/{user_id}`
- `PUT /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}/role`
- `DELETE /api/v1/users/{user_id}`
- `POST /api/v1/users/{user_id}/subscribe`
- `DELETE /api/v1/users/{user_id}/subscribe`

### Planos

- `POST /api/v1/plans`
- `GET /api/v1/plans`

### Administracao

- `GET /api/v1/admin/stats`

### Observabilidade

- `GET /api/v1/health`
- `GET /api/v1/health/ready`
- `GET /docs`
- `GET /redoc`

Observacao:
`/docs` e `/redoc` ficam desabilitados quando `ENVIRONMENT=production`.
As rotas sem prefixo continuam funcionando por compatibilidade, mas as rotas em `/api/v1` sao a interface recomendada daqui para frente.

## Fluxo de Autenticacao

1. O usuario faz login em `POST /api/v1/auth/login`.
2. A API retorna `access_token` e `refresh_token`.
3. O `access_token` e usado nas rotas protegidas via header `Authorization: Bearer ...`.
4. Quando o `access_token` expira, o cliente chama `POST /api/v1/auth/refresh`.
5. O refresh token antigo e invalidado e um novo par de tokens e emitido.
6. No logout, o cliente chama `POST /api/v1/auth/logout` e o refresh token e removido da base.

## Versionamento da API

O projeto passou a expor um prefixo estavel em `/api/v1`.

- use `/api/v1` para novas integracoes
- mantenha as rotas antigas apenas como transicao
- no Swagger, as rotas legadas aparecem como obsoletas para sinalizar a migracao gradual

## Contrato de Erro

Os erros da API agora seguem um formato mais consistente para facilitar consumo por clientes HTTP:

```json
{
  "code": "requisicao_invalida",
  "detail": "Mensagem de erro"
}
```

Em erros de validacao, a resposta tambem inclui `errors` com a lista detalhada dos campos rejeitados.

As respostas de erro tambem incluem `request_id`, e o mesmo valor e devolvido no header `X-Request-ID`.

## Health e Readiness

- `GET /api/v1/health` e publico e responde de forma enxuta para monitoramento externo
- em `production`, a versao da aplicacao deixa de aparecer nesse endpoint por padrao
- `GET /api/v1/health/ready` valida banco e cache para decidir se a API esta pronta para receber trafego
- no proxy de producao, o endpoint de readiness fica restrito ao proprio host para reduzir exposicao operacional
- o cabecalho `X-Request-ID` e saneado antes de ser reaproveitado, evitando aceitar valores malformados

## Variaveis de Ambiente

O projeto usa um arquivo `.env`. Existe um exemplo em [`.env.example`](/c:/Users/MATHEUS-PC/telecom_api/.env.example).

Variaveis principais:

- `SECRET_KEY`: chave usada para assinar JWTs
- `SECRET_KEY_FILE`: caminho opcional para ler a chave secreta de um arquivo
- `ALGORITHM`: algoritmo do JWT, por padrao `HS256`
- `JWT_ISSUER`: emissor esperado nos JWTs da aplicacao
- `JWT_AUDIENCE`: audiencia esperada nos JWTs emitidos pela API
- `ACCESS_TOKEN_EXPIRE_MINUTES`: expiracao do access token
- `REFRESH_TOKEN_EXPIRE_DAYS`: expiracao do refresh token
- `DATABASE_URL`: string de conexao do banco
- `DATABASE_URL_FILE`: caminho opcional para ler a URL do banco de um arquivo
- `DATABASE_HOST`: host do banco quando a aplicacao monta a URL a partir de partes
- `DATABASE_PORT`: porta do banco quando a aplicacao monta a URL a partir de partes
- `DATABASE_NAME`: nome do banco quando a aplicacao monta a URL a partir de partes
- `DATABASE_USER`: usuario do banco quando a aplicacao monta a URL a partir de partes
- `DATABASE_PASSWORD`: senha do banco quando a aplicacao monta a URL a partir de partes
- `DATABASE_PASSWORD_FILE`: caminho opcional para ler a senha do banco de um arquivo e montar a URL com escape seguro
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
- `PROXY_HTTP_PORT`: porta HTTP publicada pelo proxy reverso no compose de producao
- `PROXY_HTTPS_PORT`: porta HTTPS publicada pelo proxy reverso no compose de producao
- `CORS_ORIGINS`: lista CSV ou JSON de origens liberadas para browser
- `ENVIRONMENT`: `development`, `test` ou `production`
- `HEALTH_EXPOSE_VERSION`: sobrescreve a politica de exibir versao no health publico
- `TRUST_CLIENT_REQUEST_ID`: define se a API reaproveita `X-Request-ID` vindo do cliente
- `UVICORN_PROXY_HEADERS`: habilita leitura de `X-Forwarded-*` quando a API esta atras de proxy
- `UVICORN_FORWARDED_ALLOW_IPS`: lista de IPs ou redes confiaveis para cabecalhos de proxy no Uvicorn
- `LOG_LEVEL`: nivel de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- `LOG_DIR`: pasta onde os logs serao gravados
- `LOG_FILE_NAME`: nome do arquivo principal de logs
- `LOG_TO_FILE`: habilita ou desabilita escrita em arquivo
- `BACKUP_INTERVAL_HOURS`: intervalo entre backups automaticos do MySQL em Docker
- `BACKUP_RETENTION_DAYS`: quantidade de dias mantida para os arquivos de backup
- `ADMIN_BOOTSTRAP_NOME`: nome usado pelo script de bootstrap do administrador em Docker
- `ADMIN_BOOTSTRAP_EMAIL`: email usado pelo script de bootstrap do administrador em Docker
- `ADMIN_BOOTSTRAP_SENHA`: senha opcional usada pelo script de bootstrap do administrador em Docker; se vazia, o script solicita sem ecoar no terminal
- `ADMIN_BOOTSTRAP_TELEFONE`: telefone usado pelo script de bootstrap do administrador em Docker

Exemplo:

```env
SECRET_KEY=replace_with_a_secret_key_that_has_at_least_32_chars
SECRET_KEY_FILE=
ALGORITHM=HS256
JWT_ISSUER=telecom-api
JWT_AUDIENCE=telecom-api-clients
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DATABASE_URL=mysql+pymysql://user:password@localhost/database_name
DATABASE_URL_FILE=
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
PROXY_HTTP_PORT=8080
PROXY_HTTPS_PORT=8443
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
HEALTH_EXPOSE_VERSION=
TRUST_CLIENT_REQUEST_ID=
UVICORN_PROXY_HEADERS=
UVICORN_FORWARDED_ALLOW_IPS=127.0.0.1,172.16.0.0/12
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_FILE_NAME=telecom_api.log
LOG_TO_FILE=true
BACKUP_INTERVAL_HOURS=24
BACKUP_RETENTION_DAYS=7
ADMIN_BOOTSTRAP_NOME=Administrador Docker
ADMIN_BOOTSTRAP_EMAIL=admin@telecom.com
ADMIN_BOOTSTRAP_SENHA=
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
  --telefone "11999990000"
```

O script pede a senha de forma interativa e confirma duas vezes, evitando expo-la na linha de comando.

API local:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/api/v1/health`

## Rodando com Docker

```powershell
docker-compose up -d --build
```

Observacoes:

- o container da API executa `alembic upgrade head` antes de subir o Uvicorn
- os logs ficam disponiveis em `./logs/telecom_api.log` quando `LOG_TO_FILE=true`
- cada requisicao recebe um `X-Request-ID`, reaproveitado quando o cliente envia esse cabecalho
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
  --telefone "11999990000"
```

Se precisar automatizar sem prompt, envie a senha via `stdin`:

```powershell
"Admin123!" | docker compose exec -T api python -m app.scripts.criar_admin `
  --nome "Administrador Docker" `
  --email "admin@telecom.com" `
  --senha-stdin `
  --telefone "11999990000"
```

## Docker para Producao

Existe um compose separado em [docker-compose.production.yml](/c:/Users/MATHEUS-PC/telecom_api/docker-compose.production.yml) para um caminho mais seguro de producao.

Esse arquivo:

- usa `SECRET_KEY_FILE` e `DATABASE_URL_FILE` na API
- monta a `DATABASE_URL` automaticamente a partir de `DATABASE_HOST`, `DATABASE_NAME`, `DATABASE_USER` e `DATABASE_PASSWORD_FILE`
- usa `MYSQL_PASSWORD_FILE` e `MYSQL_ROOT_PASSWORD_FILE` no MySQL
- adiciona um Nginx como proxy reverso na frente da API
- publica apenas as portas HTTP e HTTPS do proxy no host
- deixa a API acessivel apenas pela rede interna do Compose
- nao publica MySQL nem Redis no host
- desabilita a exposicao da versao no health publico por padrao
- nao confia em `X-Request-ID` vindo do cliente por padrao
- redireciona HTTP para HTTPS e espera certificado/chave em arquivos secretos

Arquivos de exemplo para os segredos:

- [secret_key.txt.example](/c:/Users/MATHEUS-PC/telecom_api/docker/secrets/secret_key.txt.example)
- [mysql_password.txt.example](/c:/Users/MATHEUS-PC/telecom_api/docker/secrets/mysql_password.txt.example)
- [mysql_root_password.txt.example](/c:/Users/MATHEUS-PC/telecom_api/docker/secrets/mysql_root_password.txt.example)
- [tls.crt.example](/c:/Users/MATHEUS-PC/telecom_api/docker/secrets/tls.crt.example)
- [tls.key.example](/c:/Users/MATHEUS-PC/telecom_api/docker/secrets/tls.key.example)

Fluxo sugerido:

1. copie os arquivos `.example` em `docker/secrets/` para arquivos `.txt`
2. copie tambem `tls.crt.example` e `tls.key.example` para `tls.crt` e `tls.key`, substituindo pelo certificado e chave reais em formato PEM
3. preencha os valores reais
4. ajuste `PROXY_HTTP_PORT` e `PROXY_HTTPS_PORT` se quiser publicar o proxy em portas diferentes de `8080` e `8443`
5. mantenha `UVICORN_PROXY_HEADERS=1` e use `UVICORN_FORWARDED_ALLOW_IPS=127.0.0.1,172.16.0.0/12` como baseline para proxy local e redes Docker, ajustando para a sua topologia real quando necessario
6. execute `docker compose -f docker-compose.production.yml up -d --build`
7. valide `GET /api/v1/health` e `GET /api/v1/health/ready`
8. acesse a API pela porta HTTPS do proxy, por exemplo `https://127.0.0.1:8443/api/v1/health`

Observacao:
o compose de producao monta a `DATABASE_URL` automaticamente a partir das partes do banco e da senha lida em `MYSQL_PASSWORD_FILE`, evitando erro com caracteres especiais na senha.
Os arquivos de segredo devem conter somente o valor puro, sem espacos ou quebras de linha extras no final.

Arquivos do proxy reverso:

- [nginx.conf](/c:/Users/MATHEUS-PC/telecom_api/docker/nginx/nginx.conf)
- [telecom_api.conf](/c:/Users/MATHEUS-PC/telecom_api/docker/nginx/conf.d/telecom_api.conf)

## Deploy no Render

O projeto agora inclui um blueprint em [render.yaml](/c:/Users/MATHEUS-PC/telecom_api/render.yaml) para subir a stack principal no Render com:

- uma `Web Service` publica para a API
- deploy em `plan: free` para reduzir o custo inicial
- cache desabilitado por padrao no Render gratuito, usando o fallback seguro da aplicacao
- conexao com MySQL externo via `DATABASE_URL`
- `autoDeployTrigger: checksPass`, para deploy automatico somente depois que o CI do GitHub Actions passar

### Como o fluxo CI/CD fica nesse caso

1. voce faz push para `main`
2. o GitHub Actions roda os jobs de CI definidos em [ci.yml](/c:/Users/MATHEUS-PC/telecom_api/.github/workflows/ci.yml)
3. quando os checks passam, o Render inicia o deploy automaticamente
4. a API publica atualiza no dominio `onrender.com` ou no dominio customizado que voce configurar

Em outras palavras: sim, isso ja e CD trabalhando em cima do seu CI atual.

### Como subir

1. envie o repositorio atualizado para o GitHub
2. entre no Render e conecte sua conta GitHub
3. escolha `New +` -> `Blueprint`
4. selecione este repositorio
5. revise os servicos propostos no `render.yaml`
6. informe os valores secretos pedidos para `DATABASE_URL` e `CORS_ORIGINS`
7. finalize a criacao

### Observacoes importantes para este projeto

- o container da API agora respeita `PORT`, o que encaixa melhor no ambiente do Render
- a API continua executando `alembic upgrade head` ao iniciar, o que ajuda no bootstrap inicial
- para clientes web publicos, defina `CORS_ORIGINS` com o dominio real autorizado
- para MySQL externo, prefira fornecer a string completa em `DATABASE_URL`, porque isso simplifica host, porta, usuario, senha e parametros extras do provedor
- no plano gratuito do Render, a aplicacao sobe sem Redis dedicado; o cache fica desabilitado automaticamente

### Recomendacao pratica

Para o seu momento atual, eu acho um bom caminho subir no Render sim, porque:

- voce consegue colocar a API publica rapido
- ja tem CI no GitHub Actions e isso conversa bem com `checksPass`
- clientes externos podem integrar num endpoint real
- voce nao precisa administrar VPS, proxy reverso e SSL manualmente agora
- o `render.yaml` foi ajustado para evitar custo inicial com Key Value e usar a `Web Service` gratuita

O ponto de atencao fica na conectividade com o banco externo: alguns provedores exigem liberar faixas de IP de saida do Render ou configurar proxy de saida com IP fixo. Se o seu provedor exigir allowlist estrita, valide isso antes do primeiro deploy.

### Usando MySQL externo

Com MySQL externo, o desenho fica:

- Render hospeda a API publica
- Render hospeda o cache interno
- o banco fica em um provedor MySQL gerenciado fora do Render

Nesse caso, configure no Render a variavel `DATABASE_URL` com algo como:

```env
mysql+pymysql://USUARIO:SENHA@HOST:3306/NOME_DO_BANCO
```

Se o seu provedor exigir SSL ou parametros extras, eles entram na propria URL. Exemplo ilustrativo:

```env
mysql+pymysql://USUARIO:SENHA@HOST:3306/NOME_DO_BANCO?charset=utf8mb4
```

Checklist pratico:

1. crie o banco MySQL externo
2. obtenha host, porta, nome do banco, usuario e senha
3. monte a `DATABASE_URL`
4. no Render, preencha `DATABASE_URL` como segredo da `Web Service`
5. se o provedor exigir allowlist de IP, libere as saidas do Render para a regiao do seu servico
6. valide o deploy e depois teste `GET /api/v1/health/ready`

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

Exemplo de uso passando email, nome e telefone pela linha de comando e deixando a senha no `.env` ou no prompt:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_docker_local.ps1 `
  -EmailAdmin "admin@telecom.com" `
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
- testes de integracao com MySQL real
- teste de upgrade e downgrade das migrations
- CI com GitHub Actions em push para `main` e em `pull_request`
- auditoria automatica de dependencias com `pip-audit`
- validacao de build das imagens Docker da API e do MySQL customizado
- varredura automatica das imagens Docker com Trivy

## Exemplos de Uso

### Login

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
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

### Login legado ainda compativel

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
curl http://127.0.0.1:8000/api/v1/users/me \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

### Buscar usuario autenticado em rota legada

```bash
curl http://127.0.0.1:8000/users/me \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

### Buscar plano do usuario autenticado

```bash
curl http://127.0.0.1:8000/api/v1/users/me/plan \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

### Criar plano como administrador

```bash
curl -X POST http://127.0.0.1:8000/api/v1/plans \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Fibra 600\",\"price\":129.9,\"speed\":600}"
```

## Postman

O repositorio possui estrutura para testes manuais em [`postman/`](/c:/Users/MATHEUS-PC/telecom_api/postman) e agora inclui uma collection inicial em [telecom_api.collection.json](/c:/Users/MATHEUS-PC/telecom_api/postman/collections/telecom_api.collection.json).

Para deixar o fluxo mais profissional e reaproveitavel, a collection agora:

- usa `/api/v1` por padrao
- salva `access_token` e `refresh_token` automaticamente apos login e refresh
- captura `user_id` ao criar usuario ou consultar `/users/me`
- captura `plan_id` ao criar plano
- cobre endpoints importantes como `users/me/plan`, cancelamento de assinatura e `admin/stats`

Fluxo sugerido:

1. Importe a collection no Postman.
2. Importe tambem o ambiente [Telecom API Local.environment.yaml](/c:/Users/MATHEUS-PC/telecom_api/postman/environments/Telecom API Local.environment.yaml).
3. Selecione o ambiente importado e ajuste credenciais e dados de exemplo se quiser.
4. Execute `Login Admin` para carregar `access_token` e `refresh_token` automaticamente.
5. Execute `Criar Usuario` e `Criar Plano` para popular `user_id` e `plan_id`.
6. Use os requests autenticados para explorar usuarios, planos e endpoints administrativos sem preencher tudo manualmente.

## CI

O pipeline esta configurado em [ci.yml](/c:/Users/MATHEUS-PC/telecom_api/.github/workflows/ci.yml#L1) e executa:

- instalacao de dependencias
- lint com Ruff
- testes com Pytest
- auditoria de vulnerabilidades nas dependencias Python com `pip-audit`
- build da imagem principal da API
- build da imagem customizada do MySQL
- varredura das imagens Docker com Trivy em severidades `HIGH` e `CRITICAL`
- migrations e testes de integracao contra MySQL real e Redis ativo

O workflow tambem ja força `Node 24` para actions JavaScript, reduzindo o risco de quebra futura por deprecacao do runtime antigo do GitHub Actions.
O bloqueio de vulnerabilidades fica estrito para a imagem da API; a imagem derivada de `mysql:8.0` continua sendo varrida de forma informativa para acompanhar riscos herdados do upstream.

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
- adicionar SBOM e upload de relatórios de seguranca
- evoluir a documentacao com diagramas de sequencia e exemplos reais de deploy

## Autor

- Matheus de Souza Ebert
- GitHub: <https://github.com/MatheusEbert010>
- LinkedIn: <https://linkedin.com/in/matheusebert>
