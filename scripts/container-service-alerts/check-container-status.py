#!/usr/bin/env python3
import docker
import sys
import json
import os
import config_secret
import requests
from colorama import Fore, Style, init
from datetime import datetime
from zoneinfo import ZoneInfo

init(autoreset=True)

WEBHOOK_URL = config_secret.DISCORD_WEBHOOK
STATE_FILE = os.path.join(os.path.dirname(__file__), ".container_state.json")
TIMESTAMP = datetime.now(ZoneInfo("America/Toronto")).strftime("%Y-%m-%d %H:%M:%S %Z")

def load_previous_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_current_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        print(f"Error saving state file: {e}")

def main():
    healthy_container_list = []
    bad_container_list = []
    current_state = {} 

    # CONNECT TO DOCKER DAEMON
    client = docker.from_env()
    all_containers = client.containers.list(all=True)

    for container in all_containers:
        container_name = container.name
        container_status = container.status
        
        # Populate the state dictionary for tracking
        current_state[container_name] = container_status
    
        if container_status == "running" or container_status == "healthy":
            healthy_container_list.append(container_name)
        else:
            bad_container_list.append(container_name)

    is_cron = "--cron" in sys.argv

    if not is_cron:
        print("\n########################################")
        print("            SCAN COMPLETE              ")
        print("########################################")

        col_width = 30
        print(f"{'CONTAINER NAME':<{col_width}} {'STATUS'}")
        print("-" * (col_width + 10))
        if healthy_container_list:
            for health_container in healthy_container_list:
                print(f"{health_container:<{col_width}} {Fore.GREEN}RUNNING{Style.RESET_ALL}")
        if bad_container_list:
            for bad_container in bad_container_list:
                print(f"{bad_container:<{col_width}} {Fore.RED}STOPPED{Style.RESET_ALL}")
        print("-" * (col_width + 10) + "\n")

        total_containers = len(healthy_container_list) + len(bad_container_list)
        print(f"Summary: {len(healthy_container_list)}/{total_containers} containers running")

        print(f"Scan time: {TIMESTAMP}")

    return healthy_container_list, bad_container_list, current_state

def discord_msg(healthy_container_list, bad_container_list, current_state):
    #Only send discord message with cron jobs
    is_cron = "--cron" in sys.argv
    if not is_cron:
        return

    #STATUSCAKE 5-MINUTE HEARTBEAT
    current_minute = datetime.now(ZoneInfo("America/Toronto")).minute
    if current_minute % 5 == 0:
        try:
            requests.get(config_secret.STATUSCAKE__PUSH_URL, timeout=5)
            print("5-Minute StatusCake Heartbeat ping sent successfully!")
        except Exception as e:
            print(f"Failed to send StatusCake heartbeat: {e}")

    previous_state = load_previous_state()
    
    newly_failed = []
    newly_recovered = []

    # 1. Check for new failures
    for container in bad_container_list:
        prev_status = previous_state.get(container, "running")
        if prev_status == "running" or prev_status == "healthy":
            newly_failed.append(container)

    # 2. Check for recoveries
    for container in healthy_container_list:
        prev_status = previous_state.get(container, "running")
        if prev_status not in ["running", "healthy"] and container in previous_state:
            newly_recovered.append(container)

    # Save the new state immediately for the next run
    save_current_state(current_state)

    payload_content = ""
    if newly_failed:
        payload_content += f"🚨 **ALERT** `{TIMESTAMP}`\nThe following containers have down on minos:\n"
        for container in newly_failed:
            payload_content += f"❌ `{container}` is down!\n"
            
    if newly_recovered:
        if payload_content: payload_content += "\n"
        payload_content += f"✅ **RECOVERY** `{TIMESTAMP}`\nThe following services are back online:\n"
        for container in newly_recovered:
            payload_content += f"🌱 `{container}` has recovered successfully.\n"

    if not payload_content:
        print("No changes detected. All containers healthy.")
        return
    
    try:
        response = requests.post(WEBHOOK_URL, json={"content": payload_content})
        if response.status_code == 204:
            print("State change notification sent to Discord!")
        else:
            print(f"Failed to send alert. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending webhook payload: {e}")

if __name__ == "__main__":
    healthy_list, bad_list, current_state_map = main()
    discord_msg(healthy_list, bad_list, current_state_map)