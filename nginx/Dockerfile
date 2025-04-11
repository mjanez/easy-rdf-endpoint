FROM nginx:stable-alpine

ENV PROXY_SPARQL_LOCATION=/sparql-editor \
    PROXY_SPARQL_ENDPOINT=/sparql \
    PROXY_CATALOG_LOCATION=/catalog \
    PROXY_VALIDATOR_LOCATION=/validator

ENV CATALOG_PORT=5000
ENV SPARQL_PORT=8000
ENV VALIDATOR_PORT=8501
ENV CATALOG_COMPOSE_SERVICE=rdf-endpoint
ENV SPARQL_COMPOSE_SERVICE=sparql-endpoint
ENV VALIDATOR_COMPOSE_SERVICE=rdf-validator
ENV PROXY_SERVER_NAME=localhost
ENV PROXY_CATALOG_PROXY_PASS=http://${CATALOG_COMPOSE_SERVICE}:${CATALOG_PORT}
ENV PROXY_SPARQL_PROXY_PASS=http://${SPARQL_COMPOSE_SERVICE}:${SPARQL_PORT}
ENV PROXY_VALIDATOR_PROXY_PASS=http://${VALIDATOR_COMPOSE_SERVICE}:${VALIDATOR_PORT}

ENV NGINX_PORT=80
ENV NGINX_SSLPORT=443
ENV NGINX_LOG_DIR=/var/log/nginx
ENV NGINX_DIR=/etc/nginx
ENV NGINX_SHARE_HTML_DIR=/usr/share/nginx/html

RUN mkdir -p ${NGINX_LOG_DIR} \
    && mkdir -p ${NGINX_DIR}/certs

# Copy configuration and static files
COPY ./nginx/setup/nginx.conf ${NGINX_DIR}/nginx.conf
COPY ./nginx/setup/default.conf.template ${NGINX_DIR}/templates/default.conf.template
COPY ./nginx/setup/easy-rdf-endpoint_local.* ${NGINX_DIR}/certs/
COPY ./nginx/setup/html/ ${NGINX_SHARE_HTML_DIR}/
COPY ./nginx/setup/css/ ${NGINX_SHARE_HTML_DIR}/css/
COPY ./nginx/setup/img/ ${NGINX_SHARE_HTML_DIR}/img/
COPY ./nginx/setup/js/ ${NGINX_SHARE_HTML_DIR}/js/

# Replace $PROXY_CATALOG_LOCATION, $PROXY_SPARQL_LOCATION and $PROXY_VALIDATOR_LOCATION in index.html
RUN sed -i "s|<a href=\"/catalog\">|<a href=\"${PROXY_CATALOG_LOCATION}\">|g; s|<a href=\"/csw\">|<a href=\"${PROXY_SPARQL_LOCATION}\">|g; s|<a href=\"/validator\">|<a href=\"${PROXY_VALIDATOR_LOCATION}\">|g" ${NGINX_SHARE_HTML_DIR}/index.html

EXPOSE ${NGINX_PORT}