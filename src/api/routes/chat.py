"""
FastAPI Chat & Streaming Endpoints.
"""

import json
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    """Validated, user-supplied chat request."""

    message: str = Field(min_length=1, max_length=12000)
    session_id: str | None = Field(default=None, max_length=128)
    generate_pdf: bool = False
    send_email: bool = False
    email_recipient: str | None = Field(default=None, max_length=320)

    def resolved_session_id(self) -> str:
        if self.session_id and self.session_id.strip():
            return self.session_id.strip()
        return f"api-{uuid4().hex}"


@router.post("")
def execute_chat(payload: ChatRequest):
    """Synchronous chat endpoint executing the full MediScan Agentic RAG pipeline."""
    from pipeline.coordinator import run_pipeline
    try:
        response = run_pipeline(
            user_message=payload.message.strip(),
            session_id=payload.resolved_session_id(),
            generate_pdf=payload.generate_pdf,
            send_email=payload.send_email,
            email_recipient=payload.email_recipient,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")


@router.post("/stream")
async def stream_chat(payload: ChatRequest):
    """SSE Streaming endpoint yielding live real-time pipeline stages and final payload."""
    from pipeline.coordinator import stream_pipeline

    async def event_generator():
        try:
            async for item in stream_pipeline(
                user_message=payload.message.strip(),
                session_id=payload.resolved_session_id(),
                generate_pdf=payload.generate_pdf,
                send_email=payload.send_email,
                email_recipient=payload.email_recipient,
            ):
                event_name = item.get("event", "message")
                data_str = json.dumps(item.get("data", {}))
                yield f"event: {event_name}\ndata: {data_str}\n\n"
        except Exception as e:
            error_data = json.dumps({"stage": "error", "error": str(e)})
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/sessions")
def get_sessions() -> List[str]:
    """Returns list of active in-memory chat session IDs."""
    from pipeline.session import session_store
    return session_store.list_sessions()


@router.get("/sessions/{session_id}")
def get_session_history(session_id: str) -> List[Dict[str, str]]:
    """Returns conversation history for a given session ID."""
    from pipeline.session import session_store
    return session_store.get_history(session_id)


@router.delete("/sessions/{session_id}")
def clear_session_history(session_id: str):
    """Clears conversation history for a given session ID."""
    from pipeline.session import session_store
    session_store.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}
