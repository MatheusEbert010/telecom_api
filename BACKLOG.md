# Pendencias

Pendencias priorizadas para evolucao da Telecom API.

## Concluido nesta rodada

- [x] Tornar CORS configuravel por ambiente e habilitar `PATCH`, `OPTIONS` e `HEAD`.
- [x] Alinhar autenticacao com o contrato real da API usando `HTTPBearer`.
- [x] Evitar refresh tokens orfaos ao deletar usuario, pensando em uso com MySQL.
- [x] Ajustar `docker-compose` e container para subir a app com migrations automaticas.
- [x] Trocar `price` de `float` para `Decimal/Numeric`.
- [x] Remover uso de `KEYS` no Redis e limpar cache com `scan_iter`.
- [x] Centralizar configuracoes antes hardcoded e alinhar versao base do runtime.
- [x] Remover rota duplicada de assinatura por `/plans/{user_id}/subscribe`.
- [x] Adicionar paginacao na listagem de planos.
- [x] Adicionar log em arquivo rotativo da aplicacao.
- [x] Endurecer o ambiente Docker local com MySQL configurado e backup basico.

## Curto prazo

- [ ] Adicionar endpoint para revogar todas as sessoes de um usuario.
- [ ] Expor metricas de aplicacao com Prometheus ou endpoint dedicado.
- [ ] Criar seeds opcionais para ambiente local e demonstracoes.
- [ ] Cobrir cenarios de concorrencia para refresh token e atualizacao de usuario.
- [ ] Adicionar teste de integracao focado em MySQL real via Docker.
- [ ] Adicionar restauracao automatizada de backup para ambiente local e homologacao.

## Medio prazo

- [ ] Separar o dominio em modulos mais explicitos, como `auth`, `users` e `plans`.
- [ ] Adicionar versionamento de API com prefixo como `/api/v1`.
- [ ] Evoluir logs para formato estruturado com correlation id por requisicao.
- [ ] Criar camada de settings por ambiente com validacoes mais fortes para producao.
- [ ] Introduzir soft delete ou trilha de auditoria para operacoes administrativas.

## Longo prazo

- [ ] Adicionar observabilidade completa com traces, metricas e dashboards.
- [ ] Implementar tarefas assicronas para operacoes mais pesadas.
- [ ] Criar pipeline de deploy com rollback e smoke tests automatizados.
- [ ] Publicar documentacao de arquitetura e runbooks operacionais.
