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

def choose_printer():
    try:
        result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().splitlines()
        printers = []
        for line in lines:
            if line.startswith("printer "):
                printers.append(line.split()[1])

        if not printers:
            print("[WARN] No printers found. Is your USB printer plugged in and CUPS running?")
            return

        print("\nAvailable printers:")
        for i, p in enumerate(printers, start=1):
            print(f"[{i}] {p}")

        choice = input("Select printer number: ").strip()
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(printers):
            print("[ERROR] Invalid choice.")
            return

        selected = printers[int(choice) - 1]

        # Set as system default
        subprocess.run(["sudo", "lpoptions", "-d", selected], check=False)

        print(f"[INFO] Default printer updated to: {selected}")

    except subprocess.CalledProcessError as e:
        print("[ERROR] Could not list printers:", e)

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
[5] Choose printer (set default)
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
