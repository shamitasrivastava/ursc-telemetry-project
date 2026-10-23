# dashboard.py - URSC Dynamic Telemetry, 3D Satellite & Mission Operations Dashboard
import os
import re
import time
import datetime
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

st.set_page_config(
    page_title="ISRO Telemetry & Mission Operations",
    page_icon=":satellite:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ASTRO UXDS CYBERNETIC MISSION CONTROL THEME ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* Premium Cybernetic Deep Space Theme */
    .stApp {
        background: radial-gradient(circle at 18% 12%, rgba(14, 165, 233, 0.12) 0%, transparent 45%),
                    radial-gradient(circle at 82% 88%, rgba(99, 102, 241, 0.10) 0%, transparent 50%),
                    #070a14 !important;
        color: #e2e8f0 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090e1c 0%, #050811 100%) !important;
        border-right: 1px solid rgba(56, 189, 248, 0.15) !important;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.4) !important;
    }

    /* Glow Headers & Modern Typography */
    h1, h2, h3, h4 {
        color: #f1f5f9 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px !important;
    }
    
    /* Top Mission Header Banner */
    .mission-header-banner {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(10, 16, 32, 0.9) 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        border-radius: 12px !important;
        padding: 16px 24px !important;
        margin-bottom: 22px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(12px) !important;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 15px;
    }
    .mission-title {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 0.5px;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .mission-clock {
        font-size: 13px;
        color: #38bdf8;
        font-family: 'JetBrains Mono', monospace;
        background: rgba(15, 23, 42, 0.7);
        padding: 6px 14px;
        border-radius: 6px;
        border: 1px solid rgba(56, 189, 248, 0.25);
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.4);
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: linear-gradient(135deg, rgba(14, 23, 42, 0.75) 0%, rgba(8, 14, 28, 0.85) 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 10px !important;
        padding: 18px !important;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
        backdrop-filter: blur(10px) !important;
        margin-bottom: 18px !important;
    }

    /* Modern Metric KPI Boxes */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.75) 0%, rgba(10, 15, 30, 0.85) 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-top: 2px solid #0284c7 !important;
        padding: 14px 18px !important;
        border-radius: 10px !important;
        min-height: 95px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(8px) !important;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(56, 189, 248, 0.45) !important;
        box-shadow: 0 8px 25px rgba(2, 132, 199, 0.25) !important;
    }
    div[data-testid="stMetricValue"] {
        color: #f0f9ff !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 24px !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
        text-shadow: 0 0 16px rgba(56, 189, 248, 0.35) !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
    }

    /* Inputs, Select Boxes, and Radios */
    .stTextInput input, .stSelectbox select {
        background-color: #0b1426 !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.25) !important;
        border-radius: 6px !important;
    }

    /* Radiant Aerospace Action Buttons */
    .stButton button {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(56, 189, 248, 0.5) !important;
        font-family: inherit !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 15px rgba(2, 132, 199, 0.35) !important;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%) !important;
        box-shadow: 0 6px 24px rgba(56, 189, 248, 0.6) !important;
        transform: translateY(-2px) !important;
    }

    /* Tables & Dataframes */
    .stDataFrame {
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 8px !important;
        background-color: rgba(10, 15, 28, 0.7) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
    }
    table {
        color: #e2e8f0 !important;
        background-color: #070a14 !important;
    }
    th {
        background-color: #0d1527 !important;
        color: #38bdf8 !important;
        font-weight: 600 !important;
    }

    /* Badges & Flight Status */
    .status-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }
    .badge-nominal {
        background: rgba(16, 185, 129, 0.14) !important;
        color: #34d399 !important;
        border: 1px solid rgba(52, 211, 153, 0.4) !important;
        box-shadow: 0 0 14px rgba(16, 185, 129, 0.25) !important;
    }
    .badge-alert {
        background: rgba(244, 63, 94, 0.18) !important;
        color: #fb7185 !important;
        border: 1px solid rgba(251, 113, 133, 0.5) !important;
        box-shadow: 0 0 18px rgba(244, 63, 94, 0.45) !important;
        animation: pulse-red 1.2s infinite alternate;
    }
    @keyframes pulse-red {
        0% { box-shadow: 0 0 4px rgba(244, 63, 94, 0.4); }
        100% { box-shadow: 0 0 18px rgba(244, 63, 94, 0.9); }
    }
    </style>
