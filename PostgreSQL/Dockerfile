FROM postgres:16-alpine

COPY init-multiple-databases.sh /docker-entrypoint-initdb.d/
RUN sed -i 's/\r$//' /docker-entrypoint-initdb.d/init-multiple-databases.sh
RUN chmod +x /docker-entrypoint-initdb.d/init-multiple-databases.sh