import sys
import config_secret
from datetime import datetime
from zoneinfo import ZoneInfo
from monitors import get_cpu_status, get_disk_status, get_mem_status

WEBHOOK_URL = config_secret.DISCORD_WEBHOOK
TIMESTAMP = datetime.now(ZoneInfo("America/Toronto")).strftime("%Y-%m-%d %H:%M:%S %Z")

def main():
    try:
        print("="*80)
        print("                         CPU MEMORY DISK STATUS                      ")
        print("="*80)
        get_cpu_status()
        print("")
        get_mem_status()
        print("")
        get_disk_status()
        print("")
    except Exception as e:
        print(f"An error occurred: {e}")
    print(f"Scan time: {TIMESTAMP}")
if __name__ == "__main__":
    main()