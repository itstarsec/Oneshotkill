import subprocess
import textwrap

# Pattern lọc service: dựa trên Name/DisplayName/PathName
# - GeoVision/Geo
# - GV-VMS
# - Executable thường gặp: GV*.exe, Gv*.exe, Geo*.exe
PS_STOP = r"""
$ErrorActionPreference = 'SilentlyContinue';

function Get-GVServices {
    Get-CimInstance Win32_Service | Where-Object {
        ($_.Name -match 'Geo|GV|VMS') -or
        ($_.DisplayName -match 'GeoVision|Geo\s*Vision|GV|VMS') -or
        ($_.PathName -match 'GeoVision|GV\-VMS|\\GV.*\.exe|\\Gv.*\.exe|\\Geo.*\.exe')
    } | Select-Object Name, DisplayName, State, StartMode, PathName
}

Write-Host "=== [1] Services matched for GeoVision/GV/VMS (before stop) ==="
$svcs = Get-GVServices | Sort-Object DisplayName
$svcs | Format-Table -AutoSize Name, State, StartMode, DisplayName

Write-Host "`n=== [2] Stopping matched services... ==="
# Stop theo Name (ServiceName), force
$svcs | ForEach-Object {
    try {
        Stop-Service -Name $_.Name -Force -ErrorAction SilentlyContinue
        Write-Host ("STOP -> " + $_.Name)
    } catch {
        Write-Host ("FAIL -> " + $_.Name)
    }
}

Start-Sleep -Seconds 5

Write-Host "`n=== [3] Verify remaining RUNNING services (after stop) ==="
$remain = Get-GVServices | Where-Object { $_.State -eq 'Running' } | Sort-Object DisplayName
if ($remain) {
    Write-Host "Still RUNNING:"
    $remain | Format-Table -AutoSize Name, State, StartMode, DisplayName
} else {
    Write-Host "OK: No matched services are running."
}

Write-Host "`n=== [4] Verify key GeoVision processes still running (GV/Geo executables) ==="
Get-Process -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^(GV|Gv|Geo)' -or $_.Name -match 'VMS' } |
    Select-Object Name, Id |
    Sort-Object Name |
    Format-Table -AutoSize
"""

def run_ps(ps_script: str):
    return subprocess.call(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script])

if __name__ == "__main__":
    print("Running GeoVision STOP (v2) ...")
    run_ps(PS_STOP)
    input("\nPress Enter to exit...")
