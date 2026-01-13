import subprocess
import time
import csv
from datetime import datetime

GV_VMS_PATH = r"C:\GV-VMS\GV-VMS.exe"

# Process “cốt lõi” theo phân tích của bạn
PROCESS_KILL_ORDER = [
    "GeoWebServer.exe",      # Access Control /servicemode (có thể tự sống)
    "GeoRSSManager.exe",     # RecordingServer module
    "GvMulticamMgr.exe",     # manager riêng
    "GeoLPR_DL_x64.exe",     # LPR module
    "GV-VMS.exe",            # ROOT ghi hình
]

# Service filter mạnh: Name/DisplayName/PathName
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

PS_LIST_PROCS = r"""
$ErrorActionPreference='SilentlyContinue';
Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^(GV|Gv|Geo)' -or $_.Name -match 'VMS'
} | Select-Object Name, ProcessId, ParentProcessId, ExecutablePath, CommandLine |
Sort-Object Name |
ConvertTo-Csv -NoTypeInformation
"""

def run_ps(script: str) -> str:
    p = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        text=True, encoding="utf-8", errors="ignore",
        capture_output=True
    )
    # Không fail cứng; trả stdout để parse, stderr chỉ để debug nếu cần
    return (p.stdout or "").strip()

def parse_csv(text: str):
    if not text:
        return []
    lines = text.splitlines()
    return list(csv.DictReader(lines))

def stop_services():
    csv_txt = run_ps(PS_LIST_SERVICES)
    svcs = parse_csv(csv_txt)

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Matched services: {len(svcs)}")
    for s in svcs:
        print(f"  - {s.get('Name')} | {s.get('State')} | {s.get('DisplayName')}")

    # Stop từng service theo Name
    for s in svcs:
        name = (s.get("Name") or "").strip()
        if not name:
            continue
        subprocess.call(
            ["powershell", "-NoProfile", "-Command", f"Stop-Service -Name '{name}' -Force -ErrorAction SilentlyContinue"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

def kill_process_by_name(img: str):
    subprocess.call(
        ["taskkill", "/F", "/IM", img],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def list_gv_processes():
    csv_txt = run_ps(PS_LIST_PROCS)
    return parse_csv(csv_txt)

def main():
    print("=== GeoVision STOP (services + processes) ===\n")

    # 1) Stop services (đúng chuẩn)
    print("[1] Stopping related services...")
    stop_services()

    print("[2] Waiting 3 seconds...")
    time.sleep(3)

    # 2) Verify process còn chạy
    remain = list_gv_processes()
    print(f"[3] Remaining GV/Geo/VMS processes: {len(remain)}")
    for p in remain:
        print(f"  - {p.get('Name')} (PID {p.get('ProcessId')}) Path={p.get('ExecutablePath')}")

    # 3) Kill theo thứ tự ưu tiên (đảm bảo GV-VMS tắt)
    print("[4] Terminating core processes (ordered)...")
    for img in PROCESS_KILL_ORDER:
        kill_process_by_name(img)
        time.sleep(0.2)

    # 4) Verify lần cuối
    time.sleep(2)
    remain2 = list_gv_processes()
    if remain2:
        print(f"[5] STILL RUNNING after kill: {len(remain2)}")
        for p in remain2:
            print(f"  - {p.get('Name')} (PID {p.get('ProcessId')})")
    else:
        print("[5] OK: No GV/Geo/VMS processes running.")

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
