from printbox_core import process_mail_once, LOG_FILE, QUOTAS_FILE
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
            for entry in logs[-10:]:
                print(entry)
    except FileNotFoundError:
        print("No logs yet.")

def choose_printer():
    result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True)
    printers = []
    for line in result.stdout.strip().splitlines():
        if line.startswith("printer "):
            name = line.split()[1]
            printers.append(name)

    if not printers:
        print("[WARN] No printers found. Is your USB printer plugged in and CUPS installed?")
        return

    print("\nAvailable printers:")
    for i, p in enumerate(printers, 1):
        print(f"[{i}] {p}")
    choice = input("Select printer number: ").strip()

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(printers):
            selected = printers[idx]
            subprocess.run(["sudo", "lpoptions", "-d", selected])
            print(f"[INFO] Default printer updated to: {selected}")
        else:
            print("[WARN] Invalid choice.")
    except ValueError:
        print("[WARN] Invalid input.")

def edit_quotas():
    try:
        with open(QUOTAS_FILE, "r") as f:
            quotas = json.load(f)
    except FileNotFoundError:
        quotas = {}

    print("\nCurrent quotas:")
    for user, remaining in quotas.items():
        print(f"- {user}: {remaining} pages")

    action = input("Do you want to (a)dd/update a user or (r)eset all? ").strip().lower()
    if action == "a":
        email = input("Enter user email: ").strip()
        amount = input("Enter new quota amount (integer): ").strip()
        try:
            quotas[email] = int(amount)
            print(f"[INFO] Set {email} quota to {amount}")
        except ValueError:
            print("[WARN] Invalid number.")
    elif action == "r":
        confirm = input("Are you sure you want to reset all quotas? (yes/no): ").strip().lower()
        if confirm == "yes":
            quotas = {}
            print("[INFO] All quotas reset.")

    with open(QUOTAS_FILE, "w") as f:
        json.dump(quotas, f, indent=2)

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
[6] Edit quotas
[7] Exit
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
            edit_quotas()
        elif choice == "7":
            break
        input("\n[ENTER] to continue…")

if __name__ == "__main__":
    menu()
