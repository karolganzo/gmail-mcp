"""Rutas y constantes compartidas.

Todo lo sensible (credenciales y tokens) vive en ~/.gmail-mcp, fuera del repo.
"""
from pathlib import Path

CONFIG_DIR = Path.home() / ".gmail-mcp"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKENS_DIR = CONFIG_DIR / "tokens"

# Solo lectura: el servidor nunca puede enviar, borrar ni modificar nada.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def token_path(alias: str) -> Path:
    return TOKENS_DIR / f"{alias}.json"


def list_aliases() -> list[str]:
    if not TOKENS_DIR.exists():
        return []
    return sorted(p.stem for p in TOKENS_DIR.glob("*.json"))
