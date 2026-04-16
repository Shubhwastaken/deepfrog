import chromadb
from chromadb.config import Settings
import os

# Define where ChromaDB will store its data
CHROMA_DATA_PATH = os.path.join(os.getcwd(), "chroma_data")

if not os.path.exists(CHROMA_DATA_PATH):
    os.makedirs(CHROMA_DATA_PATH)

def get_chroma_client():
    """Initializes and returns a persistent ChromaDB client."""
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    return client

def get_or_create_collection(collection_name="customs_docs"):
    """Gets or creates a collection in ChromaDB."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(name=collection_name)
    return collection
