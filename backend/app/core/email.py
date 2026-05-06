"""Email sending utilities."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings


async def send_email(
    subject: str,
    recipient: str,
    body: str,
    html_body: Optional[str] = None,
) -> bool:
    """
    Send an email.
    
    Args:
        subject: Email subject
        recipient: Recipient email address
        body: Plain text body
        html_body: Optional HTML body
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not settings.SMTP_ENABLED:
            print(f"[EMAIL MOCK] To: {recipient}, Subject: {subject}")
            print(f"Body:\n{body}")
            return True

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = recipient

        # Attach plain text
        part1 = MIMEText(body, "plain")
        msg.attach(part1)

        # Attach HTML if provided
        if html_body:
            part2 = MIMEText(html_body, "html")
            msg.attach(part2)

        # Send via SMTP
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, recipient, msg.as_string())

        return True

    except Exception as e:
        print(f"Error sending email to {recipient}: {e}")
        return False


async def send_access_request_notification(
    requester_name: str,
    requester_email: str,
) -> bool:
    """Send notification to admin about new access request."""
    subject = f"New Access Request: {requester_name}"
    
    body = f"""
A new officer has requested access to LAOS.

Name: {requester_name}
Email: {requester_email}

Please review and create an account if approved.

---
LAOS Admin System
    """.strip()

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>New Access Request</h2>
            <p>A new officer has requested access to the LAOS system.</p>
            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Name:</td>
                    <td style="padding: 8px;">{requester_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Email:</td>
                    <td style="padding: 8px;">{requester_email}</td>
                </tr>
            </table>
            <p style="color: #666; font-size: 12px;">
                Please review this request and create an account if approved.
            </p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">LAOS Admin System</p>
        </body>
    </html>
    """

    return await send_email(
        subject=subject,
        recipient=settings.ADMIN_EMAIL,
        body=body,
        html_body=html_body,
    )
