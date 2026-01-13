import subprocess
import time
import csv
from datetime import datetime

GV_VMS_PATH = r"C:\GV-VMS\GV-VMS.exe"

PS_LIST_SERVICES = r"""
$ErrorActionPreference='SilentlyContinue';
Get-CimInstance Win32_Service | Where-Object {
    ($_.Name -match 'Geo|GV|VMS') -or
    ($_.DisplayName -match 'GeoVision|Geo\s*Vision|GV|VMS') -or
    ($_.PathName -match 'GeoVision|GV\-VMS|\\GV.*\.exe|\\Gv.*\.exe|\\Geo.*\.exe|C:\\GV\-VMS\\')
} | Select-Object Name, DisplayName, State, StartMode, PathName |
Sort-Object DisplayName |
ConvertTo-Csv -NoTypeInformation
"""

def run_ps(script: str) -> str:
    p = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        text=True, encoding="utf-8", errors="ignore",
        capture_output=True
    )
    return (p.stdout or "").strip()

def parse_csv(text: str):
    if not text:
        return []
    lines = text.splitlines()
    return list(csv.DictReader(lines))

def start_services():
    csv_txt = run_ps(PS_LIST_SERVICES)
    svcs = parse_csv(csv_txt)

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Matched services: {len(svcs)}")
    for s in svcs:
        print(f"  - {s.get('Name')} | {s.get('State')} | {s.get('DisplayName')}")

    for s in svcs:
        name = (s.get("Name") or "").strip()
        mode = (s.get("StartMode") or "").strip()
        if not name:
            continue
        if mode.lower() == "disabled":
            continue

        subprocess.call(
            ["powershell", "-NoProfile", "-Command", f"Start-Service -Name '{name}' -ErrorAction SilentlyContinue"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

def main():
    print("=== GeoVision START (services + GV-VMS) ===\n")

    # 1) Start services trước
    print("[1] Starting related services...")
    start_services()

    print("[2] Waiting 3 seconds...")
    time.sleep(3)

    # 2) Start GV-VMS.exe (root recording) nếu tồn tại
    print("[3] Starting GV-VMS root process...")
    subprocess.Popen([GV_VMS_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[4] DONE.")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
