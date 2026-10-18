"""Acceso de solo lectura a Google Calendar para una cuenta (alias)."""
from datetime import datetime, timedelta

from googleapiclient.discovery import build

from .google_auth import load_credentials

MAX_DESC_CHARS = 500


def _service(alias: str):
    return build("calendar", "v3", credentials=load_credentials(alias), cache_discovery=False)


def _day_bounds(desde_dias: int, hasta_dias: int) -> tuple[str, str]:
    """Rango [hoy+desde_dias 00:00, hoy+hasta_dias 00:00) en la zona horaria local."""
    today = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    return (today + timedelta(days=desde_dias)).isoformat(), (today + timedelta(days=hasta_dias)).isoformat()


def _event(alias: str, cal_name: str, ev: dict) -> dict:
    start, end = ev.get("start", {}), ev.get("end", {})
    desc = (ev.get("description") or "").strip()
    return {
        "cuenta": alias,
        "calendario": cal_name,
        "titulo": ev.get("summary", "(sin título)"),
        "inicio": start.get("dateTime") or start.get("date"),
        "fin": end.get("dateTime") or end.get("date"),
        "todo_el_dia": "date" in start,
        "ubicacion": ev.get("location", ""),
        "descripcion": desc[:MAX_DESC_CHARS] + ("…" if len(desc) > MAX_DESC_CHARS else ""),
        "enlace": ev.get("htmlLink", ""),
    }


def list_events(alias: str, desde_dias: int, hasta_dias: int) -> list[dict]:
    svc = _service(alias)
    time_min, time_max = _day_bounds(desde_dias, hasta_dias)
    events = []
    # Solo los calendarios que tienes visibles (marcados) en Google Calendar.
    for cal in svc.calendarList().list().execute().get("items", []):
        if not cal.get("selected", False):
            continue
        resp = svc.events().list(
            calendarId=cal["id"], timeMin=time_min, timeMax=time_max,
            singleEvents=True, orderBy="startTime", maxResults=50,
        ).execute()
        name = cal.get("summaryOverride") or cal.get("summary", cal["id"])
        events.extend(_event(alias, name, ev) for ev in resp.get("items", []))
    return events
