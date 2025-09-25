import os
import imaplib
import email
from email.header import decode_header
from email.message import EmailMessage
import subprocess
import json
from datetime import datetime
import importlib.util
import smtplib
from typing import Optional
from PyPDF2 import PdfReader, PdfWriter

# ----------------------------
# Load config
# ----------------------------
CONFIG_FILE = "/home/lucas/printbox/config.py"
spec = importlib.util.spec_from_file_location("config", CONFIG_FILE)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

EMAIL_USER = config.EMAIL_USER
EMAIL_APP_PASSWORD = config.EMAIL_APP_PASSWORD
IMAP_SERVER = "imap.gmail.com"
PRINTER_NAME = config.PRINTER_NAME
SMTP_SERVER = config.SMTP_SERVER
SMTP_PORT = config.SMTP_PORT

LOG_FILE = "/home/lucas/printbox/log.json"
QUOTAS_FILE = config.QUOTAS_FILE

# Default paper size
DEFAULT_MEDIA = "Letter"

# ----------------------------
# Helpers
# ----------------------------
def log_event(event: dict):
    """Append event with timestamp into log.json"""
    event["timestamp"] = datetime.now().isoformat()
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    logs.append(event)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def load_json_file(path: str, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        print(f"[WARN] Could not parse JSON from {path}; using default value.")
        return default


def save_json_file(path: str, data) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)


def get_pdf_page_count(path: str) -> Optional[int]:
    try:
        reader = PdfReader(path)
        return len(reader.pages)
    except Exception as e:
        print(f"[WARN] Could not read PDF page count: {e}")
        return None


def send_email(to_address: str, subject: str, body: str) -> bool:
    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email to {to_address}: {e}")
        log_event({
            "status": "email_error",
            "recipient": to_address,
            "error": str(e)
        })
        return False


def notify_insufficient_quota(sender: str, filename: str, needed_pages: int, remaining_pages: int) -> None:
    subject = "Print job could not be completed"
    body = (
        "Hello,\n\n"
        "Your recent print request could not be completed because your remaining "
        "PrintBox quota is insufficient.\n\n"
        f"Document: {filename}\n"
        f"Pages requested: {needed_pages}\n"
        f"Pages remaining: {remaining_pages}\n\n"
        "Please contact your administrator to request additional quota.\n\n"
        "— PrintBox"
    )

    if send_email(sender, subject, body):
        log_event({
            "status": "quota_email_sent",
            "sender": sender,
            "file": filename,
            "needed_pages": needed_pages,
            "remaining_pages": remaining_pages
        })


def decode_str(s):
    parts = decode_header(s)
    decoded = ""
    for text, enc in parts:
        if isinstance(text, bytes):
            decoded += text.decode(enc or "utf-8", errors="ignore")
        else:
            decoded += text
    return decoded


def reverse_pdf(input_path, output_path):
    """Reverse page order of PDF so page 1 ends up on top of stack."""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages[::-1]:
            writer.add_page(page)
        with open(output_path, "wb") as f:
            writer.write(f)
        return True
    except Exception as e:
        print(f"[WARN] Could not reverse PDF: {e}")
        return False

# ----------------------------
# Core function
# ----------------------------
def process_mail_once():
    try:
        print("[INFO] Connecting to Gmail (IMAP)…")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_APP_PASSWORD)
        mail.select("inbox")

        print("[INFO] Checking UNSEEN emails…")
        status, messages = mail.search(None, '(UNSEEN)')
        if status != "OK":
            print("[ERROR] Could not fetch emails.")
            return

        msg_ids = messages[0].split()
        if not msg_ids:
            print("[INFO] No new emails.")
            log_event({"status": "no_jobs"})
            return

        quotas = load_json_file(QUOTAS_FILE, {})
        quotas_dirty = False

        for msg_id in msg_ids:
            status, data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(data[0][1])
            sender = email.utils.parseaddr(msg.get("From"))[1]
            subject = decode_str(msg.get("Subject", ""))

            print(f"[INFO] From {sender} | Subject: {subject}")

            pdf_found = False
            for part in msg.walk():
                if part.get_content_type() == "application/pdf":
                    filename = decode_str(part.get_filename())
                    if not filename:
                        filename = "document.pdf"

                    filepath = os.path.join("/home/lucas/printbox", filename)
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))

                    pdf_found = True
                    print(f"[INFO] Saved PDF: {filename}")

                    page_count = get_pdf_page_count(filepath)
                    if page_count is None:
                        log_event({
                            "status": "page_count_error",
                            "sender": sender,
                            "file": filename
                        })
                        continue

                    # 🔄 Reverse PDF so page 1 prints on top
                    reversed_path = filepath.replace(".pdf", "_reversed.pdf")
                    if reverse_pdf(filepath, reversed_path):
                        final_path = reversed_path
                    else:
                        final_path = filepath

                    remaining_quota = quotas.get(sender)
                    if remaining_quota is not None:
                        if remaining_quota < page_count:
                            print(
                                f"[WARN] Not enough quota for {sender}: "
                                f"needed {page_count}, remaining {remaining_quota}"
                            )
                            notify_insufficient_quota(sender, filename, page_count, remaining_quota)
                            log_event({
                                "status": "quota_insufficient",
                                "sender": sender,
                                "file": filename,
                                "needed_pages": page_count,
                                "remaining_pages": remaining_quota
                            })
                            continue
                        quotas[sender] = remaining_quota - page_count
                        quotas_dirty = True

                    # 🔒 Always force Letter, single-sided, fit-to-page
                    abs_path = os.path.abspath(final_path)
                    result = subprocess.run([
                        "lp",
                        "-o", "sides=one-sided",
                        "-o", f"media={DEFAULT_MEDIA}",
                        "-o", "fit-to-page",
                        "-d", PRINTER_NAME,
                        abs_path
                    ], capture_output=True, text=True)

                    print(result.stdout.strip())
                    print(f"[PRINT] Sent {filename} (reversed) to {PRINTER_NAME}")

                    log_event({
                        "status": "printed",
                        "sender": sender,
                        "file": filename,
                        "reversed": True,
                        "pages": page_count
                    })

            if not pdf_found:
                print("[INFO] No PDFs → marking as read.")
                log_event({"status": "no_pdf_in_email", "sender": sender})

            # Mark email as seen
            mail.store(msg_id, "+FLAGS", "\\Seen")

        if quotas_dirty:
            save_json_file(QUOTAS_FILE, quotas)

        mail.logout()
        print("[INFO] Done.")

    except Exception as e:
        print(f"[ERROR] {e}")
        log_event({"status": "error", "error": str(e)})
