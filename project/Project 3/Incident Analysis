"""
PROJECT 4 — Incident Analysis (Blue Team)

Simulates analysis of a cybersecurity incident using log data.
Identifies:
- What happened
- How it was detected
- What failed
- How it could be prevented

Author: Aaron Viegas
"""

import pandas as pd
from datetime import datetime

# -----------------------------
# STEP 1 — Load Incident Logs
# -----------------------------

def load_logs():
    """
    Simulated security event logs.
    In a real scenario, this would come from a SIEM or log file.
    """
    data = {
        "timestamp": [
            "2024-06-01 09:10",
            "2024-06-01 09:12",
            "2024-06-01 09:14",
            "2024-06-01 09:20",
            "2024-06-01 09:35",
        ],
        "event_type": [
            "Login Failure",
            "Login Failure",
            "Login Failure",
            "Login Success",
            "Data Exfiltration"
        ],
        "source_ip": [
            "185.220.101.5",
            "185.220.101.5",
            "185.220.101.5",
            "185.220.101.5",
            "185.220.101.5"
        ],
        "user": [
            "admin",
            "admin",
            "admin",
            "admin",
            "admin"
        ],
        "severity": [
            "Medium",
            "Medium",
            "Medium",
            "High",
            "Critical"
        ]
    }

    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


# -----------------------------
# STEP 2 — Analyze What Happened
# -----------------------------

def analyze_incident(df):
    """
    Determines the nature of the incident.
    """
    failed_logins = df[df["event_type"] == "Login Failure"]
    success_logins = df[df["event_type"] == "Login Success"]
    data_exfil = df[df["event_type"] == "Data Exfiltration"]

    incident_summary = {
        "failed_login_count": len(failed_logins),
        "successful_login": not success_logins.empty,
        "data_exfiltration": not data_exfil.empty,
        "attacker_ip": df["source_ip"].mode()[0],
        "target_user": df["user"].mode()[0],
    }

    return incident_summary


# -----------------------------
# STEP 3 — Detection Method
# -----------------------------

def detection_method(summary):
    """
    Determines how the incident was detected.
    """
    if summary["failed_login_count"] >= 3:
        return "Detected via brute-force login anomaly"
    elif summary["data_exfiltration"]:
        return "Detected via abnormal outbound data monitoring"
    else:
        return "Detected via standard log review"


# -----------------------------
# STEP 4 — Identify Failures
# -----------------------------

def identify_failures(summary):
    failures = []

    if summary["failed_login_count"] >= 3:
        failures.append("No account lockout policy")

    if summary["successful_login"]:
        failures.append("Weak authentication controls")

    if summary["data_exfiltration"]:
        failures.append("Lack of outbound traffic monitoring")

    return failures


# -----------------------------
# STEP 5 — Prevention Measures
# -----------------------------

def prevention_recommendations(failures):
    recommendations = []

    for failure in failures:
        if "lockout" in failure:
            recommendations.append("Implement account lockout after repeated failures")
        if "authentication" in failure:
            recommendations.append("Enforce multi-factor authentication (MFA)")
        if "traffic" in failure:
            recommendations.append("Deploy DLP and network monitoring tools")

    return recommendations


# -----------------------------
# STEP 6 — Generate Incident Report
# -----------------------------

def generate_report(df, summary, detection, failures, recommendations):
    print("\n🟦 INCIDENT ANALYSIS REPORT")
    print("=" * 40)

    print("\n📌 What Happened:")
    print(f"Repeated login failures followed by unauthorized access and data exfiltration.")
    print(f"Attacker IP: {summary['attacker_ip']}")
    print(f"Target Account: {summary['target_user']}")

    print("\n🔍 How Was It Detected:")
    print(detection)

    print("\n❌ What Failed:")
    for f in failures:
        print(f"- {f}")

    print("\n🛡️ How Could It Be Prevented:")
    for r in recommendations:
        print(f"- {r}")

    print("\n📊 Incident Timeline:")
    print(df[["timestamp", "event_type", "severity"]])


# -----------------------------
# MAIN EXECUTION
# -----------------------------

def main():
    logs = load_logs()
    summary = analyze_incident(logs)
    detection = detection_method(summary)
    failures = identify_failures(summary)
    recommendations = prevention_recommendations(failures)

    generate_report(
        logs,
        summary,
        detection,
        failures,
        recommendations
    )


if __name__ == "__main__":
    main()
