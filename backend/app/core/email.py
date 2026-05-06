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


async def send_approval_email(
    requester_name: str,
    requester_email: str,
    temporary_password: str,
) -> bool:
    """Send approval email to requester with login credentials."""
    subject = "Your LAOS Account Has Been Created"
    
    body = f"""
Dear {requester_name},

Your access request has been approved, and your account has been created.

Login Credentials:
Email: {requester_email}
Temporary Password: {temporary_password}

Login at: {settings.FRONTEND_URL or 'http://localhost:5173'}

IMPORTANT: Please change your password upon first login for security.

Best regards,
LAOS Admin System
    """.strip()

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #003366;">Access Approved</h2>
                <p>Dear {requester_name},</p>
                <p>Your access request has been approved, and your account has been created.</p>
                
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Login Credentials</h3>
                    <table style="border-collapse: collapse; width: 100%;">
                        <tr>
                            <td style="padding: 8px; font-weight: bold; width: 120px;">Email:</td>
                            <td style="padding: 8px; font-family: monospace;">{requester_email}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; font-weight: bold;">Password:</td>
                            <td style="padding: 8px; font-family: monospace; background-color: #fff3cd; padding: 8px; border-radius: 3px;">{temporary_password}</td>
                        </tr>
                    </table>
                </div>
                
                <p style="background-color: #fff3cd; padding: 12px; border-left: 4px solid #ffc107; border-radius: 3px;">
                    <strong>IMPORTANT:</strong> Please change your password upon first login for security.
                </p>
                
                <p>
                    <a href="{settings.FRONTEND_URL or 'http://localhost:5173'}" style="display: inline-block; padding: 10px 20px; background-color: #003366; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">
                        Go to LAOS
                    </a>
                </p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">
                    This is an automated email from LAOS Admin System. Please do not reply to this email.
                </p>
            </div>
        </body>
    </html>
    """

    return await send_email(
        subject=subject,
        recipient=requester_email,
        body=body,
        html_body=html_body,
    )


async def send_rejection_email(
    requester_name: str,
    requester_email: str,
    rejection_reason: str = "Your access request could not be approved at this time.",
) -> bool:
    """Send rejection email to requester."""
    subject = "Your LAOS Access Request - Unable to Approve"
    
    body = f"""
Dear {requester_name},

Thank you for your interest in accessing LAOS (Legal Action Orchestration System).

Unfortunately, your access request could not be approved.

Reason: {rejection_reason}

If you have questions, please contact the LAOS administrator.

Best regards,
LAOS Admin System
    """.strip()

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #d32f2f;">Request Status</h2>
                <p>Dear {requester_name},</p>
                <p>Thank you for your interest in accessing LAOS (Legal Action Orchestration System).</p>
                
                <div style="background-color: #ffebee; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #d32f2f;">
                    <h3 style="margin-top: 0; color: #d32f2f;">Access Request Not Approved</h3>
                    <p><strong>Reason:</strong> {rejection_reason}</p>
                </div>
                
                <p>If you have questions or would like to resubmit your request, please contact the LAOS administrator.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">
                    This is an automated email from LAOS Admin System. Please do not reply to this email.
                </p>
            </div>
        </body>
    </html>
    """

    return await send_email(
        subject=subject,
        recipient=requester_email,
        body=body,
        html_body=html_body,
    )
