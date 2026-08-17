"""Microsoft Graph email notifications for approval-workflow events.

Uses the client-credentials (app-only) flow with the same Azure AD app registration used for
Microsoft SSO login, via plain httpx calls - no Graph SDK needed for a single sendMail call.
Every public function is best-effort: a failed send is logged and swallowed, never raised, so a
notification outage can never block the underlying approval action.
"""

import base64
import datetime
import logging
from dataclasses import dataclass

import httpx

from app.config import settings
from app.models import Attachment
from app.storage import read_bytes

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
_token_cache: dict[str, str | datetime.datetime | None] = {"token": None, "expires_at": None}

# Graph's sendMail accepts small attachments inline (base64 in the JSON body); beyond a few MB the
# request risks Exchange's message-size limit, so anything over this combined size is sent as a
# secure download link back into the app instead of inflating/risking the email itself.
INLINE_ATTACHMENT_LIMIT_BYTES = 3 * 1024 * 1024


@dataclass
class EmailAttachment:
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    download_url: str


def attachments_for_email(records: list[Attachment]) -> list[EmailAttachment]:
    return [
        EmailAttachment(
            filename=a.filename, content_type=a.content_type, size_bytes=a.size_bytes,
            storage_path=a.storage_path, download_url=f"{settings.backend_base_url}/attachments/{a.id}/download",
        )
        for a in records
    ]


async def _get_graph_token() -> str | None:
    now = datetime.datetime.now(datetime.timezone.utc)
    cached_expiry = _token_cache["expires_at"]
    if _token_cache["token"] and isinstance(cached_expiry, datetime.datetime) and now < cached_expiry:
        return _token_cache["token"]  # type: ignore[return-value]

    if not (settings.microsoft_tenant_id and settings.microsoft_client_id and settings.microsoft_client_secret):
        logger.info("Microsoft Graph credentials not configured — skipping email notification")
        return None

    url = f"https://login.microsoftonline.com/{settings.microsoft_tenant_id}/oauth2/v2.0/token"
    data = {
        "client_id": settings.microsoft_client_id,
        "client_secret": settings.microsoft_client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError:
        logger.exception("Failed to acquire Microsoft Graph app-only token")
        return None

    _token_cache["token"] = body["access_token"]
    _token_cache["expires_at"] = now + datetime.timedelta(seconds=int(body.get("expires_in", 3600)) - 60)
    return _token_cache["token"]  # type: ignore[return-value]


def _render_email(
    heading: str, owner_type: str, owner_id: str, rows: list[tuple[str, str]], link_path: str,
    attachment_note: str | None = None,
) -> str:
    row_html = "".join(
        f'<tr><td style="padding:4px 12px;color:#667085;font-family:sans-serif;font-size:13px;">{label}</td>'
        f'<td style="padding:4px 12px;color:#101828;font-family:sans-serif;font-size:13px;font-weight:600;">{value}</td></tr>'
        for label, value in rows
    )
    link = f"{settings.frontend_base_url}{link_path}"
    attachment_html = (
        f'<p style="color:#475467;font-family:sans-serif;font-size:13px;">{attachment_note}</p>' if attachment_note else ""
    )
    return (
        '<div style="font-family:sans-serif;">'
        f"<h2 style=\"color:#101828;\">{heading}</h2>"
        f"<p style=\"color:#475467;\">{owner_type.replace('_', ' ').title()} <b>{owner_id}</b></p>"
        f'<table style="border-collapse:collapse;margin:12px 0;">{row_html}</table>'
        f"{attachment_html}"
        f'<p><a href="{link}" style="color:#3a5bd9;">Open in Subcontract Module &rarr;</a></p>'
        "</div>"
    )


async def send_email(
    to_email: str, to_name: str, subject: str, html_body: str, graph_attachments: list[dict] | None = None,
) -> None:
    if not settings.microsoft_sender_mailbox:
        logger.info("MICROSOFT_SENDER_MAILBOX not set — skipping email %r to %s", subject, to_email)
        return

    token = await _get_graph_token()
    if not token:
        logger.warning("No Microsoft Graph token available — skipping email %r to %s", subject, to_email)
        return

    message: dict = {
        "subject": subject,
        "body": {"contentType": "HTML", "content": html_body},
        "toRecipients": [{"emailAddress": {"address": to_email, "name": to_name}}],
    }
    if graph_attachments:
        message["attachments"] = graph_attachments
    payload = {"message": message, "saveToSentItems": "true"}
    url = f"{GRAPH_BASE}/users/{settings.microsoft_sender_mailbox}/sendMail"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
            resp.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Failed to send approval notification email %r to %s", subject, to_email)


def _build_inline_attachments(attachments: list[EmailAttachment]) -> list[dict] | None:
    graph_attachments = []
    for a in attachments:
        try:
            content = read_bytes(a.storage_path)
        except OSError:
            logger.exception("Attachment file missing on disk, skipping from email: %s", a.storage_path)
            continue
        graph_attachments.append({
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": a.filename,
            "contentType": a.content_type,
            "contentBytes": base64.b64encode(content).decode("ascii"),
        })
    return graph_attachments or None


async def send_workflow_notification(
    to_email: str | None, to_name: str, heading: str, owner_type: str, owner_id: str,
    rows: list[tuple[str, str]], link_path: str, attachments: list[EmailAttachment] | None = None,
) -> None:
    if not to_email:
        logger.info("No recipient email resolved — skipping %r notification for %s %s", heading, owner_type, owner_id)
        return

    graph_attachments: list[dict] | None = None
    attachment_note: str | None = None
    if attachments:
        total_bytes = sum(a.size_bytes for a in attachments)
        if total_bytes <= INLINE_ATTACHMENT_LIMIT_BYTES:
            graph_attachments = _build_inline_attachments(attachments)
            if graph_attachments:
                attachment_note = f"📎 Attached: {', '.join(a.filename for a in attachments)}"
        if not graph_attachments:
            links = " &middot; ".join(f'<a href="{a.download_url}" style="color:#3a5bd9;">{a.filename}</a>' for a in attachments)
            attachment_note = f"📎 Supporting document{'s' if len(attachments) > 1 else ''}: {links}"

    html = _render_email(heading, owner_type, owner_id, rows, link_path, attachment_note)
    await send_email(to_email, to_name, heading, html, graph_attachments)
