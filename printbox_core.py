import os
import imaplib
import email
from email.header import decode_header
import subprocess
import json
from datetime import datetime
import importlib.util
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

LOG_FILE = "/home/lucas/printbox/log.json"

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

                    # 🔄 Reverse PDF so page 1 prints on top
                    reversed_path = filepath.replace(".pdf", "_reversed.pdf")
                    if reverse_pdf(filepath, reversed_path):
                        final_path = reversed_path
                    else:
                        final_path = filepath

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
                        "reversed": True
                    })

            if not pdf_found:
                print("[INFO] No PDFs → marking as read.")
                log_event({"status": "no_pdf_in_email", "sender": sender})

            # Mark email as seen
            mail.store(msg_id, "+FLAGS", "\\Seen")

        mail.logout()
        print("[INFO] Done.")

    except Exception as e:
        print(f"[ERROR] {e}")
        log_event({"status": "error", "error": str(e)})
