"""
MediScan Pipeline Configuration.
Loads environment variables and sets system-wide paths and model configurations.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Detect project root directory (contains src, data, vectorstore, reports)
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent if current_dir.name == "pipeline" else current_dir

# Load .env file
env_path = project_root / "src" / ".env"
if not env_path.exists():
    env_path = project_root / ".env"

load_dotenv(dotenv_path=env_path)

# Reports output directory
REPORTS_DIR = project_root / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# API & Model Endpoints
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

ROUTER_MODEL = os.getenv("ROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b")
AGENT_MODEL = os.getenv("AGENT_MODEL", "z-ai/glm-5.3-flash")
EVALUATOR_MODEL = os.getenv("EVALUATOR_MODEL", "deepseek-ai/deepseek-v4-flash-0731")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "nvidia/llama-nemotron-rerank-1b-v2")

# Gmail OAuth Paths
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", str(project_root / "token.json"))
GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", str(project_root / "credentials.json"))
