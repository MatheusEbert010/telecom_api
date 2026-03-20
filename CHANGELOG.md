# Changelog

Todas as mudancas relevantes deste projeto serao documentadas aqui.

Este arquivo segue a ideia do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e utiliza versionamento semantico.

## [Unreleased]

### Added

- Estrutura de testes com `pytest`, incluindo testes de seguranca, integracao HTTP e migrations.
- Pipeline de CI no GitHub Actions para executar lint e testes automaticamente.
- Collection inicial do Postman para explorar os principais fluxos da API.
- Camada de servicos para planos, reduzindo acoplamento dos routers.
- Helpers centralizados para datas em UTC.
- Documentacao interna com docstrings e comentarios concisos em portugues.

### Changed

- README reestruturado para refletir a arquitetura, o fluxo de autenticacao, os exemplos de uso e a estrategia de qualidade do projeto.
- Routers reorganizados para usar `response_model` seguros e validacoes mais claras.
- Fluxo de autenticacao endurecido com rotacao de refresh token.
- Projeto preparado para lint com Ruff e configuracao central em `pyproject.toml`.
- Migrations revisadas para funcionar corretamente em banco limpo.

### Security

- Bloqueada a escalada de privilegio no cadastro e na atualizacao comum de usuarios.
- Persistencia de refresh tokens alterada para hash em vez de texto puro.
- Middleware e respostas revisados para reduzir exposicao de informacoes sensiveis.
- Regras de RBAC reforcadas em usuarios, auth e planos.

### Fixed

- Correcao do conflito de rota entre `/users/me` e `/{user_id}`.
- Correcao da serializacao de objetos ORM no cache.
- Correcao de warnings de `utcnow` com normalizacao para UTC.
- Correcao do bootstrap do Alembic e da cadeia de migrations.
