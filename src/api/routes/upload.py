"""
FastAPI Upload & Ingestion Endpoints.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/api/upload", tags=["Upload"])


@router.post("")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a clinical findings document or text file and extracts structured findings."""
    from pipeline.extraction import extract_clinical_info

    try:
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")

        if not text.strip():
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        extracted = extract_clinical_info(text)

        return {
            "filename": file.filename,
            "text_preview": text[:500],
            "extracted_findings": extracted.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process uploaded file: {str(e)}")
