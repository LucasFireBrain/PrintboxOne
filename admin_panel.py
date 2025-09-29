from printbox_core import process_mail_once, LOG_FILE
import json
import subprocess
import re

CONFIG_PATH = "/home/lucas/printbox/config.py"

def show_printer_status():
    result = subprocess.run(["lpstat", "-p", "-d"], capture_output=True, text=True)
    print(result.stdout.strip())

def show_job_queue():
    try:
        result = subprocess.run(["lpq"], capture_output=True, text=True, check=True)
        print(result.stdout.strip())
    except FileNotFoundError:
        print("[WARN] lpq command not found. Install it with: sudo apt install cups-bsd")
    except subprocess.CalledProcessError as e:
        print("[ERROR] Could not get job queue:", e)

def show_logs():
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
            for entry in logs[-10:]:  # last 10
                print(entry)
    except FileNotFoundError:
        print("No logs yet.")

def list_printers():
    """List printers detected by CUPS"""
    result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    printers = []
    for line in lines:
        m = re.match(r"^printer\s+(\S+)", line)
        if m:
            printers.append(m.group(1))
    return printers

def choose_printer():
    """Prompt user to select a printer and save to config.py"""
    printers = list_printers()
    if not printers:
        print("[WARN] No printers found. Is your USB printer plugged in and CUPS installed?")
        return
    print("\nAvailable printers:")
    for idx, p in enumerate(printers, 1):
        print(f"[{idx}] {p}")
    choice = input("Select printer number: ").strip()
    try:
        chosen = printers[int(choice)-1]
    except (IndexError, ValueError):
        print("[ERROR] Invalid choice")
        return

    # Update config.py
    with open(CONFIG_PATH, "r") as f:
        cfg = f.read()
    new_cfg = re.sub(r'PRINTER_NAME\s*=\s*".*"', f'PRINTER_NAME = "{chosen}"', cfg)
    with open(CONFIG_PATH, "w") as f:
        f.write(new_cfg)

    print(f"[INFO] Default printer updated to: {chosen}")

def menu():
    while True:
        print("""
=========================
     PrintBox Admin
=========================
[1] Printer status
[2] Job queue
[3] View last logs
[4] Check inbox once
[5] Choose printer
[6] Exit
""")
        choice = input("Select option: ").strip()

        if choice == "1":
            show_printer_status()
        elif choice == "2":
            show_job_queue()
        elif choice == "3":
            show_logs()
        elif choice == "4":
            process_mail_once()
        elif choice == "5":
            choose_printer()
        elif choice == "6":
            break
        input("\n[ENTER] to continue…")

if __name__ == "__main__":
    menu()
