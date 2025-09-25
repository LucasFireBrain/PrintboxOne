import imaplib, email, os, subprocess, json, datetime
from PyPDF2 import PdfReader

# ==== CONFIG ====
EMAIL_USER = "pbox.cirvid1315@gmail.com"
EMAIL_PASS = "dcoxqeyhvgxytecb"
IMAP_SERVER = "imap.gmail.com"
PRINTER_NAME = "HP_DeskJet_2800_series_35029A_USB_"
WORKDIR = "/home/lucas/printbox/tmp"
LOGFILE = "/home/lucas/printbox/printbox_log.json"
WHITELIST_FILE = "/home/lucas/printbox/whitelist.json"  # optional, for future


# ==== LOGGING ====
def log_event(entry):
    entry["timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")
    logs = []

    # Load existing log if it exists
    if os.path.exists(LOGFILE):
        with open(LOGFILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    logs.append(entry)

    # Save back
    with open(LOGFILE, "w") as f:
        json.dump(logs, f, indent=2)


# ==== PROCESS EMAILS ====
def process_mail():
    os.makedirs(WORKDIR, exist_ok=True)

    print("[INFO] Connecting to Gmail...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    print("[INFO] Checking for new emails...")
    status, messages = mail.search(None, "UNSEEN")
    if messages == [b""]:
        print("[INFO] No new emails found.")
        log_event({"status": "no_jobs"})
    else:
        for num in messages[0].split():
            status, data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            sender = email.utils.parseaddr(msg["From"])[1]
            subject = msg.get("Subject", "(no subject)")
            print(f"[INFO] New email from {sender}, subject: {subject}")

            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename()
                    if filename and filename.lower().endswith(".pdf"):
                        filepath = os.path.join(WORKDIR, filename)
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        print(f"[INFO] Saved PDF: {filename}")

                        # Count PDF pages
                        try:
                            reader = PdfReader(filepath)
                            page_count = len(reader.pages)
                        except Exception:
                            page_count = None

                        # Print
                        try:
                            subprocess.run(["lp", "-d", PRINTER_NAME, filepath], check=True)
                            print(f"[PRINT] Sent {filename} to {PRINTER_NAME}")

                            log_event({
                                "status": "printed",
                                "sender": sender,
                                "apartment": "unknown",  # placeholder until whitelist is used
                                "file": filename,
                                "pages": page_count
                            })
                        except subprocess.CalledProcessError as e:
                            print(f"[ERROR] Failed to print {filename}: {e}")
                            log_event({
                                "status": "error",
                                "sender": sender,
                                "file": filename,
                                "error": str(e)
                            })

            mail.store(num, "+FLAGS", "\\Seen")
            print("[INFO] Marked email as read.")

    mail.logout()
    print("[INFO] Done.")


if __name__ == "__main__":
    process_mail()
