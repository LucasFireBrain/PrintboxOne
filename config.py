# /home/lucas/printbox/config.py

# ==== EMAIL (Gmail) ====
EMAIL_USER = "pbox.cirvid1315@gmail.com"     # the shared inbox residents send to
EMAIL_APP_PASSWORD = "dcoxqeyhvgxytecb"
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587                                 # STARTTLS

# Where to send daily backups (your email, committee, etc.)
BACKUP_TO = ["pbox.cirvid1315@gmail.com"]

# ==== PRINTER / CUPS ====
PRINTER_NAME = "HP_DeskJet_2800_series_35029A_USB_"  # lpstat -p -d shows this
WORKDIR = "/home/lucas/printbox/tmp"

# ==== DATA FILES (local JSON “DB”) ====
LOGFILE = "/home/lucas/printbox/printbox_log.json"
WHITELIST_FILE = "/home/lucas/printbox/whitelist.json"
QUOTAS_FILE = "/home/lucas/printbox/quotas.json"

# ==== LOOP & HOURS ====
OPERATING_HOURS = (8, 22)      # from 08:00 to 22:00
POLL_INTERVAL_SEC = 300        # 5 minutes
RUN_CONTINUOUS_DEFAULT = False # toggled in admin panel
