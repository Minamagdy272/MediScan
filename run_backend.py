"""
Convenience launcher for the MediScan FastAPI Backend Server.
"""

import sys
from pathlib import Path
import uvicorn

# Add src to python path
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print("=" * 65)
    print("  Starting MediScan Clinical Decision Support FastAPI Server")
    print("  API URL    : http://localhost:8000")
    print("  API Docs   : http://localhost:8000/docs")
    print("  Health     : http://localhost:8000/api/health")
    print("=" * 65)
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
