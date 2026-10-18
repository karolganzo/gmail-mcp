"""Servidor MCP de solo lectura para varias cuentas de Gmail.

Importante: en transporte stdio, stdout es el canal del protocolo.
Nunca uses print() aquí; usa logging (va a stderr).
"""
import logging

from mcp.server import MCPServer

from . import gmail_client as gc
from .config import list_aliases

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("gmail-mcp")

mcp = MCPServer("gmail-multi")

TODAS = "todas"


def _targets(cuenta: str) -> list[str]:
    return list_aliases() if cuenta == TODAS else [cuenta]


@mcp.tool()
def listar_cuentas() -> list[dict]:
    """Lista las cuentas de Gmail conectadas (alias y dirección de correo)."""
    cuentas = []
    for alias in list_aliases():
        try:
            cuentas.append({"alias": alias, "correo": gc.profile_email(alias), "estado": "ok"})
        except gc.AccountError as e:
            cuentas.append({"alias": alias, "correo": None, "estado": str(e)})
    return cuentas


@mcp.tool()
def buscar_correos(consulta: str, cuenta: str = TODAS, max_resultados: int = 10) -> dict:
    """Busca correos con la sintaxis de búsqueda de Gmail.

    Args:
        consulta: Búsqueda de Gmail, ej. "is:unread newer_than:2d" o "from:banco".
        cuenta: Alias de la cuenta, o "todas" para buscar en todas.
        max_resultados: Máximo por cuenta (1-25).
    """
    max_resultados = max(1, min(max_resultados, 25))
    resultados, errores = [], {}
    for alias in _targets(cuenta):
        try:
            resultados.extend(gc.search(alias, consulta, max_resultados))
        except gc.AccountError as e:
            errores[alias] = str(e)
        except Exception as e:  # errores de red / API: se reportan sin tumbar el servidor
            log.exception("Error buscando en %s", alias)
            errores[alias] = f"Error de la API: {e}"
    return {"resultados": resultados, "errores": errores}


@mcp.tool()
def leer_hilo(cuenta: str, thread_id: str) -> list[dict]:
    """Lee un hilo completo (todos sus mensajes con el cuerpo en texto).

    Args:
        cuenta: Alias de la cuenta donde está el hilo.
        thread_id: El thread_id devuelto por buscar_correos.
    """
    return gc.read_thread(cuenta, thread_id)


def main() -> None:
    mcp.run()  # stdio por defecto


if __name__ == "__main__":
    main()
