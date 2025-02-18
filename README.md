# README - Serving RDF with Docker & Flask

## Overview
This project provides a simple **Dockerized RDF endpoint** that serves an `.rdf` file with the correct `Content-Type: application/rdf+xml`, ensuring compatibility with **DCAT-AP federators** and **RDF parsers** like `rdflib`.

## Quick Start 
### Run with Docker
```sh
docker build -t rdf-server .
docker run -p 5000:5000 -v $(pwd)/catalog.rdf:/app/catalog.rdf rdf-server
```

Then, access your RDF file at: 

  👉 `http://localhost:5000/catalog.rdf`

### Run with Docker Compose (Optional)
If you prefer `docker-compose`, use:  

```sh
docker-compose up -d
```
---

## **🛠 Project Structure**
```
/rdf-server
│── catalog.rdf           # Your RDF file (replace with your own)
│── app.py                # Flask server to serve RDF
│── Dockerfile            # Docker setup
│── requirements.txt      # Python dependencies
│── docker-compose.yml    # Optional: Docker Compose config
│── README.md             # Documentation
```

---

## Code Explanation

### Flask App (`app.py`)
A minimal Flask server to serve `catalog.rdf` with the correct `Content-Type`.  

```python
from flask import Flask, send_file

app = Flask(__name__)

@app.route("/catalog.rdf")
def serve_rdf():
    return send_file("catalog.rdf", mimetype="application/rdf+xml")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

---

### Dockerfile
This Dockerfile creates a lightweight Flask container.  

```dockerfile
# Use lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy required files
COPY app.py requirements.txt catalog.rdf .  

# Install dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 5000

# Run Flask server
CMD ["python", "app.py"]
```

---

### Python Dependencies (`requirements.txt`)
```txt
flask
```

---

### Docker Compose (Optional)
For easier deployment using `docker-compose`.  

```yaml
version: '3.8'
services:
  rdf-server:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./catalog.rdf:/app/catalog.rdf
```

---

## Deploy in Codespaces
1. Open **GitHub Codespaces**.  
2. Clone this repository.  
3. Run:  
   ```sh
   docker-compose up -d
   ```
4. Access: `http://localhost:5000/catalog.rdf`  

---

## Notes
- Replace `catalog.rdf` with your actual RDF file.  
- Modify `app.py` if you need additional routes or enhancements.  
- Works with **Codespaces, Docker, Kubernetes, and any containerized environment**.

## License
This project is licensed under the **MIT License**. 