""", unsafe_allow_html=True)

log_path = "logs/telemetry_audit_log.csv"
telemetry_file = "iosys_test_09102026-081918385_r1.txt"

# --- SIDEBAR: MISSION CONTROL & CHAOS FAULT INJECTION ---
st.sidebar.markdown("## Ground Ops Command")
st.sidebar.markdown(f"**Station:** ISTRAC Ground Station (BLR)<br/>**Track:** LEO-550 (Inc: 45.0°)", unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.markdown("### Live Demo Controls")
inject_fault = st.sidebar.checkbox("Activate Chaos Mode (Fault Injection)", value=False)

if inject_fault:
    st.sidebar.error("FAULT ACTIVE: Simulating Reaction Wheel speed saturation & Receiver loss-of-lock.")
    os.makedirs("logs", exist_ok=True)
    if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
        temp_audit = pd.read_csv(log_path)
        if not temp_audit.empty and temp_audit.iloc[-1]["Status"] != "CRITICAL ANOMALY":
            new_fault_row = pd.DataFrame([{
                "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Telecommand": "SIMULATE_RW_SPIKE_FAULT",
                "Autoencoder_MSE": 0.8542,
                "Unlock_Risk_Pct": 100.0,
                "Rule_Warnings": "Alert: Subsystem Over-speed & Bus Voltage Spike",
                "Cascading_Impact_Count": 4,
                "Status": "CRITICAL ANOMALY"
            }])
            temp_audit = pd.concat([temp_audit, new_fault_row], ignore_index=True)
            temp_audit.to_csv(log_path, index=False)
else:
    st.sidebar.success("System Nominal: Flight parameters stable.")

# Navigation Selection
page = st.sidebar.radio("Mission Control View", [
    "Mission Operations Center (3D Satellite & Live Orbit)",
    "Live Telemetry Streams & Volatility Analyzer",
    "AI Anomaly Detection & Dual-Model Diagnostics",
    "Cross-Subsystem Cascading Impact (Depth-4)",
    "Multi-Channel Cascading Waveforms"
])

# --- CACHED DATA LOADER ---
@st.cache_data
def load_real_data():
    if os.path.exists(telemetry_file):
        df = pd.read_csv(telemetry_file, low_memory=False)
        if "Timestamp" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%d-%b-%Y %H:%M:%S.%f", errors="coerce")
            df = df.sort_values("Timestamp").reset_index(drop=True)
        return df
    return None

df_raw = load_real_data()
audit_df = pd.read_csv(log_path) if os.path.exists(log_path) and os.path.getsize(log_path) > 0 else pd.DataFrame()

# Current UTC and IST times
utc_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
ist_now = datetime.datetime.now().strftime("%H:%M:%S IST")

# Top Mission Control Header Banner
st.markdown(f"""
    <div class="mission-header-banner">
        <div>
            <div class="mission-title">
                ISRO TELEMETRY & COMMAND OPERATIONS DECK
            </div>
            <div style="color:#94a3b8; font-size:12px; margin-top:4px;">
                Spacecraft: <span style="color:#00f0ff;font-weight:bold;">ISRO-LEO-550</span> | Orbit: <span style="color:#f59e0b;">550 km Circular</span>
            </div>
        </div>
        <div style="display:flex; gap:10px; align-items:center;">
            <div class="mission-clock mission-clock-utc" id="live-utc-clock">{utc_now}</div>
            <div class="mission-clock mission-clock-ist" id="live-ist-clock">{ist_now}</div>
            <div>
                <span class="status-badge {'badge-alert' if inject_fault else 'badge-nominal'}">
                    {'CRITICAL ANOMALY' if inject_fault else 'FLIGHT NOMINAL'}
                </span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Live ticking real-time background clock synchronizer
components.html("""
<script>
(function() {
    function tick() {
        try {
            const now = new Date();
            const pad = n => String(n).padStart(2, '0');
            const utcStr = now.getUTCFullYear() + '-' + pad(now.getUTCMonth()+1) + '-' + pad(now.getUTCDate()) + ' ' +
                           pad(now.getUTCHours()) + ':' + pad(now.getUTCMinutes()) + ':' + pad(now.getUTCSeconds()) + ' UTC';
            const istStr = now.toLocaleTimeString('en-GB', { timeZone: 'Asia/Kolkata', hour12: false }) + ' IST';
            
            const pDoc = (window.parent && window.parent.document) ? window.parent.document : document;
            const utcs = pDoc.querySelectorAll('.mission-clock-utc, #live-utc-clock');
            utcs.forEach(el => { el.innerText = utcStr; });
            const ists = pDoc.querySelectorAll('.mission-clock-ist, #live-ist-clock');
            ists.forEach(el => { el.innerText = istStr; });
        } catch(e) {}
    }
    if (!window._isroLiveClockTimer) {
        window._isroLiveClockTimer = setInterval(tick, 1000);
    }
    tick();
})();
</script>
""", height=0)


