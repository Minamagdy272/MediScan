"""
config.py - Central configuration for the MediScan VDB & Retrieval system.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve project paths
PACKAGE_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = SRC_ROOT.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
EXTERNAL_DATA_DIR = DATA_DIR / "external_sources"
REGISTRY_DIR = DATA_DIR / "registry"
SOURCE_REGISTRY_CSV = REGISTRY_DIR / "source_registry.csv"

OPENI_XML_DIR = DATA_DIR / "radiology" / "ecgen-radiology"

VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore" / "chromadb"
BM25_INDEX_PATH = PROJECT_ROOT / "vectorstore" / "bm25_index.pkl"

# Load environment variables
ENV_PATH = SRC_ROOT / ".env"
load_dotenv(ENV_PATH)

# NVIDIA NIM Configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nvidia/llama-nemotron-embed-vl-1b-v2")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "nvidia/llama-nemotron-rerank-1b-v2")

# OpenRouter & Agent Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b")
EVALUATOR_MODEL = os.getenv("EVALUATOR_MODEL", "deepseek-ai/deepseek-v4-flash-0731")

# Chunking Hyperparameters
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 150
MAX_REPORT_CHUNK_SIZE = 1000

# Hybrid Retrieval Settings
DENSE_TOP_K = 20
SPARSE_TOP_K = 20
RERANK_TOP_K = 5
RRF_K_CONSTANT = 60
