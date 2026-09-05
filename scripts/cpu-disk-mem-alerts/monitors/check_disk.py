import psutil
import math
import os
import config_secret
from colorama import Fore, Style

def get_disk_status():

    base_dir = "/mnt"
    BAR_LENGTH = 50
    disk_data = {} # Our central dictionary

    # Gather all paths
    mount_paths = [
        os.path.join(base_dir, name) 
        for name in os.listdir(base_dir) 
        if os.path.ismount(os.path.join(base_dir, name))
    ]

    # Populate the dictionary
    for path in mount_paths:
        drive_name = os.path.basename(path)
        used_percent = psutil.disk_usage(path).percent
        rounded_used_percentage = math.ceil(used_percent)
        
        # Calculate bar length
        bar_length = int((rounded_used_percentage / 100) * BAR_LENGTH)
        if rounded_used_percentage > 0 and bar_length == 0:
            bar_length = 1

        # Store everything in a dictionary
        disk_data[drive_name] = {
            "percent": rounded_used_percentage,
            "bar_length": bar_length,
            "path": path
        }
    print("[DISK USAGE]\n")
    color = Fore.RED if rounded_used_percentage >= config_secret.MEMORY_WARNING_PERCENT else Fore.GREEN
    
    for drive, stats in disk_data.items():
        bar = "█" * stats["bar_length"] + " " * (BAR_LENGTH - stats["bar_length"])
        print(f"{drive:<15} [{bar}] {color}{stats['percent']}% used{Style.RESET_ALL}")
