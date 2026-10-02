import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException

from services.auth import verify_api_key
from services.ingestion import ingest_pdf
from services.vectorstore import get_weaviate_client, ensure_schema, COLLECTION_NAME

router = APIRouter()

UPLOAD_DIR = "/app/uploads"
MAX_FILE_SIZE_MB = 25


@router.get("/documents")
async def list_documents(api_key: str = Depends(verify_api_key)):
    ensure_schema()
    client = get_weaviate_client()
    collection = client.collections.get(COLLECTION_NAME)

    seen: dict[str, dict] = {}
    for obj in collection.iterator():
        doc_id = obj.properties.get("document_id")
        if doc_id not in seen:
            seen[doc_id] = {
                "document_id": doc_id,
                "document_name": obj.properties.get("document_name"),
                "chunks_indexed": 0,
            }
        seen[doc_id]["chunks_indexed"] += 1

    return list(seen.values())


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    temp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.pdf")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    with open(temp_path, "wb") as f:
        f.write(content)

    try:
        result = await ingest_pdf(temp_path, document_name=file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return result
