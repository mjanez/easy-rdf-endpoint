# README - Serving RDF with Docker & Flask

## Overview
This project provides a simple **Dockerized RDF endpoint** that serves an `.rdf` file with the correct `Content-Type: application/rdf+xml`, ensuring compatibility with **DCAT-AP federators** and **RDF parsers** like `rdflib`.


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
    git clone https://github.com/mjanez/easy-rdf-endpoint.git & cd ckan-docker
    ```

2. Copy the `.env.example` template and modify the resulting `.env` to suit your needs.

    ```shell
    cp .env.example .env
    ```

    Adjust the vars as necessary
    ```ini
    # Host Ports
    SV_PORT_HOST=5000

    # Options
    CATALOG_FILE=catalog.rdf
    ```

3. Build & up the container.

```sh
docker compose up -d
```

Then, access your RDF file at: 

  👉 `http://localhost:5000/catalog.rdf`

---

## Project Structure
```
/rdf-server
│── /data/catalog.rdf          # Your RDF file (replace with your own)
│── /scr/app.py                # Flask server to serve RDF
│── /src/requirements.txt      # Python dependencies
│── /docker/Dockerfile         # Docker setup
│── docker-compose.yml         # Docker Compose config
│── README.md                  # Documentation
```

## Notes
- Replace `catalog.rdf` with your actual RDF file.  
- Modify `app.py` if you need additional routes or enhancements.  
- Works with **Codespaces, Docker, Kubernetes, and any containerized environment**.

## License
This project is licensed under the **MIT License**. 
