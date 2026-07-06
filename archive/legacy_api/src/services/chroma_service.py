import traceback

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma

from src.services.openai_service import openai_embeddings
from src.utils.config import settings
from src.utils.logger import logger

chroma_client = None

_host = settings.CHROMA_SERVER_HOST
_port = settings.CHROMA_SERVER_HTTP_PORT if settings.CHROMA_SERVER_HTTP_PORT else 8000

_settings = Settings(
    chroma_server_host=_host,
    chroma_server_http_port=_port,
    chroma_client_auth_provider=settings.CHROMA_SERVER_AUTH_PROVIDER,
    chroma_client_auth_credentials=settings.CHROMA_SERVER_AUTH_CREDENTIALS,
    chroma_auth_token_transport_header=settings.CHROMA_AUTH_TOKEN_TRANSPORT_HEADER,
)

chroma_client = (
    chromadb.HttpClient(
        host=settings.CHROMA_SERVER_HOST,
        port=_port,
        settings=_settings,
    )
    if settings.ENVIRONMENT == "production" and not settings.CI
    else chromadb.Client()
)

vector_store = Chroma(
    client=chroma_client,
    collection_name="focus",
    embedding_function=openai_embeddings,
    persist_directory=".chroma" if settings.ENVIRONMENT == "test" else None,
)


def get_collection(name: str):
    if not chroma_client:
        return None

    return chroma_client.get_collection(name)


def clear_focus_items_from_vector_store():
    try:
        logger.info("Resetting Chroma vector store.")
        vector_store.reset_collection()
        logger.info("Reset Chroma vector store.")
    except Exception:
        traceback.print_exc()
        logger.error("Error resetting ChromaDB vector store")
