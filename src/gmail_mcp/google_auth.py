"""Carga y renueva las credenciales OAuth de cada cuenta (alias)."""
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from .config import SCOPES, list_aliases, token_path


class AccountError(Exception):
    """Error que se le muestra a Claude con instrucciones claras."""


def _reauth_hint(alias: str) -> str:
    return f"Re-autoriza con: uv run python -m gmail_mcp.auth {alias}"


def load_credentials(alias: str) -> Credentials:
    if alias not in list_aliases():
        raise AccountError(f"La cuenta '{alias}' no existe. Disponibles: {', '.join(list_aliases()) or 'ninguna'}.")

    path = token_path(alias)
    # Se leen los permisos guardados en el token (no los forzamos) para
    # detectar tokens viejos a los que les falta un permiso nuevo.
    creds = Credentials.from_authorized_user_file(str(path))
    if not set(SCOPES) <= set(creds.scopes or []):
        raise AccountError(f"El token de '{alias}' no tiene todos los permisos necesarios. {_reauth_hint(alias)}")

    if creds.valid:
        return creds
    try:
        creds.refresh(Request())
    except RefreshError as e:
        # En modo "Prueba", Google invalida los tokens cada 7 días.
        raise AccountError(f"El token de '{alias}' expiró. {_reauth_hint(alias)}") from e
    path.write_text(creds.to_json(), encoding="utf-8")
    return creds
