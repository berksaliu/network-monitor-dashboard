import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NOC Network Monitor Dashboard",
    page_icon=":satellite:",
    layout="wide"
)

DB_NAME = "monitoring.db"

def load_data():
    """
    Queries SQLite database and loads the metric history into a Pandas DataFrame.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        query = "SELECT * FROM ping_log ORDER BY id DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

# ---------------------------------------------------------------------------
# UI HEADER & CONTROL SIDEBAR
# ---------------------------------------------------------------------------
st.title("Enterprise Network Operations Dashboard")
st.caption("Real-time ICMP availability polling, latency telemetry, and outage logs.")

st.sidebar.header("Dashboard Controls")
if st.sidebar.button("Refresh Data"):
    st.rerun()

df = load_data()

if df.empty:
    st.warning("Database is empty or missing! Ensure \"python monitor.py\" is running in your terminal.")
    st.stop()

# Sidebar Filter: Target Host
target_options = ["All Targets"] + list(df['target_name'].unique())
selected_target = st.sidebar.selectbox("Filter Target Host", target_options)

filtered_df = df if selected_target == "All Targets" else df[df['target_name'] == selected_target]

# ---------------------------------------------------------------------------
# LIVE STATUS KEY PERFORMANCE INDICATORS (KPIs)
# ---------------------------------------------------------------------------

st.subheader("Live Status Overview")

# Group by host name and take the latest status check
latest_status = df.groupby('target_name').first().reset_index()
cols = st.columns(len(latest_status))

for idx, row in latest_status.iterrows():
    with cols[idx]:
        target_name = row['target_name']
        host = row['target_host']
        status = row['status']
        latency = row['latency_ms']

        # Calculate host SLA uptime percentage across logged data
        host_data = df[df['target_name'] == target_name]
        total_checks = len(host_data)
        online_checks = len(host_data[host_data['status'] == 'ONLINE'])
        uptime_pct = (online_checks / total_checks * 100) if total_checks > 0 else 0.0

        if status == "ONLINE":
            st.metric(
                label = f"{target_name} ({host})",
                value = f"{latency:.1f} ms" if latency is not None else "Online",
                delta = f"{uptime_pct:.1f}% Uptime SLA"
            )
        else:
            st.metric(
                label = f"{target_name} ({host})",
                value = "OFFLINE",
                delta = f"{uptime_pct:.1f}% Uptime SLA",
                delta_color = "inverse"
            )

st.markdown("---")

# ---------------------------------------------------------------------------
# LATENCY PERFORMANCE TIME-SERIES CHART
# ---------------------------------------------------------------------------
st.subheader("Round-Trip Time (RTT) Latency Trends")

# Excludes offline records from line chart to prevent artificial zero-dips
online_metrics = filtered_df[filtered_df['status'] == 'ONLINE']

if not online_metrics.empty:
    fig = px.line(
        online_metrics,
        x = 'timestamp',
        y = 'latency_ms',
        color = 'target_name',
        title = "Latency (ms) over Time",
        labels = {'timestamp': 'Timestamp', 'latency_ms': 'Latency (ms)', 'target_name': 'Host'},
        markers = True
    )
    fig.update_layout(height = 400, hovermode = "x unified")
    st.plotly_chart(fig, use_container_width = True)

    # Summary statistics table
    st.markdown("#### Latency Statistics (Online Period)")
    stats_df = online_metrics.groupby('target_name')['latency_ms'].agg(['min', 'mean', 'max']).reset_index()
    stats_df.columns = ['Target Name', 'Min Latency (ms)', 'Average Latency (ms)', 'Max Latency (ms)']
    st.dataframe(stats_df, use_container_width=True)
else:
    st.info("No online data points recorded for plotting.")


st.markdown("---")

# ---------------------------------------------------------------------------
# INCIDENT LOG & TELEMETRY STREAM
# ---------------------------------------------------------------------------

col_outages, col_telemetry = st.columns(2)

with col_outages:
    st.subheader("Incident & Outage Log")
    outages = filtered_df[filtered_df['status'] == 'OFFLINE']
    if not outages.empty:
        st.error(f"Detected {len(outages)} outage event(s) in selected scope.")
        st.dataframe(outages[['timestamp', 'target_name', 'target_host', 'status']], use_container_width=True)
    else:
        st.success("Zero outages recorded. All service operational.")

with col_telemetry:
    st.subheader("Raw Telemetry Feed")
    st.dataframe(filtered_df[['timestamp', 'target_name', 'target_host', 'status', 'latency_ms']].head(15), use_container_width=True)