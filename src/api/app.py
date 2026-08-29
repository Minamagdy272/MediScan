"""
FastAPI Application Entrypoint for MediScan.
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure project root & src are on python path
src_dir = Path(__file__).resolve().parent.parent
project_root = src_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from api.routes.chat import router as chat_router
from api.routes.reports import router as reports_router
from api.routes.upload import router as upload_router
from api.routes.health import router as health_router

app = FastAPI(
    title="MediScan Clinical Decision Support API",
    description="Evidence-Grounded Agentic RAG API with Controlled Policy Gating",
    version="1.0.0"
)

# CORS configuration for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows Angular (http://localhost:4200, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(chat_router)
app.include_router(reports_router)
app.include_router(upload_router)
app.include_router(health_router)

# Mount static reports directory (lazy - only if dir exists)
reports_dir = project_root / "reports"
if reports_dir.exists():
    app.mount("/static/reports", StaticFiles(directory=str(reports_dir)), name="reports")


@app.get("/")
def root():
    return {
        "app": "MediScan Clinical AI Assistant",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
