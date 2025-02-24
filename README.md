# README - Serving RDF with Docker & Flask

## Overview
This project provides a simple **Dockerized RDF endpoint** that serves an `.rdf` file an provides an SPARQL Endpoint based on [`vemonet/rdflib-endpoint`](https://github.com/vemonet/rdflib-endpoint)

The RDF file using the correct `Content-Type: application/rdf+xml`, ensuring compatibility with **DCAT-AP federators** and **RDF parsers** like `rdflib`.

## Quick Start
Use [Codespaces](https://github.com/features/codespaces) to test `easy-rdf-endpoint` in your browser
<center><a href='https://codespaces.new/mjanez/easy-rdf-endpoint'><img src='https://github.com/codespaces/badge.svg' alt='GitHub Codespaces' style={{maxWidth: '100%'}}/></a></center>

## Getting started
**Requirements**:
* [Docker](https://docs.docker.com/get-docker/)

### Clone and configure
Before starting the deployment, you'll need to set up a `.env` file. This file is crucial as it contains environment variables that the application needs to run properly.

1. Clone project
    ```shell
    cd /path/to/my/project
    git clone https://github.com/mjanez/easy-rdf-endpoint.git & cd easy-rdf-endpoint
    ```

2. Copy the [`.env.example`](.env.example) template and modify the resulting `.env` to suit your needs.

    ```shell
    cp .env.example .env
    ```

    Adjust the vars as necessary, example:
    ```ini
    # Server Configuration
    PROXY_SERVER_NAME=my-example-sparql-server.org

    # RDF of filename in folder ./data 
    CATALOG_FILE=my-custom-catalog.rdf
    ```

3. Build & up the container.

```sh
docker compose up -d
```

Then, access your RDF file an [endpoints](#endpoints).

---

### Endpoints
The endpoints will be available at:
* Landing page[`http://localhost:5000`](http://localhost:5000)
    * Access your RDF file at: [`http://localhost:5000/catalog`](http://localhost:5000/catalog)
    * Default query editor (Yasgui): [`http://localhost:5000/sparql-editor`](http://localhost:5000/sparql-editor)
    * SPARQL endpoint: [`http://localhost:5000/sparql`](http://localhost5000/sparql)

## Project Structure
```sh
/easy-rdf-endpoint
│── /data/catalog.rdf          # Your Catalog RDF file (replace with your own)
│── /doc/                      # References, as images or documents, used in repo
│── /easy-rdf-endpoint/        # RDF+SPARQL Endpoint setup
│── /nginx/                    # NGINX docker setup
│── /src/                      # Now using NGINX instead of the old RDF serving mode
│── .env.example               # Sample ENVVars file for use with Docker Compose
│── docker-compose.yml         # Docker Compose config
│── README.md                  # Documentation
```

[!NOTE]
> - Replace `catalog.rdf` with your actual RDF file.  
> - Works with **Codespaces, Docker, Kubernetes, and any containerized environment**.

## Update SSL Certificate
To update the local SSL certificate, follow these steps:

1. Generate a new certificate and private key:
```sh
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/setup/easy-rdf-endpoint_local.key \
  -out nginx/setup/easy-rdf-endpoint_local.crt \
  -subj "/C=ES/ST=Madrid/L=Madrid/O=Development/CN=localhost"
```

2. Verify that the files have been created correctly:
```sh
ls -l nginx/setup/easy-rdf-endpoint_local.*
```

3. Restart the `nginx` container to apply the changes:
```sh
docker compose restart nginx
```

> [!CAUTION]
> This certificate is for local development only. In production, use a valid certificate from a certificate authority.

## Development

### Using DevContainers
This project supports development using DevContainers, which provides a consistent development environment for all contributors.

**Requirements**:
* [Docker](https://docs.docker.com/get-docker/)
- [VS Code](https://code.visualstudio.com/) or [GitHub Codespaces](https://github.com/features/codespaces)
- [VS Code Remote - Containers extension](https://docs.rancherdesktop.io/how-to-guides/vs-code-remote-containers/)

#### Getting Started with DevContainer
1. Clone the repository:
```bash
git clone https://github.com/mjanez/easy-rdf-endpoint.git
cd easy-rdf-endpoint
```

2. Open in VS Code:
```bash
code .
```

3. When prompted "*Reopen in Container*", click "*Reopen in Container*". Alternatively:
   - Press `F1`
   - Type "*Remote-Containers: Reopen in Container*"
   - Press *Enter*

VS Code will build and start the development container. This may take a few minutes the first time.

#### What's Included
The development container includes:
- Python 3.11 environment
- Required Python packages pre-installed
- Popular VS Code extensions for Python/Docker development
- Git configuration
- Port forwarding for the application

#### Working in the Container
Once inside the container you can:
- Run the application: `exec gunicorn --bind 0.0.0.0:5000 app:app`
- Modify the [`easy-rdf-endpoint/setup/rdflib-endpoint/sparql_override.py`](./easy-rdf-endpoint/setup/rdflib-endpoint/sparql_override.py)
- Execute SPARQL queries: `http://localhost:5000/sparql`
- Debug with VS Code's integrated debugger

## License
This project is licensed under the **MIT License**. 
