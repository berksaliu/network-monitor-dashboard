import sqlite3
import subprocess
import time
import re
from datetime import datetime

#---------------------------------------------------------------------
# CONFIGURATION: Target Infrastructure
# In a real NOC environment, these represent gateways, core switches, internal DNS servers and external ISP edge routers
#---------------------------------------------------------------------

# Define the target infrastructure to monitor
TARGETS = [
    {"name": "Local Gateway", "host": "192.168.0.1"},
    {"name": "Cloudflare DNS", "host": "1.1.1.1"},
    {"name": "Google DNS", "host": "8.8.8.8"},
    {"name": "Google Web", "host": "google.com"},
    {"name": "Dead Gateway", "host": "192.0.2.1"}
]

DB_NAME = "monitoring.db"

def init_db():
    """
    Initialize the SQLite database and creates the relational table if it doesn't exist.

    Schema Design:
    - id: Autoincrementing primary key.
    - timestamp: ISO formatted date/time string of check.
    - target_name: Friendly display name.
    - target_host: Domain name or IPv4 address.
    - status: ONLINE or OFFLINE.
    - latency_ms: mRound-trip tie in milliseconds (Null if offline).
    """

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ping_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                target_name TEXT NOT NULL,
                target_host TEXT NOT NULL,
                status TEXT NOT NULL,
                latency_ms REAL
            )
        ''')
        conn.commit()

def ping_host(host):
    """
    Executes an OS ping command against the target host.
    Returns a tuple: (status: str, latency_ms: float or None)
    """
    try:
        # Windows Ping Flags:
        # '-n 1': Send exactly 1 ICMP Echo packet (fast evaluation).
        # '-w 1000': Set timeout to 1000 milliseconds (1 second) before giving up.
        cmd = ["ping", "-n", "1", "-w", "1000", host]

        # Execute command safely via subprocess and capture std output as string
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)

        # Regex pattern to locate latency value (e.g., "time=14ms" or "time=120ms")
        match = re.search(r'time[=<]([\d.]+)ms', output)

        if match:
            latency = float(match.group(1))
            return "ONLINE", latency
        elif "time<1ms" in output:
            # Local network responses under 1 millisecond
            return "ONLINE", 0.5
        else:
            return "OFFLINE", None

    except subprocess.CalledProcessError:
        # Host timed out or returned packet loss (Exit code non-zero)
        return "OFFLINE", None
    except Exception as e:
        # Catch unexpected OS or execution errors
        print(f"[ERROR] Internal execution error for {host}: {e}")
        return "OFFLINE", None

def run_check():
    """
    Performs one full sweep of all monitored targets and logs findings into SQLite.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n--- [Telemetry Sweep Executed: {timestamp}] ---")

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        for target in TARGETS:
            status, latency = ping_host(target["host"])

            # Insert metric record into database
            cursor.execute('''
                INSERT INTO ping_log (timestamp, target_name, target_host, status, latency_ms)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, target["name"], target["host"], status, latency))

            latency_str = f"{latency:.1f} ms" if latency is not None else "CRITICAL / TIMEOUT"
            print(f"[{status}] {target['name']} ({target['host']}) | Latency: {latency_str}")

            conn.commit()

if __name__ == "__main__":
    init_db()
    print("==========================================================")
    print("   NOC Network Telemetry & Metric Collector Engine        ")
    print("==========================================================")
    print(f"Monitoring {len(TARGETS)} targets every 30 seconds. Press Ctrl+C to exit.\n")

    try:
        while True:
            run_check()
            time.sleep(30)  # Wait for 30 seconds before the next sweep
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Collector service cleanly stopped by operator.")