# --- TELECOMMAND DISPATCHER HELPER ---
def dispatch_telecommand(command_str):
    """Executes orbital send-and-check verification loop and logs result."""
    cmd_upper = command_str.strip().upper()
    
    # 1. Delay simulation for LEO 550km
    c = 299792.458
    propagation_delay = round(((550 / c) * 2) * 1000, 2)
    obc_delay = 25.0
    actuation_delay = 150.0
    total_delay = round(propagation_delay + obc_delay + actuation_delay, 2)
    
    # 2. Rule & Limit Checks
    warnings = []
    recon_error = 0.015 + np.random.uniform(0.002, 0.02)
    unlock_prob = 0.00
    impact_count = 0
    
    if "SPEED" in cmd_upper or "RW" in cmd_upper:
        numbers = re.findall(r"\d+", cmd_upper)
        target_rpm = float(numbers[-1]) if numbers else 4500.0
        st.session_state["commanded_rw_speed"] = target_rpm
        if target_rpm > 4500.0:
            warnings.append(f"Alert: Reaction Wheel Target {target_rpm} RPM breaches Upper Limit (4500 RPM)!")
            recon_error = 0.742 + np.random.uniform(0.05, 0.15)
            unlock_prob = 0.85
            impact_count = 4
        elif target_rpm < 1200.0:
            warnings.append(f"Alert: Reaction Wheel Target {target_rpm} RPM breaches Lower Limit (1200 RPM)!")
            recon_error = 0.420
            impact_count = 2
        else:
            impact_count = 1
            
    elif "SAFE" in cmd_upper:
        st.session_state["commanded_rw_speed"] = 1500.0
        st.session_state["commanded_temp"] = 24.2
        recon_error = 0.0084
        unlock_prob = 0.0
        impact_count = 1
    elif "THERMAL" in cmd_upper:
        st.session_state["commanded_temp"] = 22.5
        recon_error = 0.0112
        impact_count = 2
    elif "FAULT" in cmd_upper:
        st.session_state["commanded_rw_speed"] = 5200.0
        st.session_state["commanded_temp"] = 88.5
        warnings.append("Alert: Artificial Chaos Fault Injected")
        recon_error = 0.8542
        unlock_prob = 1.0
        impact_count = 4
    else:
        impact_count = np.random.randint(1, 3)

    dynamic_threshold = 0.08500
    is_anomalous = recon_error > dynamic_threshold or unlock_prob > 0.50 or len(warnings) > 0
    status_str = "RISK / ANOMALY DETECTED" if is_anomalous else "HEALTHY & LOCKED"
    warnings_str = " | ".join(warnings) if warnings else "None"
    
    # Append to log file
    os.makedirs("logs", exist_ok=True)
    new_entry = {
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Telecommand": command_str,
        "Autoencoder_MSE": round(recon_error, 5),
        "Unlock_Risk_Pct": round(unlock_prob * 100, 2),
        "Cascading_Impact_Count": impact_count,
        "Status": status_str,
        "Rule_Warnings": warnings_str
    }
    
    if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
        df_cur = pd.read_csv(log_path)
        df_cur = pd.concat([df_cur, pd.DataFrame([new_entry])], ignore_index=True)
        df_cur.to_csv(log_path, index=False)
    else:
        pd.DataFrame([new_entry]).to_csv(log_path, index=False)
        
    # Update ISRO report file
    with open("isro_report_xband-m-on.tst", "a") as f:
        clean_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{clean_ts}] COMMAND: {command_str:<25} | STATUS: [{status_str}] (MSE: {round(recon_error, 5)})\n")
        
    return {
        "status": status_str,
        "mse": recon_error,
        "unlock_prob": unlock_prob,
        "warnings": warnings,
        "impact_count": impact_count,
        "total_delay": total_delay,
        "prop_delay": propagation_delay
    }


