import psutil
import math
import config_secret
from colorama import Fore, Style

def get_mem_status():
    BAR_LENGTH = 30
    memory_b = psutil.virtual_memory()
    memory_total_gb = memory_b.total / 1024 ** 3
    memory_used_gb = memory_b.used / 1024 ** 3
    memory_free_gb = memory_b.free / 1024 ** 3
    used_memory_percentage = math.floor(memory_used_gb / memory_total_gb * 100)

    bar_filled_length = int((math.ceil(used_memory_percentage) / 100) * BAR_LENGTH)
    bar = "█" * bar_filled_length + " " * (BAR_LENGTH - bar_filled_length)

    color = Fore.RED if used_memory_percentage >= config_secret.MEMORY_WARNING_PERCENT else Fore.GREEN

    print("[MEMORY USAGE]")
    print(f"Total Memory: {memory_total_gb:5.1f} GB")
    print(f"Used Memory : {memory_used_gb:5.1f} GB")
    print(f"Free Memory : {memory_free_gb:5.1f} GB")
    print(f"[{bar}] {color}{math.ceil(used_memory_percentage):5.0f}% used{Style.RESET_ALL}")