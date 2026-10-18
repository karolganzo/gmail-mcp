"""Acceso a la Gmail API para una cuenta (alias)."""
import base64
import html
import re

from googleapiclient.discovery import build

from .google_auth import AccountError, load_credentials  # noqa: F401 (re-export)

MAX_BODY_CHARS = 4000


def service(alias: str):
    # Se construye por llamada: así siempre usa un token vigente (y refrescado).
    return build("gmail", "v1", credentials=load_credentials(alias), cache_discovery=False)


def _headers(msg: dict) -> dict[str, str]:
    wanted = {"from", "to", "subject", "date"}
    return {
        h["name"].lower(): h["value"]
        for h in msg.get("payload", {}).get("headers", [])
        if h["name"].lower() in wanted
    }


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def _find_part(payload: dict, mime: str) -> str | None:
    if payload.get("mimeType") == mime and payload.get("body", {}).get("data"):
        return _decode(payload["body"]["data"])
    for part in payload.get("parts", []) or []:
        found = _find_part(part, mime)
        if found:
            return found
    return None


def _html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?</\1>", "", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", raw)
    text = html.unescape(re.sub(r"<[^>]+>", "", raw))
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def body_text(msg: dict) -> str:
    payload = msg.get("payload", {})
    text = _find_part(payload, "text/plain")
    if text is None:
        raw_html = _find_part(payload, "text/html")
        text = _html_to_text(raw_html) if raw_html else ""
    text = text.strip()
    if len(text) > MAX_BODY_CHARS:
        text = text[:MAX_BODY_CHARS] + "\n[... recortado]"
    return text


def summarize(alias: str, msg: dict) -> dict:
    h = _headers(msg)
    return {
        "cuenta": alias,
        "id": msg["id"],
        "thread_id": msg["threadId"],
        "de": h.get("from", ""),
        "asunto": h.get("subject", "(sin asunto)"),
        "fecha": h.get("date", ""),
        "no_leido": "UNREAD" in msg.get("labelIds", []),
        "fragmento": html.unescape(msg.get("snippet", "")),
    }


def search(alias: str, query: str, max_results: int) -> list[dict]:
    svc = service(alias)
    resp = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    results = []
    for ref in resp.get("messages", []):
        msg = svc.users().messages().get(
            userId="me", id=ref["id"], format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute()
        results.append(summarize(alias, msg))
    return results


def read_thread(alias: str, thread_id: str) -> list[dict]:
    thread = service(alias).users().threads().get(userId="me", id=thread_id, format="full").execute()
    out = []
    for msg in thread.get("messages", []):
        item = summarize(alias, msg)
        item["cuerpo"] = body_text(msg)
        out.append(item)
    return out


def profile_email(alias: str) -> str:
    return service(alias).users().getProfile(userId="me").execute()["emailAddress"]
