# ================================
# Security Log File Analyzer
# Author: Aaron Viegas
# Purpose: Analyze security logs to identify suspicious activity
# ================================

from collections import defaultdict
from datetime import datetime

# -------------------------------
# Configuration
# -------------------------------

LOG_FILE = "sample_logs.txt"
FAILED_LOGIN_THRESHOLD = 5

# -------------------------------
# Data Structures
# -------------------------------

failed_logins = defaultdict(int)
event_counts = defaultdict(int)
suspicious_ips = set()

# -------------------------------
# Helper Functions
# -------------------------------

def parse_log_line(line):
    """
    Expected log format:
    [YYYY-MM-DD HH:MM:SS] IP_ADDRESS EVENT_TYPE
    Example:
    [2025-01-10 12:45:23] 192.168.1.10 FAILED_LOGIN
    """
    try:
        timestamp_part, ip, event = line.strip().split("] ")
        timestamp = timestamp_part.replace("[", "")
        return timestamp, ip, event
    except ValueError:
        return None, None, None


def assess_risk(ip):
    """
    Simple risk scoring logic
    """
    if failed_logins[ip] >= FAILED_LOGIN_THRESHOLD:
        return "HIGH"
    elif failed_logins[ip] >= 3:
        return "MEDIUM"
    else:
        return "LOW"


# -------------------------------
# Main Analysis Logic
# -------------------------------

def analyze_logs():
    with open(LOG_FILE, "r") as file:
        for line in file:
            timestamp, ip, event = parse_log_line(line)

            if not ip:
                continue

            event_counts[ip] += 1

            if event == "FAILED_LOGIN":
                failed_logins[ip] += 1

                if failed_logins[ip] >= FAILED_LOGIN_THRESHOLD:
                    suspicious_ips.add(ip)


# -------------------------------
# Reporting
# -------------------------------

def generate_report():
    print("\n=== SECURITY LOG ANALYSIS REPORT ===\n")

    for ip in event_counts:
        risk = assess_risk(ip)
        print(f"IP Address: {ip}")
        print(f"  Total Events: {event_counts[ip]}")
        print(f"  Failed Logins: {failed_logins[ip]}")
        print(f"  Risk Level: {risk}")
        print("-" * 40)

    print("\n=== SUSPICIOUS IP ADDRESSES ===")
    for ip in suspicious_ips:
        print(f"⚠ {ip} (Possible brute-force activity)")


# -------------------------------
# Entry Point
# -------------------------------

if __name__ == "__main__":
    analyze_logs()
    generate_report()
