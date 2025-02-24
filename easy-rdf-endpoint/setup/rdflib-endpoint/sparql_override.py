import os
import json
from typing import Dict, Any
from rdflib import Dataset
from rdflib_endpoint import SparqlEndpoint
import uvicorn

class CustomSparqlEndpoint(SparqlEndpoint):
    """A custom SPARQL endpoint that extends RDFlib's SparqlEndpoint.

    This class provides a configurable SPARQL endpoint that loads its configuration
    from environment variables.

    Args:
        graph (Dataset): The RDF dataset to be queried through the endpoint.
    """
    def __init__(self, graph: Dataset):
        config = self._load_config()
        
        super().__init__(
            graph=graph,
            path="/",
            cors_enabled=True,
            **config
        )

    def _load_config(self) -> Dict[str, Any]:
        """Loads configuration from environment variables.

        Returns:
            Dict[str, Any]: A dictionary containing the endpoint configuration with keys:
                - title: The endpoint title
                - description: The endpoint description
                - version: The endpoint version
                - example_query: The default SPARQL query
                - example_queries: Additional example queries
        """
        try:
            example_queries = json.loads(os.getenv("EXAMPLE_SPARQL_QUERIES", "{}"))
        except json.JSONDecodeError:
            print("WARNING: Error parsing EXAMPLE_SPARQL_QUERIES, using defaults")
            example_queries = {}

        return {
            "title": os.getenv("SPARQL_ENDPOINT_TITLE", "SPARQL endpoint from RDF file"),
            "description": os.getenv("SPARQL_ENDPOINT_DESCRIPTION", "SPARQL endpoint for querying a RDF data catalog"),
            "version": os.getenv("SPARQL_ENDPOINT_VERSION", "1.0.0"),
            "example_query": os.getenv("DEFAULT_SPARQL_QUERY", 
                """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT * WHERE {
                    ?s ?p ?o .
                } LIMIT 100"""),
            "example_queries": example_queries
        }

def create_app():
    """Creates and configures the FastAPI application.

    This function initializes the RDF dataset, loads the catalog data,
    and creates a new SPARQL endpoint instance.

    Returns:
        CustomSparqlEndpoint: A configured SPARQL endpoint instance.
    """
    # Initializing the network
    g = Dataset(store="Oxigraph")
    catalog_path = os.path.join("/app/data", os.getenv("CATALOG_FILE", "catalog.rdf"))
    g.parse(catalog_path)
    print(f"[Custom SPARQL Endpoint] INFO: 📥️ Loaded triples from {catalog_path}, total: {len(g)}")

    # Create and return endpoint
    return CustomSparqlEndpoint(graph=g)

def main():
    """Main entry point for the application.

    Initializes and runs the SPARQL endpoint server using uvicorn.
    The server configuration (host, port, workers) can be customized
    through environment variables.
    """
    app = create_app()
    uvicorn.run(
        "sparql_override:create_app",
        host="0.0.0.0",
        port=8000,
        workers=int(os.getenv("WORKERS", "2")),
        factory=True
    )

if __name__ == "__main__":
    main()