import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import datetime

# ==========================
# CONFIGURATION
# ==========================
TARGET_URL = "http://localhost/dvwa/"  # Change to TryHackMe / HTB / DVWA URL
TIMEOUT = 5

# ==========================
# REPORT STORAGE
# ==========================
report = {
    "target": TARGET_URL,
    "date": str(datetime.date.today()),
    "findings": []
}

# ==========================
# HELPER FUNCTIONS
# ==========================
def add_finding(title, risk, description, recommendation):
    report["findings"].append({
        "title": title,
        "risk": risk,
        "description": description,
        "recommendation": recommendation
    })

# ==========================
# 1. RECONNAISSANCE
# ==========================
def reconnaissance():
    try:
        response = requests.get(TARGET_URL, timeout=TIMEOUT)
        headers = response.headers

        # Server information disclosure
        if "Server" in headers:
            add_finding(
                title="Server Header Disclosure",
                risk="Low",
                description=f"Server header reveals: {headers['Server']}",
                recommendation="Remove or obfuscate server headers to reduce information leakage."
            )

        # Missing security headers
        security_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Content-Security-Policy",
            "Strict-Transport-Security"
        ]

        for header in security_headers:
            if header not in headers:
                add_finding(
                    title=f"Missing Security Header: {header}",
                    risk="Medium",
                    description=f"{header} is not present in HTTP response.",
                    recommendation=f"Implement {header} to improve client-side protection."
                )

    except Exception as e:
        print(f"[!] Reconnaissance failed: {e}")

# ==========================
# 2. ROBOTS.TXT CHECK
# ==========================
def check_robots():
    try:
        robots_url = urljoin(TARGET_URL, "/robots.txt")
        response = requests.get(robots_url, timeout=TIMEOUT)

        if response.status_code == 200:
            add_finding(
                title="robots.txt Accessible",
                risk="Low",
                description="robots.txt file is publicly accessible and may reveal sensitive paths.",
                recommendation="Avoid listing sensitive directories in robots.txt."
            )
    except:
        pass

# ==========================
# 3. FORM DISCOVERY
# ==========================
def discover_forms():
    try:
        response = requests.get(TARGET_URL, timeout=TIMEOUT)
        soup = BeautifulSoup(response.text, "html.parser")
        forms = soup.find_all("form")

        if forms:
            add_finding(
                title="HTML Forms Detected",
                risk="Informational",
                description=f"{len(forms)} form(s) detected on the application.",
                recommendation="Ensure all form inputs are validated and sanitized server-side."
            )
    except:
        pass

# ==========================
# 4. HTTP METHOD CHECK
# ==========================
def check_http_methods():
    try:
        response = requests.options(TARGET_URL, timeout=TIMEOUT)
        methods = response.headers.get("Allow", "")

        if "PUT" in methods or "DELETE" in methods:
            add_finding(
                title="Dangerous HTTP Methods Enabled",
                risk="High",
                description=f"Potentially dangerous HTTP methods allowed: {methods}",
                recommendation="Disable unnecessary HTTP methods on the server."
            )
    except:
        pass

# ==========================
# REPORT OUTPUT
# ==========================
def generate_report():
    print("\n=== SECURITY ASSESSMENT REPORT ===")
    print(f"Target: {report['target']}")
    print(f"Date: {report['date']}")
    print("\nFindings:\n")

    if not report["findings"]:
        print("No findings detected.")
        return

    for idx, finding in enumerate(report["findings"], start=1):
        print(f"{idx}. {finding['title']}")
        print(f"   Risk Level: {finding['risk']}")
        print(f"   Description: {finding['description']}")
        print(f"   Recommendation: {finding['recommendation']}\n")

# ==========================
# MAIN EXECUTION
# ==========================
if __name__ == "__main__":
    print("[*] Starting security assessment...\n")

    reconnaissance()
    check_robots()
    discover_forms()
    check_http_methods()

    generate_report()
