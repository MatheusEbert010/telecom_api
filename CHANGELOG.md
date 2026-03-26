# Changelog

Todas as mudancas relevantes deste projeto serao documentadas aqui.

Este arquivo segue a ideia do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e utiliza versionamento semantico.

## [1.2.0] - 2026-03-26

### Added

- Prefixo preferencial `/api/v1` para auth, usuarios, planos, administracao e health, mantendo compatibilidade com as rotas legadas.
- Endpoint `GET /users/me/plan` para consulta dedicada do plano do usuario autenticado.
- Endpoint `DELETE /users/{user_id}/subscribe` para cancelamento de assinatura.
- Endpoint `GET /admin/stats` com metricas administrativas consolidadas.
- Script de bootstrap local para subir Docker e criar administrador com um unico comando.

### Changed

- Contrato de erro padronizado com `code` e `detail`, incluindo lista `errors` nas falhas de validacao.
- Query avancada de usuarios movida para o repository para reduzir acoplamento no service.
- `Plan.speed` passou a ser obrigatorio tambem no banco de dados.
- Indices adicionados em `users.role` e `users.plan_id` para melhorar filtros e contagens.
- Documentacao atualizada para refletir a versao `1.2.0`, o novo prefixo e os endpoints recentes.

### Security

- Rotas legadas mantidas como compatibilidade e marcadas como obsoletas na documentacao para orientar a migracao.

### Infra

- Stack Docker validada com MySQL local em container, incluindo migrations aplicadas ate `head`.
- Backup local e logs em arquivo mantidos como parte do fluxo de ambiente.

## [Unreleased]

- Espaco reservado para as proximas mudancas.
