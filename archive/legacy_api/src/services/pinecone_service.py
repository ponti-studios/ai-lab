from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from src.data.db import SessionLocal
from src.data.focus_repository import get_focus_vector_documents
from src.data.models.focus import Focus
from src.services.openai_service import openai_embeddings
from src.utils.config import settings

pc = Pinecone(api_key=settings.PINECONE_API_KEY)

focus_index = "mindsherpa-focus"

vector_store = PineconeVectorStore(index=focus_index, embedding=openai_embeddings)


def upsert_focus_to_pinecone():
    session = SessionLocal()
    focus_items = session.query(Focus).filter(Focus.in_vector_store.is_(False)).all()

    documents = get_focus_vector_documents(focus_items)
    data = [{"id": str(focus_item.id), "text": focus_item.text} for focus_item in focus_items]

    if len(data) == 0:
        return

    vector_store.add_documents(documents=documents, ids=[d["id"] for d in data])

    for focus_item in focus_items:
        focus_item.in_vector_store = True

    session.add_all(focus_items)
    session.commit()
    session.flush()
    session.close()
