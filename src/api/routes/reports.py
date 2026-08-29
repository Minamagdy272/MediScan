"""
FastAPI Reports & Email Delivery Endpoints.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.post("/generate")
def generate_report(payload: dict):
    """Generates PDF for the current session or supplied text."""
    from pipeline.pdf_service import generate_pdf_report
    from pipeline.session import session_store
    
    session_id = payload.get("session_id", "default")
    report_text = payload.get("report_text")

    if not report_text:
        history = session_store.get_history(session_id)
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                report_text = msg.get("content")
                break

    if not report_text:
        raise HTTPException(status_code=400, detail="No clinical report found for this session.")

    pdf_path = generate_pdf_report(
        report_text=report_text,
        session_id=session_id,
        final_action="ACCEPT"
    )
    filename = Path(pdf_path).name

    return {
        "status": "success",
        "pdf_path": pdf_path,
        "filename": filename,
        "download_url": f"/api/reports/download/{filename}"
    }


@router.get("/download/{filename}")
def download_report(filename: str):
    """Downloads a generated PDF report."""
    from pipeline.config import REPORTS_DIR

    safe_filename = Path(filename).name
    file_path = REPORTS_DIR / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested report PDF does not exist.")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=safe_filename
    )


@router.post("/email")
def email_report(payload: dict):
    """Emails an approved PDF report to the requested recipient."""
    from pipeline.email_service import send_report_email
    from pipeline.config import REPORTS_DIR

    recipient_email = payload.get("recipient_email")
    if not recipient_email or "@" not in recipient_email:
        raise HTTPException(status_code=400, detail="Valid recipient email required.")

    pdf_filename = payload.get("pdf_filename")
    pdf_path = None
    if pdf_filename:
        pdf_path = str(REPORTS_DIR / Path(pdf_filename).name)
    else:
        reports = list(REPORTS_DIR.glob("*.pdf"))
        if reports:
            reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            pdf_path = str(reports[0])

    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="No approved PDF report available to send.")

    success, message = send_report_email(pdf_path, recipient_email)
    if not success:
        raise HTTPException(status_code=500, detail=f"Email delivery failed: {message}")

    return {
        "status": "sent",
        "recipient": recipient_email,
        "pdf_attached": Path(pdf_path).name,
        "delivery_message": message
    }