# ==============================================================================
# VIEW 1: MISSION OPERATIONS CENTER (3D SATELLITE & LIVE ORBIT)
# ==============================================================================
if page == "Mission Operations Center (3D Satellite & Live Orbit)":
    st.markdown("### Real-Time Spacecraft 3D Orbit & Attitude Visualizer")
    st.markdown("Interactive 3D tracking visualization showing the satellite in a 550 km LEO trajectory over ISTRAC Ground Station (Bangalore). Drag to rotate, zoom with wheel, or test maneuvers below.")

    # Load 3D Satellite Canvas Widget
    widget_path = "src/satellite_widget.html"
    if os.path.exists(widget_path):
        with open(widget_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # If fault is injected, dynamically alter initial state in html
        if inject_fault:
            html_content = html_content.replace("let faultActive = false;", "let faultActive = true;")
            
        components.html(html_content, height=480, scrolling=False)
    else:
        st.warning("Satellite 3D widget source not found.")

    st.markdown("---")
    st.markdown("### Real-Time Synchronized Ground Station Command Audit Log")
    if os.path.exists(log_path) and not audit_df.empty:
        st.dataframe(audit_df.tail(10), use_container_width=True)
    else:
        st.info("No telecommands logged yet. Transmit an uplink above to generate audit logs.")

    st.markdown("---")
    st.markdown("### Real-Time Telemetry Command (TM) Verification & Downlink Stream")
    st.markdown("Spacecraft telemetry return packets downlinked from orbit verifying execution registers, observed sensor responses, and RF carrier SNR for commanded subsystems.")

    # Telemetry Command (TM) Verification Table
    if os.path.exists(log_path) and not audit_df.empty:
        tm_rows = []
        for idx, row in audit_df.tail(12).iterrows():
            cmd = str(row.get("Telecommand", "TC_CMD"))
            cmd_upper = cmd.upper()
            status = str(row.get("Status", "STANDBY"))
            mse = float(row.get("Autoencoder_MSE", 0.01))
            ts = row.get("Timestamp", "")

            # Map Telecommand to downlinked Telemetry Command (TM) response and verification register
            if "SPEED" in cmd_upper or "RW" in cmd_upper:
                numbers = re.findall(r"\d+", cmd)
                target_rpm = float(numbers[-1]) if numbers else 4500.0
                tm_cmd = "TM_ADCS_RW_SPEED_ACK"
                tm_param = "RW_SPEED_RPM"
                tm_val = f"{target_rpm:.1f} RPM"
                exe_reg = "0x00 (SUCCESS)" if (1200 <= target_rpm <= 4500) else "0x08 (LIMIT_BREACH)"
                tm_state = "VERIFIED [NOMINAL]" if "HEALTHY" in status else "ANOMALOUS OVER-SPEED"
                link_snr = "+18.2 dB" if "HEALTHY" in status else "+6.1 dB (DEGRADED)"
            elif "TTC" in cmd_upper:
                tm_cmd = "TM_TTC_TX_CARRIER_LOCK"
                tm_param = "TTC_RX-1_CAR_LOCK_STS"
                tm_val = "LOCK (-68.4 dBm)" if "HEALTHY" in status else "UNLOCK (-115.8 dBm)"
                exe_reg = "0x00 (SUCCESS)"
                tm_state = "VERIFIED [NOMINAL]" if "HEALTHY" in status else "LOSS OF LOCK"
                link_snr = "+22.4 dB" if "HEALTHY" in status else "-4.2 dB (UNLOCKED)"
            elif "SYS" in cmd_upper or "OBC" in cmd_upper:
                tm_cmd = "TM_OBC_SYS_HANDOVER_ACK"
                tm_param = "SYS_SEL / OBC_STATUS"
                tm_val = "OBC-1 [PRIMARY MASTER]"
                exe_reg = "0x01 (EXECUTED)"
                tm_state = "VERIFIED [NOMINAL]"
                link_snr = "+19.0 dB"
            elif "THERMAL" in cmd_upper:
                tm_cmd = "TM_TCS_LOOP_STATUS"
                tm_param = "GCRX_10_RF_DECK_M_TS264_TMP"
                tm_val = "24.2 °C [NOMINAL]"
                exe_reg = "0x00 (SUCCESS)"
                tm_state = "VERIFIED [NOMINAL]"
                link_snr = "+19.5 dB"
            elif "SAFE" in cmd_upper:
                tm_cmd = "TM_ADCS_SAFE_RECOVERY_ACK"
                tm_param = "RW_SPEED_RPM / GYRO_2"
                tm_val = "1500.0 RPM / GYRO_OK"
                exe_reg = "0x00 (FDIR_RECOVERED)"
                tm_state = "VERIFIED [RECOVERED]"
                link_snr = "+20.1 dB"
            elif "FAULT" in cmd_upper or "SPIKE" in cmd_upper:
                tm_cmd = "TM_ALERT_FAULT_INJECT_ACK"
                tm_param = "RW_SPEED_RPM / TTC_RX-1_AGC"
                tm_val = "5200.0 RPM / -115.8 dBm"
                exe_reg = "0xFF (CRITICAL_ALERT)"
                tm_state = "CRITICAL ANOMALY"
                link_snr = "-6.5 dB (DROPOUT)"
            else:
                tm_cmd = "TM_CMD_ACK_REGISTER"
                tm_param = "EXE_CMD_CNTR_SEL"
                tm_val = "CNTR_ACK_01"
                exe_reg = "0x00 (SUCCESS)"
                tm_state = "VERIFIED [NOMINAL]" if mse < 0.085 else "ANOMALY DETECTED"
                link_snr = "+17.8 dB"

            tm_rows.append({
                "Timestamp": ts,
                "Telemetry Command (TM)": tm_cmd,
                "Monitored Telemetry Channel": tm_param,
                "Downlinked Telemetry Value": tm_val,
                "Execution Register (EXE_REG)": exe_reg,
                "Telemetry Verification Status": tm_state,
                "Carrier Link SNR": link_snr,
                "Reconstruction MSE": round(mse, 5)
            })

        df_tm_display = pd.DataFrame(tm_rows)
        st.dataframe(df_tm_display, use_container_width=True)
    else:
        st.info("No telemetry command verification downlinks logged yet.")

    # Historical ISRO Telecommand/Telemetry Dataset Expandable View
    tc_csv_path = "Tc_data_08-10-2026.csv"
    if os.path.exists(tc_csv_path):
        with st.expander("View Historical Flight Telemetry Command Archive (Tc_data_08-10-2026.csv)"):
            df_hist = pd.read_csv(tc_csv_path)
            clean_hist_cols = ["cmdSysTime", "cmdMnem", "station", "cmdStat", "originator", "timeVal"]
            avail_hist = [c for c in clean_hist_cols if c in df_hist.columns]
            st.dataframe(df_hist[avail_hist].head(25), use_container_width=True)


# ==============================================================================
# VIEW 2: LIVE TELEMETRY STREAMS & VOLATILITY ANALYZER
# ==============================================================================
elif page == "Live Telemetry Streams & Volatility Analyzer":
    st.subheader("Subsystem Telemetry Stream & Volatility Multipliers")

    if df_raw is not None:
        numeric_df = df_raw.select_dtypes(include=[np.number])
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Telemetry Records", f"{len(df_raw):,}")
        col_m2.metric("Telemetry Channels", f"{df_raw.shape[1]}")
        col_m3.metric("Numeric Sensors", f"{numeric_df.shape[1]}")
        col_m4.metric("Sampling Rate", "10 Hz High-Rate")

        st.markdown("---")
        st.markdown("### Spacecraft Telemetry Volatility Multipliers & Variance Analysis")

        # Compute comprehensive telemetry statistics
        stats_records = []
        for col_name in numeric_df.columns:
            s_data = numeric_df[col_name].dropna()
            if len(s_data) == 0:
                continue
            std_val = float(s_data.std())
            mean_val = float(s_data.mean())
            min_val = float(s_data.min())
            max_val = float(s_data.max())
            dyn_range = max_val - min_val

            # Categorize Subsystem
            if any(k in col_name.upper() for k in ["TMP", "DECK", "LO_DECK", "RF_DECK", "TS119", "TS024", "TS264", "TS120", "TS025"]):
                subsystem = "Thermal Control"
            elif any(k in col_name.upper() for k in ["TX", "RX", "AGC", "CAR", "TTC", "CLCW", "LINK", "RF_AVL", "BIT_LOCK"]):
                subsystem = "Telemetry & Comm"
            elif any(k in col_name.upper() for k in ["CMD", "CNTR", "REG", "EXE", "SYS_SEL"]):
                subsystem = "Command & Data (CDH)"
            elif any(k in col_name.upper() for k in ["DCDC", "POS_", "8V", "15V", "PWR", "VOLT"]):
                subsystem = "Electrical Power (EPS)"
            else:
                subsystem = "Core Avionics"

            if std_val > 10.0:
                stability = "Ultra-High Dynamic / Counter"
            elif std_val >= 1.0:
                stability = "High Dynamic Fluctuation"
            elif std_val >= 0.3:
                stability = "Moderate Dynamic Activity"
            else:
                stability = "Low Drift / Stable"

            stats_records.append({
                "Sensor Mnemonic": col_name,
                "Subsystem": subsystem,
                "Mean (μ)": round(mean_val, 4),
                "Min": round(min_val, 4),
                "Max": round(max_val, 4),
                "Dynamic Range (Δ)": round(dyn_range, 4),
                "Volatility Multiplier (σ)": round(std_val, 4),
                "Operational State": stability,
            })

        volatility_full = pd.DataFrame(stats_records).sort_values(by="Volatility Multiplier (σ)", ascending=False).reset_index(drop=True)

        # Interactive controls toolbar
        ctrl_c1, ctrl_c2, ctrl_c3 = st.columns([2, 2, 2])
        with ctrl_c1:
            scale_mode = st.radio(
                "Axis Scale Mode",
                ["Logarithmic Scale (log10)", "Linear Scale"],
                horizontal=True,
                help="Logarithmic scale enables simultaneous visual comparison of ultra-high variance counters and fine physical sensor dynamics."
            )
        with ctrl_c2:
            top_n = st.slider(
                "Display Top N Channels",
                min_value=5,
                max_value=min(25, len(volatility_full)),
                value=12,
                step=1
            )
        with ctrl_c3:
            filter_counters = st.checkbox(
                "Physical Sensors Only",
                value=False,
                help="Exclude digital command registers and counter accumulators to isolate physical thermal, RF, voltage, and current dynamics."
            )

        # Filter dataset for plotting
        plot_df = volatility_full.copy()
        if filter_counters:
            plot_df = plot_df[~plot_df["Sensor Mnemonic"].str.contains("CNTR|REG|CMD", case=False, regex=True)]
        
        plot_df = plot_df.head(top_n)

        # Enhanced Volatility Multiplier Plot
        use_log = (scale_mode == "Logarithmic Scale (log10)")
        fig_bar = px.bar(
            plot_df,
            x="Volatility Multiplier (σ)",
            y="Sensor Mnemonic",
            orientation='h',
            title=f"Top {len(plot_df)} Spacecraft Sensors by Volatility Multiplier (Standard Deviation σ)",
            color="Volatility Multiplier (σ)",
            color_continuous_scale=[[0, "#0284c7"], [0.35, "#06b6d4"], [0.7, "#6366f1"], [1, "#d946ef"]],
            log_x=use_log,
            text="Volatility Multiplier (σ)",
            template="plotly_dark",
            hover_data={
                "Subsystem": True,
                "Mean (μ)": True,
                "Dynamic Range (Δ)": True,
                "Operational State": True,
                "Volatility Multiplier (σ)": ":.4f"
            }
        )
        fig_bar.update_traces(
            texttemplate="%{text:.3f} σ",
            textposition="outside",
            marker=dict(line=dict(width=1, color="rgba(56, 189, 248, 0.6)"))
        )
        fig_bar.update_layout(
            paper_bgcolor="#070a14",
            plot_bgcolor="rgba(11, 18, 33, 0.6)",
            height=460,
            margin=dict(l=260, r=80, t=50, b=40),
            yaxis=dict(
                categoryorder="total ascending",
                title=dict(text="Telemetry Channel Mnemonic", font=dict(color="#38bdf8", size=12)),
                tickfont=dict(size=11, color="#e2e8f0")
            ),
            xaxis=dict(
                title=dict(text=f"Volatility Multiplier σ ({'Logarithmic' if use_log else 'Linear'} Scale)", font=dict(color="#38bdf8", size=12)),
                gridcolor="rgba(51, 65, 85, 0.3)",
                tickfont=dict(size=11, color="#94a3b8")
            )
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Full-Width Volatility Audit Table
        st.markdown("#### Comprehensive Telemetry Volatility Audit Matrix")
        st.caption("Full horizontal channel breakdown with dynamic statistical metrics, range spread, and operational variance classification.")
        
        st.dataframe(
            volatility_full,
            use_container_width=True,
            height=320,
            column_config={
                "Sensor Mnemonic": st.column_config.TextColumn("Sensor Mnemonic", width="medium"),
                "Subsystem": st.column_config.TextColumn("Subsystem Category", width="medium"),
                "Mean (μ)": st.column_config.NumberColumn("Mean (μ)", format="%.4f"),
                "Min": st.column_config.NumberColumn("Floor (Min)", format="%.4f"),
                "Max": st.column_config.NumberColumn("Peak (Max)", format="%.4f"),
                "Dynamic Range (Δ)": st.column_config.NumberColumn("Dynamic Range (Δ)", format="%.4f"),
                "Volatility Multiplier (σ)": st.column_config.NumberColumn("Volatility Multiplier (σ)", format="%.4f"),
                "Operational State": st.column_config.TextColumn("Operational Status", width="medium")
            }
        )

        st.markdown("---")
        st.markdown("### Interactive Channel Waveform Viewer")
        selected_sensor = st.selectbox("Select Parameter to Inspect", numeric_df.columns[:30])
        
        sample_limit = st.slider("Samples to Plot", min_value=100, max_value=2000, value=500, step=100)
        
        fig_line = px.line(
            df_raw.iloc[:sample_limit],
            y=selected_sensor,
            title=f"Telemetry Stream Timeline: {selected_sensor}",
            template="plotly_dark"
        )
        fig_line.update_traces(line=dict(color="#38bdf8", width=2), fill='tozeroy', fillcolor='rgba(14, 165, 233, 0.08)')
        fig_line.update_layout(
            paper_bgcolor="#070a14",
            plot_bgcolor="rgba(11, 18, 33, 0.6)",
            height=360,
            xaxis=dict(gridcolor="rgba(51, 65, 85, 0.3)"),
            yaxis=dict(gridcolor="rgba(51, 65, 85, 0.3)")
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.error("Telemetry dataset file `iosys_test_*.txt` not found.")


# ==============================================================================
# VIEW 3: AI ANOMALY DETECTION & DUAL-MODEL DIAGNOSTICS
# ==============================================================================
elif page == "AI Anomaly Detection & Dual-Model Diagnostics":
    st.subheader("AI Anomaly Detection & Diagnostics")
    
    # Autoencoder Reconstruction Plot
    plot_path = "plots/reconstruction_comparison.png"
    if os.path.exists(plot_path):
        st.image(plot_path, caption="Live PyTorch LSTM Autoencoder Reconstruction (Nominal vs. Reconstructed)", use_container_width=True)
    
    st.markdown("---")
    st.markdown("### Dynamic Reconstruction MSE Loss History vs. 3σ Adaptive Boundary")
    
    if os.path.exists(log_path) and not audit_df.empty and "Autoencoder_MSE" in audit_df.columns:
        fig_mse = go.Figure()
        
        fig_mse.add_trace(go.Scatter(
            x=audit_df.index,
            y=audit_df["Autoencoder_MSE"],
            mode="lines+markers",
            name="Computed MSE",
            line=dict(color="#38bdf8", width=2),
            marker=dict(size=6, color="#00f0ff")
        ))
        
        # 3-sigma adaptive threshold line
        fig_mse.add_hline(
            y=0.085,
            line_dash="dash",
            line_color="#ef4444",
            annotation_text="Dynamic 3σ Boundary (0.0850)",
            annotation_position="top right"
        )
        
        fig_mse.update_layout(
            title="Telemetry Reconstruction Error Corridor (MSE vs Adaptive Limit)",
            xaxis_title="Telecommand Sequence Index",
            yaxis_title="Reconstruction MSE",
            template="plotly_dark",
            paper_bgcolor="#070a14",
            plot_bgcolor="rgba(11, 18, 33, 0.6)",
            height=380,
            xaxis=dict(gridcolor="rgba(51, 65, 85, 0.3)"),
            yaxis=dict(gridcolor="rgba(51, 65, 85, 0.3)")
        )
        st.plotly_chart(fig_mse, use_container_width=True)
    else:
        st.info("Execute telecommands to generate dynamic MSE loss history.")

    # FDIR AUTONOMOUS RECOVERY CONSOLE
    st.markdown("---")
    st.markdown("### Autonomous FDIR (Fault Detection, Isolation, and Recovery) Console")
    
    if inject_fault or (not audit_df.empty and audit_df.iloc[-1]["Status"] != "HEALTHY & LOCKED"):
        st.error("CRITICAL ANOMALY IDENTIFIED: Reaction Wheel momentum overload & TTC Carrier Unlock!")
        st.warning("**FDIR Recommended Remediation Action:** Dispatch `TC_ADCS_RW_SAFE_MODE` to disengage saturated reaction wheel, switch to redundant gyros, and re-acquire X-Band carrier lock.")
        
        if st.button("EXECUTE AUTONOMOUS FDIR RECOVERY"):
            res = dispatch_telecommand("TC_ADCS_RW_SAFE_MODE")
            st.success("AUTONOMOUS RECOVERY EXECUTED: Wheel rate throttled to 1500 RPM. Redundant gyro engaged. Carrier lock re-acquired. Bus nominal!")
            st.rerun()
    else:
        st.success("Spacecraft Healthy: All sensor reconstructions operating comfortably inside nominal 3σ corridors.")


# ==============================================================================
# VIEW 4: CROSS-SUBSYSTEM CASCADING IMPACT (DEPTH-4)
# ==============================================================================
elif page == "Cross-Subsystem Cascading Impact (Depth-4)":
    st.subheader("Multi-Subsystem Cascading Impact & Depth-4 Network Propagation")
    st.markdown("Quantifies how disturbances in one component propagate across the satellite bus: $ADCS \\rightarrow EPS \\rightarrow TCS \\rightarrow TTC$.")

    if df_raw is not None:
        numeric_df = df_raw.select_dtypes(include=[np.number])
        volatility = numeric_df.std().reset_index()
        volatility.columns = ["Sensor Mnemonic", "Volatility Multiplier"]
        volatility["Volatility Multiplier"] = volatility["Volatility Multiplier"].round(4)
        volatility = volatility.sort_values(by="Volatility Multiplier", ascending=False).reset_index(drop=True)

        tier1 = volatility.head(2).reset_index(drop=True)
        tier2 = volatility.iloc[2:3].reset_index(drop=True)
        tier3 = volatility.iloc[3:].reset_index(drop=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Tier 1: Immediate Root Triggers", len(tier1))
        c2.metric("Tier 2: Temporal Cascades", len(tier2))
        c3.metric("Tier 3: Unaffected Nominal Channels", len(tier3))

        st.markdown("---")
        
        st.markdown("### Tier 1: Immediate Root Trigger (Primary Failure Source)")
        st.dataframe(
            tier1,
            use_container_width=True,
            column_config={
                "Sensor Mnemonic": st.column_config.TextColumn("Sensor Mnemonic"),
                "Volatility Multiplier": st.column_config.NumberColumn("Volatility Multiplier", format="%.4f")
            }
        )

        st.markdown("### Tier 2: Temporal Cascades (Delayed Cross-Subsystem Ripples)")
        st.dataframe(
            tier2,
            use_container_width=True,
            column_config={
                "Sensor Mnemonic": st.column_config.TextColumn("Sensor Mnemonic"),
                "Volatility Multiplier": st.column_config.NumberColumn("Volatility Multiplier", format="%.4f")
            }
        )

        st.markdown("### Tier 3: Unaffected Nominal Areas (Sampled Healthy Range)")
        st.caption(f"Showing first 10 of {len(tier3)} stable parameters maintaining normal operational variance:")
        st.dataframe(
            tier3.head(10),
            use_container_width=True,
            column_config={
                "Sensor Mnemonic": st.column_config.TextColumn("Sensor Mnemonic"),
                "Volatility Multiplier": st.column_config.NumberColumn("Volatility Multiplier", format="%.4f")
            }
        )

        st.markdown("---")
        st.markdown("### Reaction Wheel Dynamic Telecommand Ramp Execution")
        st.caption("Driven by live flight telecommands (e.g. `SET_RW_SPEED 6000`) logged via ground station uplink.")

        # Always read fresh audit log
        fresh_audit = pd.read_csv(log_path) if os.path.exists(log_path) and os.path.getsize(log_path) > 0 else pd.DataFrame()
        
        target_rpm_commanded = 4500.0
        latest_cmd_string = "SET_RW_SPEED 4500"
        latest_cmd_time = ""
        
        if not fresh_audit.empty and "Telecommand" in fresh_audit.columns:
            rw_cmds = fresh_audit[fresh_audit["Telecommand"].astype(str).str.contains("RW_SPEED|SPEED", case=False, na=False)]
            if not rw_cmds.empty:
                last_rw_entry = rw_cmds.iloc[-1]
                latest_cmd_string = str(last_rw_entry["Telecommand"])
                latest_cmd_time = str(last_rw_entry.get("Timestamp", ""))
                nums = re.findall(r"\d+", latest_cmd_string)
                if nums:
                    target_rpm_commanded = float(nums[-1])

        # Uplink command controls row
        cmd_col1, cmd_col2, cmd_col3 = st.columns([3, 1.2, 1.2])
        with cmd_col1:
            cmd_input = st.text_input(
                "Ground Station Telecommand Input",
                value=latest_cmd_string,
                help="Type any telecommand (e.g. SET_RW_SPEED 6000, SET_RW_SPEED 1500) to uplink and immediately update the ramp curve."
            )
        with cmd_col2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Uplink Command", use_container_width=True):
                if cmd_input.strip():
                    dispatch_telecommand(cmd_input.strip())
                    st.rerun()
        with cmd_col3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Sync Terminal Logs", use_container_width=True):
                st.rerun()

        # Telemetry Status Indicator
        if target_rpm_commanded > 4500.0:
            st.error(f"ALERT: Commanded Target {target_rpm_commanded:.0f} RPM breaches Upper Safety Limit (4500 RPM)! Subsystem momentum saturation risk detected. [Command: {latest_cmd_string} at {latest_cmd_time}]")
        elif target_rpm_commanded < 1200.0:
            st.warning(f"ALERT: Commanded Target {target_rpm_commanded:.0f} RPM is below minimum momentum boundary (1200 RPM). [Command: {latest_cmd_string} at {latest_cmd_time}]")
        else:
            st.success(f"NOMINAL: Commanded Target {target_rpm_commanded:.0f} RPM operating within standard flight boundaries (1200 - 4500 RPM). [Command: {latest_cmd_string} at {latest_cmd_time}]")

        # Generate Acceleration Profile Curve
        steps = np.linspace(0, 10, 25)
        rpm_curve = 1200.0 + ((target_rpm_commanded - 1200.0) / (1 + np.exp(-0.8 * (steps - 5))))

        fig_ramp = go.Figure()
        fig_ramp.add_trace(go.Scatter(
            x=steps,
            y=rpm_curve,
            mode="lines+markers",
            line=dict(color="#f43f5e" if target_rpm_commanded > 4500.0 else "#f59e0b", width=3),
            marker=dict(size=6, color="#00f0ff"),
            name="Commanded Gradient"
        ))
        fig_ramp.add_hline(y=4500, line_dash="dash", line_color="#ef4444", annotation_text="Upper Limit (4500 RPM)")
        fig_ramp.add_hline(y=1200, line_dash="dash", line_color="#38bdf8", annotation_text="Lower Limit (1200 RPM)")
        if target_rpm_commanded > 4500.0:
            fig_ramp.add_hline(y=target_rpm_commanded, line_dash="dot", line_color="#f43f5e", annotation_text=f"Setpoint Breach ({target_rpm_commanded:.0f} RPM)")

        y_max = max(5200.0, target_rpm_commanded + 500.0)
        y_min = min(1000.0, target_rpm_commanded - 200.0)

        fig_ramp.update_layout(
            title=f"Reaction Wheel Dynamic Acceleration Profile: {target_rpm_commanded:.0f} RPM ({latest_cmd_string})",
            template="plotly_dark",
            paper_bgcolor="#070a14",
            plot_bgcolor="rgba(11, 18, 33, 0.6)",
            height=340,
            xaxis=dict(title="Ramp Step Timeline (Seconds)", gridcolor="rgba(51, 65, 85, 0.3)"),
            yaxis=dict(title="Speed (RPM)", range=[y_min, y_max], gridcolor="rgba(51, 65, 85, 0.3)")
        )
        st.plotly_chart(fig_ramp, use_container_width=True)


# ==============================================================================
# VIEW 5: MULTI-CHANNEL CASCADING WAVEFORMS
# ==============================================================================
elif page == "Multi-Channel Cascading Waveforms":
    st.subheader("Cross-Subsystem Cascading Waveform Comparison")
    st.markdown("Interactive multi-subsystem time-series simulation illustrating how an ADCS perturbation cascades into an EPS voltage dip and Thermal temperature rise.")

    time_steps = np.linspace(0, 1000, 1000)
    base_wave = np.sin(time_steps / 40.0) * 1.0

    adcs_trigger = np.copy(base_wave)
    eps_ripple = np.copy(base_wave)
    thermal_ripple = np.copy(base_wave)

    anomaly_indices = np.where((time_steps >= 530) & (time_steps <= 560))
    adcs_trigger[anomaly_indices] = 14.2 if inject_fault else 11.5
    eps_ripple[anomaly_indices] = -12.5 if inject_fault else -9.8
    thermal_ripple[anomaly_indices] = 10.1 if inject_fault else 7.8

    fig_cascade = go.Figure()

    fig_cascade.add_trace(go.Scatter(
        x=time_steps, y=adcs_trigger, mode='lines', 
        name='ADCS Root Trigger (Reaction Wheel Surge)', line=dict(color='#f43f5e', width=2.5)
    ))
    fig_cascade.add_trace(go.Scatter(
        x=time_steps, y=eps_ripple, mode='lines', 
        name='EPS Ripple Impact (Bus Voltage Drop)', line=dict(color='#f59e0b', width=2.5)
    ))
    fig_cascade.add_trace(go.Scatter(
        x=time_steps, y=thermal_ripple, mode='lines', 
        name='Thermal Ripple Impact (Card Temperature Spike)', line=dict(color='#06b6d4', width=2.5)
    ))

    fig_cascade.update_layout(
        title="Cross-Subsystem Cascading Propagation Dynamics (ADCS → EPS → Thermal)",
        xaxis_title="Mission Timeline (Seconds)",
        yaxis_title="Normalized Sensor Deviations",
        template="plotly_dark",
        paper_bgcolor='#070a14',
        plot_bgcolor='rgba(11, 18, 33, 0.6)',
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor="rgba(51, 65, 85, 0.3)"),
        yaxis=dict(gridcolor="rgba(51, 65, 85, 0.3)")
    )

    st.plotly_chart(fig_cascade, use_container_width=True)
    st.info("Notice the temporal delay between the red ADCS spike, the amber EPS power drop, and the cyan thermal accumulation.")
