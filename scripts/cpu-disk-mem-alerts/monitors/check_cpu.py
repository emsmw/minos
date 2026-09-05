import psutil
from colorama import Fore, Style
import config_secret

def get_cpu_status():
    # Capture percentages as raw floats
    percentages = psutil.cpu_percent(interval=1, percpu=True)
    num_cores = len(percentages)
    half = num_cores // 2
    BAR_LENGTH = 20 
    
    print("[CPU USAGE PER CORE]")
    for i in range(half):
        # Left Column calculation (using raw float)
        used_percentage_left = percentages[i]
        filled_left = int((used_percentage_left / 100) * BAR_LENGTH)
        # Ensure a tiny sliver shows if usage is > 0% but less than 1 bar block
        if used_percentage_left > 0 and filled_left == 0:
            filled_left = 1
        bar_left = "█" * filled_left + " " * (BAR_LENGTH - filled_left)
        color_left = Fore.RED if used_percentage_left >= config_secret.CPU_WARNING_PERCENT else Fore.GREEN
        
        # Right Column calculation
        used_percentage_right = percentages[i + half]
        filled_right = int((used_percentage_right / 100) * BAR_LENGTH)
        if used_percentage_right > 0 and filled_right == 0:
            filled_right = 1
        bar_right = "█" * filled_right + " " * (BAR_LENGTH - filled_right)
        color_right = Fore.RED if used_percentage_left >= config_secret.MEMORY_WARNING_PERCENT else Fore.GREEN

        # Print using :>5.1f to handle the decimals and keep columns aligned
        print(
                    f" Core {i+1:>2} [{bar_left}] {color_left}{used_percentage_left:>5.1f}%{Style.RESET_ALL} | "
                    f"Core {i+half+1:>2} [{bar_right}] {color_right}{used_percentage_right:>5.1f}%{Style.RESET_ALL}"
                )