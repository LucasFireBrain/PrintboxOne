# PrintboxOne

PrintboxOne is a small proof-of-concept service that turns a shared email inbox into a community print station. Residents send PDFs to the mailbox, the service watches for new messages, and any attachments are pushed to a local printer while the activity is logged for quota tracking. The project is currently an MVP, but it lays the groundwork for richer features such as user metadata, quota enforcement, and email notifications.

## Why it exists
Managing a shared printer usually means juggling USB drives, managing accounts manually, and keeping track of who printed what. PrintboxOne streamlines the process:

1. **Central inbox** – people send their documents to a designated Gmail account.
2. **Automated processing** – the service checks the inbox, saves PDF attachments, and prints them with consistent settings.
3. **Activity log** – every job is written to a JSON log so that admins can review usage and, later, calculate remaining quota.
4. **Admin tools** – a simple command-line menu lets you check printer status, review recent jobs, or trigger a manual inbox scan.

## Repository at a glance
| File | Purpose |
| --- | --- |
| `printbox_core.py` | Main worker that connects to Gmail, downloads PDFs, prepares them, and prints through CUPS. |
| `admin_panel.py` | Text-based admin console for printer status, queue inspection, logs, and triggering `printbox_core.process_mail_once()`. |
| `config.py` | Central configuration: email credentials, printer name, data file paths, and scheduling preferences. |
| `setup_printbox.sh` | Bootstrap script for a Linux host. Creates folders/JSON files and installs Python dependencies. |
| `printbox_simple.py` | Earlier minimal script kept for reference; `printbox_core.py` is the recommended entry point. |

Generated data lives under `/home/lucas/printbox/` by default (configurable). That folder stores temp downloads, logs, quota JSON, and whitelist data.

## Prerequisites
- **Hardware**: A printer managed by CUPS on a Linux machine (e.g., Raspberry Pi, Ubuntu desktop).
- **Software**:
  - Python 3.9+
  - `pip` and the `PyPDF2` package
  - CUPS command-line tools (`lp`, `lpstat`, optionally `lpq`)
- **Google account**: Create or repurpose a Gmail inbox, enable IMAP, and generate an App Password if you use multi-factor authentication.

> ⚠️ Keep credentials safe. `config.py` contains plain-text passwords; restrict file permissions and consider using environment variables or a secrets manager in production.

## Quick start (first-time setup)
1. **Copy the repository onto the print host**
   ```bash
   git clone https://github.com/your-org/PrintboxOne.git
   cd PrintboxOne
   ```
2. **Run the setup helper** (creates folders and installs dependencies)
   ```bash
   chmod +x setup_printbox.sh
   ./setup_printbox.sh
   ```
3. **Update `config.py`** with your Gmail user, app password, printer name, and (optionally) custom paths.
4. **Move the runtime files** (`config.py`, `printbox_core.py`, `admin_panel.py`) into the working directory defined in `config.py` (default `/home/lucas/printbox/`).

You can run everything directly from the repo while experimenting, but keeping runtime files in the dedicated folder makes log and data paths consistent with the defaults.

## How printing works
1. `printbox_core.process_mail_once()` logs into the Gmail inbox via IMAP and looks for unread messages.
2. Each email is inspected for PDF attachments. For every PDF:
   - The file is saved to the working directory.
   - Pages are reversed so that page 1 lands on top of the output stack (handy for manual duplexing).
   - The file is printed with CUPS using one-sided, Letter-sized, fit-to-page settings.
   - The event (sender, filename, success/error) is recorded in `log.json`.
3. Emails without PDFs are marked as read and noted in the log.

All actions append to `log.json`, which you can parse later to calculate per-user usage or detect failures.

## Running the service
### One-off check
```bash
python3 -c "from printbox_core import process_mail_once; process_mail_once()"
```

### Using the admin panel
```bash
python3 admin_panel.py
```
The menu lets you:
- Inspect printer status (`lpstat -p -d`)
- View the current print queue (`lpq`)
- Show the 10 most recent log entries
- Trigger a single mailbox scan/print cycle

### Continuous operation
For a continuous loop, wrap `process_mail_once()` in your own scheduler. Two simple options:
- **Cron** – run `printbox_core` every few minutes.
- **systemd service + timer** – more robust for production.

Future versions will use the values in `config.POLL_INTERVAL_SEC` and `RUN_CONTINUOUS_DEFAULT` to provide a built-in loop.

## Managing metadata and quotas
The MVP lays the groundwork for quota tracking:
- `whitelist.json` can store user metadata (e.g., apartment number, allowed printers).
- `quotas.json` will track remaining page counts per user.
- Each log entry records the sender and pages printed, making it possible to decrement quota after each job.

These files are currently populated manually. A typical shape is:
```json
{
  "user@example.com": {
    "name": "Alex Doe",
    "apartment": "2B",
    "monthly_quota": 50,
    "quota_remaining": 32
  }
}
```

As you extend the project you can add helpers that validate senders, reject jobs that exceed quota, and update totals automatically.

## Roadmap ideas
- Send confirmation emails with job status, page count, and remaining quota.
- Expose a simple web dashboard for residents and admins.
- Add authentication/authorization for the admin panel.
- Expand printer options (duplex, color, paper size) per user or per job.
- Automatically back up logs/quotas to the addresses listed in `config.BACKUP_TO`.

## Troubleshooting
| Symptom | Likely fix |
| --- | --- |
| `imaplib` login fails | Verify Gmail IMAP is enabled and the App Password is correct. |
| `lp`/`lpstat` not found | Install CUPS utilities: `sudo apt install cups-bsd`. |
| PDF prints in reverse order | The script intentionally reverses pages; adjust `reverse_pdf` if you prefer the original order. |
| Nothing prints, but log shows jobs | Check `PRINTER_NAME` in `config.py` matches `lpstat -p -d` exactly. |

## Contributing
This project is still evolving. Feel free to experiment locally, document findings, and propose changes that make the service easier for non-technical admins to operate. Pull requests that improve onboarding (e.g., scripts, docs, or configuration helpers) are especially welcome.
