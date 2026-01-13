import subprocess
import csv
from datetime import datetime

# === Danh sách trích từ DETECTED (đã bỏ PID & loại trùng) ===
TARGET_PROCESSES = [
    "igfxCUIService.exe",
    "vmcompute.exe",
    "DongleService.exe",
    "GeoStartupAgentService.exe",
    "openvpnserv.exe",
    "pservice.exe",
    "vmware-authd.exe",
    "vmnetdhcp.exe",
    "vmware-usbarbitrator64.exe",
    "vmnat.exe",
    "parsecd.exe",
    "node.exe",
    "PresentationFontCache.exe",
    "Client.exe",
    "inspect_flash.exe",
]

def get_running_images():
    out = subprocess.check_output(
        ["tasklist", "/FO", "CSV"],
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    reader = csv.DictReader(out.splitlines())
    return {(row.get("Image Name") or "").strip() for row in reader}

def kill_by_image(name):
    # /IM để kill theo tên, /F để cưỡng bức, ẩn output cho gọn
    subprocess.call(
        ["taskkill", "/F", "/IM", name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def main():
    running = get_running_images()
    targets = [p for p in TARGET_PROCESSES if p in running]

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if targets:
        print(f"[{ts}] DETECTED: " + ", ".join(targets))
        for p in targets:
            kill_by_image(p)
        print(f"[{ts}] DONE: killed {len(targets)} process(es).")
    else:
        print(f"[{ts}] OK: no target process running.")

    # Giữ cửa sổ không tự tắt khi double-click
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
