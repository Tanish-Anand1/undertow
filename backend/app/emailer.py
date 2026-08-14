from __future__ import annotations

from app.config import get_settings


def build_digest_email_body(email: str, digest: dict) -> str:
    lines = [
        f"Undertow daily digest for {email}",
        "=" * 40,
        f"High-signal posts (last {digest['hours']}h): {digest['total']}",
        "",
    ]
    for group in digest["by_tag"]:
        lines.append(f"[{group['tag']}] {group['count']}")
    lines.append("")
    lines.append("Top posts")
    lines.append("-" * 40)

    flat = []
    for group in digest["by_tag"]:
        for post, _wl in group["posts"]:
            flat.append(post)
    flat.sort(key=lambda p: float(p.relevance_score or 0), reverse=True)

    for post in flat[:5]:
        lines.append(
            f"* ({post.relevance_score:.0f}) [{post.tag}] {post.title[:100]}\n"
            f"  {post.source} - {post.url}"
        )
        lines.append("")

    if not flat:
        lines.append("No high-relevance hits this period. Keep listening.")

    lines.append("")
    lines.append("- Undertow")
    return "\n".join(lines)


def send_email(to_email: str, subject: str, body: str) -> bool:
    settings = get_settings()
    if not settings.sendgrid_api_key:
        print(f"[email] SENDGRID_API_KEY not set — would send to {to_email}:\n{subject}\n{body[:500]}")
        return False

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=settings.sendgrid_from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body,
        )
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        resp = sg.send(message)
        print(f"[email] sent to {to_email} status={resp.status_code}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[email] failed for {to_email}: {exc}")
        return False
