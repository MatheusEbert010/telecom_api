FROM mysql:8.0

# Copia a configuracao customizada para dentro da imagem com permissao consistente.
COPY conf.d/my.cnf /etc/mysql/conf.d/my.cnf

RUN chmod 644 /etc/mysql/conf.d/my.cnf
