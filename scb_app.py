import streamlit as st
import pandas as pd
from ping3 import ping

# ------------------ DEVICE LIST ------------------
devices = [
    {"name": "PLC ITC-1", "ip": "10.22.250.1"},
    {"name": "CENTRAL INVERTER-1 (ITC-1)", "ip": "10.22.250.2"},
    {"name": "CENTRAL INVERTER-2 (ITC-1)", "ip": "10.22.250.3"},
    {"name": "PROT RELAY 33KV ICOG PANEL (ITC-1)", "ip": "10.22.250.6"},
    {"name": "MGW UPS (ITC-1)", "ip": "10.22.250.10"},
    # ... continue with all 250 entries
    {"name": "Magus-OPC Main #1", "ip": "10.22.250.250"},
    {"name": "Magus-OPC Backup #2", "ip": "10.22.250.253"}
]

# ------------------ STREAMLIT APP ------------------
st.set_page_config(page_title="IP Ping Monitor", layout="wide")

st.title("🌐 IP Ping Monitor")
st.write("Ping all devices in one click and see which are online/offline.")

if st.button("🚀 Ping All Devices"):
    results = []
    for d in devices:
        response = ping(d["ip"], timeout=1)
        status = "✅ Online" if response else "❌ Offline"
        results.append({"Device": d["name"], "IP": d["ip"], "Status": status})

    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True)

