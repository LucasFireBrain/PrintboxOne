from printbox_core import process_mail_once, LOG_FILE
import json
import subprocess

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
[5] Exit
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
            break
        input("\n[ENTER] to continue…")

if __name__ == "__main__":
    menu()
