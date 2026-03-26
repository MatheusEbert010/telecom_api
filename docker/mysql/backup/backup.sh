#!/bin/sh

set -eu

echo "Iniciando rotina de backup do MySQL"

while true
do
  timestamp="$(date +%Y-%m-%d_%H-%M-%S)"
  arquivo="/backups/${MYSQL_DATABASE}_${timestamp}.sql"

  echo "Gerando backup em ${arquivo}"
  mysqldump \
    --host="${MYSQL_HOST}" \
    --user="${MYSQL_USER}" \
    --password="${MYSQL_PASSWORD}" \
    --single-transaction \
    --quick \
    --routines \
    --triggers \
    "${MYSQL_DATABASE}" > "${arquivo}"

  echo "Removendo backups com mais de ${BACKUP_RETENTION_DAYS} dias"
  find /backups -type f -name "*.sql" -mtime +"${BACKUP_RETENTION_DAYS}" -delete

  echo "Backup concluido. Aguardando ${BACKUP_INTERVAL_HOURS} horas para a proxima execucao"
  sleep "$((BACKUP_INTERVAL_HOURS * 3600))"
done
