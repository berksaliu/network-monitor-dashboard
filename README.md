# 📡 Enterprise ICMP Network Monitoring Dashboard

A lightweight, automated Network Operations Center (NOC) telemetry collector and web dashboard built using **Python, SQLite, Streamlit, and Plotly**. 

This system continuously polls target network nodes via ICMP echo requests, persists latency and uptime telemetry in an SQLite database, calculates real-time SLA availability percentages, and logs service outage incidents.

---

## 🛠️ Architecture & Telemetry Pipeline

```text
[ Target Endpoints ] ──(ICMP Ping / 30s)──> [ monitor.py (Daemon) ]
(Gateways, DNS, Web)                             │
                                                 ▼
[ Streamlit Web UI ] ◄──(SQL Queries)──── [ SQLite (monitoring.db) ]
(KPIs, Charts, Logs)
```

1. **Telemetry Collector (`monitor.py`):** Runs as a background service polling targets every 30 seconds. Extracts round-trip time (RTT) latency via regular expressions and logs host state (`ONLINE` / `OFFLINE`).
2. **Database Engine (`monitoring.db`):** Persists time-series records into a structured relational schema (`ping_log`).
3. **Operations Dashboard (`app.py`):** Renders dynamic KPI availability cards, Plotly time-series latency graphs, and an automated incident log.

---

## 📊 Telemetry Data & Outage Simulation Reports

### 1. Baseline Operational Telemetry (Normal State)
*Collected during standard network operating conditions across all target hosts.*

| Timestamp | Target Name | Target Host | Status | Latency (ms) |
| :--- | :--- | :--- | :--- | :--- |
| `2026-08-14 21:12:24` | Google Web | `google.com` | `ONLINE` | 35.0 |
| `2026-08-14 21:12:24` | Google DNS | `8.8.8.8` | `ONLINE` | 21.0 |
| `2026-08-14 21:12:24` | Cloudflare DNS | `1.1.1.1` | `ONLINE` | 28.0 |
| `2026-08-14 21:12:24` | Local Gateway | `192.168.0.1` | `ONLINE` | 1.0 |

---

### 2. Isolated Incident Log (Simulated Failure)
*Filtered query capturing simulated host reachability failure for target `192.0.2.1`.*

| Timestamp | Target Name | Target Host | Status | Action Taken |
| :--- | :--- | :--- | :--- | :--- |
| `2026-08-14 21:28:25` | Dead Gateway | `192.0.2.1` | `OFFLINE` | Incident Logged |
| `2026-08-14 21:27:54` | Dead Gateway | `192.0.2.1` | `OFFLINE` | Incident Logged |
| `2026-08-14 21:27:23` | Dead Gateway | `192.0.2.1` | `OFFLINE` | Incident Logged |

*Full markdown reports can be reviewed in the [`reports/`](./reports/) directory.*

---

## 🚀 How to Run Locally

### 1. Clone Repository & Setup Environment
```bash
git clone https://github.com/berksaliu/network-monitor-dashboard.git
cd network-monitor-dashboard
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start Telemetry Daemon (Terminal 1)
```bash
python monitor.py
```

### 3. Launch Dashboard UI (Terminal 2)
```bash
streamlit run app.py
```
*Navigate to `http://localhost:8501` in your browser.*

---

## 💻 Tech Stack & Requirements
* **Language:** Python 3.10+
* **Database:** SQLite3
* **Dashboard Framework:** Streamlit
* **Data & Analytics:** Pandas, Plotly Express
* **Protocols:** ICMP Echo (Layer 3)
