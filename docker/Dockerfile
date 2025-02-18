FROM python:3.11-slim
LABEL maintainer="mjanez"
LABEL version="1.0"
LABEL description="Easy RDF Endpoint"

ENV CATALOG_FILE=catalog.rdf
ENV WORKERS=2
ENV ENABLE_CORS=false
ENV ALLOWED_ORIGINS="*"

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY ./src /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY ./docker/docker-entrypoint.d/start_server.sh /app/start_server.sh
COPY ./docker/setup/index.html /app/static/index.html
COPY ./docker/setup/robots.txt /app/static/robots.txt
RUN chmod +x /app/start_server.sh

RUN pip install --no-cache-dir --upgrade pip && \
    mkdir -p /app/static && \
    chown -R appuser:appuser /app

    # Change to non-root user
USER appuser

# Copy non-root files
COPY ./data/${CATALOG_FILE} /app/static/catalog.rdf

EXPOSE 5000

CMD ["/app/start_server.sh"]