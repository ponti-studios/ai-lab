import traceback

from langchain_core.documents import Document
from sqlalchemy.orm import Session

from src.data.models.focus import Focus
from src.services import chroma_service
from src.services.keywords.keywords_service import get_query_keywords
from src.utils.logger import logger


def delete_none_ids_from_chroma():
    try:
        collection = chroma_service.get_collection("focus")
        if not collection:
            return

        result = collection.get(ids=["None"])
        documents = result["documents"]
        if documents:
            if len(documents) > 0:
                logger.info("No None IDs to delete from Chroma.")
                return

            logger.info(f"Deleting None IDs from Chroma: {len(documents)}")
            collection.delete(ids=["None"])
            logger.info(f"{len(documents)} None IDs deleted from Chroma.")
    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error deleting None IDs from Chroma: {e}")


def refresh_focus_from_chroma(session: Session):
    try:
        focus_items = session.query(Focus).filter(Focus.in_vector_store.is_(False)).all()
        if not focus_items:
            return

        logger.info(f"Processing {len(focus_items)} focus items for Chroma")
        focus_ids = [str(focus_item.id) for focus_item in focus_items]
        existing_docs = chroma_service.vector_store.get(ids=focus_ids)
        existing_ids = set(existing_docs["ids"])

        for focus_item in focus_items:
            focus_id = str(focus_item.id)
            keyword_str = ",".join(get_query_keywords(focus_item.text))
            page_content = f"{focus_item.text} \n\n {keyword_str}"
            document = Document(
                page_content=page_content,
                metadata=focus_item.to_json(),
            )

            if focus_id in existing_ids:
                # Update existing document
                chroma_service.vector_store.update_document(
                    document_id=focus_id,
                    document=document,
                )
                logger.info(f"Updated focus item {focus_id} in Chroma")
            else:
                # Add new document
                chroma_service.vector_store.add_documents(
                    documents=[document],
                    ids=[focus_id],
                )
                logger.info(f"Added new focus item {focus_id} to Chroma")

        # Mark all processed items as in_vector_store
        session.query(Focus).filter(Focus.id.in_([focus_item.id for focus_item in focus_items])).update(
            {"in_vector_store": True}
        )
        session.commit()
        logger.info(f"Marked {len(focus_items)} focus items as in_vector_store")

    except Exception as e:
        traceback.print_exc()
        logger.error(f"Error refreshing focus items from vector store: {e}")
