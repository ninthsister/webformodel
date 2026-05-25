from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent

PATIENT_ROOT = BASE_DIR / "static" / "patient"
UPLOAD_DIR = BASE_DIR / "uploads"
RESULT_DIR = BASE_DIR / "static" / "results"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)
PATIENT_ROOT.mkdir(parents=True, exist_ok=True)

