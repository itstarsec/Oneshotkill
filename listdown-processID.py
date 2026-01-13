import subprocess
import time

print("Stopping GeoVision VMS services...")
subprocess.call([
    "powershell",
    "-Command",
    "Get-Service | Where-Object { $_.Name -match 'Geo|GV' } | Stop-Service -Force"
])

print("Waiting 60 seconds...")
time.sleep(60)

print("Starting GeoVision VMS services...")
subprocess.call([
    "powershell",
    "-Command",
    "Get-Service | Where-Object { $_.Name -match 'Geo|GV' } | Start-Service"
])

print("GeoVision VMS restart completed.")
input("Press Enter to exit...")
