FROM python:3.11-slim

LABEL maintainer="mjanez"
LABEL version="1.0"
LABEL description="Easy RDF Endpoint"

ENV CATALOG_FILE=catalog.rdf \
    WORKERS=2 \
    ENABLE_CORS=false \
    ALLOWED_ORIGINS="*"

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY ./src/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /app/
COPY ./easy-rdf-endpoint/docker-entrypoint.d/start_server.sh /app/start_server.sh

RUN chmod +x /app/start_server.sh && \
    mkdir -p /app/static && \
    chown -R appuser:appuser /app

# Change to non-root user
USER appuser

# Copy non-root files
COPY ./data/${CATALOG_FILE} /app/static/catalog.rdf

EXPOSE 5000

CMD ["/app/start_server.sh"]