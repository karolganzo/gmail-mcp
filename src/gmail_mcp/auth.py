"""Autoriza una cuenta de Gmail y guarda su token.

Uso:
    uv run python -m gmail_mcp.auth <alias>     # ej. personal, personal2, unam
    uv run python -m gmail_mcp.auth --list
"""
import re
import sys

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import CREDENTIALS_FILE, SCOPES, TOKENS_DIR, list_aliases, token_path

ALIAS_RE = re.compile(r"^[a-z0-9_-]{1,32}$")


def authorize(alias: str) -> None:
    if not ALIAS_RE.match(alias):
        sys.exit("Alias inválido: usa minúsculas, números, '-' o '_' (máx. 32).")
    if not CREDENTIALS_FILE.exists():
        sys.exit(f"No encontré {CREDENTIALS_FILE}")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    # Abre el navegador; elige la cuenta que corresponde a este alias.
    creds = flow.run_local_server(port=0, prompt="consent select_account")

    email = build("gmail", "v1", credentials=creds).users().getProfile(userId="me").execute()["emailAddress"]

    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    token_path(alias).write_text(creds.to_json(), encoding="utf-8")
    print(f"OK: '{alias}' -> {email}")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "--list":
        aliases = list_aliases()
        print("\n".join(aliases) if aliases else "No hay cuentas autorizadas.")
        return
    authorize(args[0])


if __name__ == "__main__":
    main()
