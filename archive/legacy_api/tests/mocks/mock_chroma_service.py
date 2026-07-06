from unittest.mock import MagicMock

# Mock the chromadb.HttpClient
chroma_client = MagicMock()

# Mock the Chroma vector store
vector_store = MagicMock()


def get_collection(name: str):
    return MagicMock()


def clear_focus_items_from_vector_store():
    pass
