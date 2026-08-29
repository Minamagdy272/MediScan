"""
Explicit Email Delivery Service (Gmail OAuth API - Opt-In Only).
Gated: Sends email ONLY for approved reports.
"""

import base64
from pathlib import Path
from typing import Tuple
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from .config import GMAIL_TOKEN_PATH, GMAIL_CREDENTIALS_PATH


def get_gmail_credentials():
    """Load Gmail OAuth credentials."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    token_path = Path(GMAIL_TOKEN_PATH)
    credentials_path = Path(GMAIL_CREDENTIALS_PATH)

    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(token_path, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
            print("✓ Gmail OAuth token refreshed.")
        except Exception as e:
            print(f"⚠ Gmail token refresh failed: {e}")
            creds = None

    if not creds or not creds.valid:
        if not credentials_path.exists():
            raise FileNotFoundError(
                "Gmail OAuth is not configured.\n"
                f"Missing credentials file: {credentials_path}\n\n"
                "Create OAuth Desktop App credentials in Google Cloud Console and download credentials.json."
            )
        print("Opening Gmail OAuth authorization flow...")
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
        print(f"✓ Gmail authorization completed. Token saved to {token_path}")

    return creds


def send_report_email(pdf_path: str, recipient: str) -> Tuple[bool, str]:
    """Sends an approved PDF report through Gmail API."""
    if not pdf_path:
        return False, "PDF_NOT_AVAILABLE"

    if not Path(pdf_path).exists():
        return False, "PDF_FILE_NOT_FOUND"

    if not recipient or "@" not in recipient:
        return False, "INVALID_RECIPIENT"

    try:
        from googleapiclient.discovery import build

        creds = get_gmail_credentials()
        service = build("gmail", "v1", credentials=creds)

        message = MIMEMultipart()
        message["to"] = recipient
        message["subject"] = "MediScan Clinical Decision Support Report"
        message.attach(
            MIMEText(
                "Please find attached the approved MediScan evidence-grounded clinical decision support report.\n\n"
                "Important: MediScan is a research prototype and does not replace licensed clinical judgment.",
                "plain"
            )
        )

        with open(pdf_path, "rb") as f:
            attachment = MIMEApplication(f.read(), _subtype="pdf")
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=Path(pdf_path).name
            )
            message.attach(attachment)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        result = service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        message_id = result.get("id")

        if not message_id:
            return False, "GMAIL_API_RETURNED_NO_MESSAGE_ID"

        print(f"✓ Email successfully sent to {recipient}")
        return True, f"SENT:{message_id}"

    except FileNotFoundError as e:
        print(f"✗ Gmail configuration unavailable: {e}")
        return False, f"GMAIL_NOT_CONFIGURED:{e}"
    except Exception as e:
        print(f"✗ Gmail delivery failed: {e}")
        return False, f"GMAIL_SEND_FAILED:{e}"
