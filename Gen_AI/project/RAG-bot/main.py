import os

from dotenv import load_dotenv
from elasticsearch import Elasticsearch

from src.generation.response_generation import generate_response
from src.ingestion.indexing import create_index_if_not_exists
from src.ingestion.ingestion import run_ingestion_pipeline

load_dotenv()

# Configure Elasticsearch client using environment variables with sensible fallbacks.
es_cloud_id = os.getenv("ES_CLOUD_ID")
es_api_key = os.getenv("ES_API_KEY")
es_hosts = os.getenv("ES_HOSTS")  # comma-separated, e.g. "http://localhost:9200"
es_username = os.getenv("ES_USERNAME")
es_password = os.getenv("ES_PASSWORD")

if es_cloud_id and es_api_key:
    client = Elasticsearch(cloud_id=es_cloud_id, api_key=es_api_key)
elif es_hosts:
    hosts = [h.strip() for h in es_hosts.split(",") if h.strip()]
    if es_username and es_password:
        client = Elasticsearch(hosts=hosts, http_auth=(es_username, es_password))
    else:
        client = Elasticsearch(hosts=hosts)
else:
    # Default to a local Elasticsearch instance
    client = Elasticsearch(hosts=["http://localhost:9200"])

# Quick connection check to provide a clear error if Elasticsearch is unreachable
try:
    if not client.ping():
        raise RuntimeError("Elasticsearch cluster is not responding to ping. Check your ES configuration.")
except Exception as exc:
    raise RuntimeError(f"Failed to connect to Elasticsearch: {exc}") from exc

# Ensure the index exists
create_index_if_not_exists(client)

if __name__ == "__main__":
    # Run the ingestion pipeline
    ingest_flag = False
    run_ingestion_pipeline(client, ingest_flag)

    # Generate a response using GPT-3.5
    query_text = "Sabka Saath, Sabka Vikas"
    response = generate_response(client, query_text)
