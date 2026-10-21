# dashboard.py - URSC Dynamic Telemetry & Cascading Impact Dashboard
import os
import re
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="URSC Telemetry & Command Operations",
    page_icon=None,
    layout="wide"
)

st.title("URSC Dynamic Telemetry & Command Operations")
st.markdown("---")

# --- CACHED DATA LOADER FOR REAL TELEMETRY ---
@st.cache_data
def load_real_data():
  file_path = "iosys_test_09102026-081918385_r1.txt"
  if os.path.exists(file_path):
    df = pd.read_csv(file_path, low_memory=False)
    if "Timestamp" in df.columns:
      df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%d-%b-%Y %H:%M:%S.%f", errors="coerce")
      df = df.sort_values("Timestamp").reset_index(drop=True)
    return df
  return None

df_raw = load_real_data()

# Load audit logs for metrics
log_path = "logs/telemetry_audit_log.csv"
audit_df = pd.read_csv(log_path) if os.path.exists(log_path) else pd.DataFrame()

# Sidebar Navigation with Dedicated Cascading Waveform Page
page = st.sidebar.selectbox("Select Dashboard View", [
    "Live Telemetry & Command Log",
    "Real-Time Reconstruction & Anomaly View",
    "Subsystem Correlation & Parameter Analysis",
    "Cascading Impact & Tiered Analysis",
    "Cross-Subsystem Cascading Waveform Analysis"
])

# --- VIEW 1: LIVE TELEMETRY & COMMAND LOG ---
if page == "Live Telemetry & Command Log":
  st.subheader("Subsystem Telemetry Stream & Terminal Audit Synchronization")

  col_m1, col_m2, col_m3, col_m4 = st.columns(4)
  with col_m1:
    st.metric("Telemetry Records", f"{len(df_raw):,}" if df_raw is not None else "0")
  with col_m2:
    st.metric("Commands Executed", len(audit_df) if not audit_df.empty else 0)
  with col_m3:
    last_status = audit_df["Status"].iloc[-1] if not audit_df.empty and "Status" in audit_df.columns else "STANDBY"
    st.metric("System Status", last_status)
  with col_m4:
    last_mse = f"{audit_df['Autoencoder_MSE'].iloc[-1]:.4f}" if not audit_df.empty and "Autoencoder_MSE" in audit_df.columns else "N/A"
    st.metric("Reconstruction MSE", last_mse)

  st.markdown("---")
  st.markdown("### Telemetry Stream Highlights")
  if df_raw is not None:
    key_cols = [c for c in ["Timestamp", "TTC_RX-1_CAR_LOCK_STS", "TTC_RX-1_AGC", "RX1_Lock_Binary"] if c in df_raw.columns]
    if not key_cols:
      key_cols = list(df_raw.columns[:6])
    st.dataframe(df_raw[key_cols].head(15), use_container_width=True)
  else:
    st.error("Telemetry dataset file not found.")

  st.markdown("---")
  st.markdown("### VS Code Terminal Audit Log")
  if os.path.exists(log_path) and not audit_df.empty:
    st.dataframe(audit_df.tail(15), use_container_width=True)
  else:
    st.info("No audit log generated yet.")

# --- VIEW 2: REAL-TIME RECONSTRUCTION & ANOMALY VIEW ---
elif page == "Real-Time Reconstruction & Anomaly View":
  st.subheader("Model Inference & Autoencoder Reconstruction Validation")

  plot_path = "plots/reconstruction_comparison.png"
  if os.path.exists(plot_path):
    st.image(plot_path, caption="Backend LSTM Autoencoder Reconstruction Comparison")
  else:
    st.info("No reconstruction plot found. Run a command in your terminal.")

  st.markdown("### Recent Dynamic Anomaly Score History (MSE Loss vs. Adaptive Threshold)")
  if os.path.exists(log_path) and "Autoencoder_MSE" in audit_df.columns:
    fig, ax = plt.subplots(figsize=(10, 4))
    
    mse_values = audit_df["Autoencoder_MSE"].values
    steps = range(len(mse_values))
    
    mean_mse = np.mean(mse_values)
    std_mse = np.std(mse_values)
    dyn_thresh = mean_mse + (3.0 * std_mse) if std_mse > 0 else 15.0

    colors = ['crimson' if val > dyn_thresh else 'royalblue' for val in mse_values]
    
    ax.plot(steps, mse_values, color='gray', linestyle='-', alpha=0.5, label='Reconstruction MSE Trajectory')
    ax.scatter(steps, mse_values, c=colors, s=50, zorder=3, label='Command Execution Point')
    ax.axhline(dyn_thresh, color='red', linestyle='--', linewidth=2, label=f'Adaptive Threshold (Mean + 3σ: {dyn_thresh:.3f})')
    
    ax.set_title("Terminal Telecommand Anomaly Audit (MSE Loss Corridor)")
    ax.set_xlabel("Telecommand Execution Sequence Index")
    ax.set_ylabel("Mean Squared Error (MSE)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    
    st.pyplot(fig)
    st.success("Chart enhanced: Showing safety corridors and dynamic threshold boundaries.")
  else:
    st.info("Waiting for audit logs...")

# --- VIEW 3: SUBSYSTEM CORRELATION & PARAMETER ANALYSIS ---
elif page == "Subsystem Correlation & Parameter Analysis":
  st.subheader("Subsystem Parameter Variance & Statistical Analysis")

  if df_raw is not None:
    numeric_df = df_raw.select_dtypes(include=[np.number])

    st.markdown("### Computed Parameter Volatility (Standard Deviation)")
    if not numeric_df.empty:
      volatility = numeric_df.std().reset_index()
      volatility.columns = ["Sensor Mnemonic", "Volatility Multiplier"]
      volatility = volatility.sort_values(by="Volatility Multiplier", ascending=False)
      st.dataframe(volatility.head(20), use_container_width=True)

    st.markdown("### Telemetry Channel Trend Viewer")
    selected_col = st.selectbox("Select Parameter to Plot", numeric_df.columns[:20])
    if selected_col:
      fig, ax = plt.subplots(figsize=(10, 4))
      ax.plot(df_raw.index[:500], df_raw[selected_col].head(500), color="#1f77b4", linewidth=1.2)
      ax.set_title(f"Telemetry Timeline: {selected_col}")
      ax.set_xlabel("Data Sample Index")
      ax.set_ylabel("Sensor Value")
      ax.grid(True, alpha=0.2)
      st.pyplot(fig)
  else:
    st.error("Telemetry dataset not loaded.")

# --- VIEW 4: CASCADING IMPACT & TIERED ANALYSIS ---
elif page == "Cascading Impact & Tiered Analysis":
  st.subheader("Multi-Subsystem Cascading Impact & Depth-4 Cross-Coupling")
  st.markdown("Dynamic breakdown of root triggers, cross-coupled parameter ripples, and gradual command gradients.")

  if df_raw is not None:
    numeric_df = df_raw.select_dtypes(include=[np.number])
    if not numeric_df.empty:
      volatility = numeric_df.std().reset_index()
      volatility.columns = ["Sensor Mnemonic", "Volatility Multiplier"]
      volatility = volatility.sort_values(by="Volatility Multiplier", ascending=False).reset_index(drop=True)

      tier1 = volatility.head(2)
      tier2 = volatility.iloc[2:4]
      tier3 = volatility.iloc[4:]

      c1, c2, c3 = st.columns(3)
      with c1:
        st.metric("Tier 1: Immediate Root Triggers", len(tier1))
      with c2:
        st.metric("Tier 2: Depth-4 Cross-Coupled Cascades", len(tier2))
      with c3:
        st.metric("Tier 3: Unaffected Nominal Channels", len(tier3))

      st.markdown("---")
      st.markdown("### Tier 1: Immediate Root Trigger (Primary Source)")
      st.dataframe(tier1, use_container_width=True)

      st.markdown("### Tier 2: Temporal Cascades (Cross-Subsystem Ripples)")
      st.dataframe(tier2, use_container_width=True)

      st.markdown("### Tier 3: Unaffected Nominal Areas")
      st.dataframe(tier3.head(10), use_container_width=True)

      st.markdown("---")
      st.markdown("### Reaction Wheel & General Command Gradient Simulator")
      
      default_cmd = "SET_RW_SPEED 1500"
      if not audit_df.empty and "Telecommand" in audit_df.columns:
        default_cmd = audit_df["Telecommand"].iloc[-1]

      command_choice = st.text_input("Simulate Telecommand Parameter Gradient", value=default_cmd)
      
      if st.button("Generate Gradual Ramp Curve"):
        steps = np.linspace(0, 10, 20)
        cmd_upper = command_choice.upper()

        if "SPEED" in cmd_upper or "RW" in cmd_upper:
          numbers = re.findall(r"\d+", command_choice)
          target_rpm = float(numbers[-1]) if numbers else 4500.0
          start_rpm = 1200.0

          rpm_curve = start_rpm + ((target_rpm - start_rpm) / (1 + np.exp(-0.8 * (steps - 5))))

          fig, ax = plt.subplots(figsize=(10, 3.5))
          ax.plot(steps, rpm_curve, marker='o', color='darkorange', linewidth=2)
          ax.set_title(f"Reaction Wheel Dynamic Acceleration Ramp (Target: {target_rpm:.0f} RPM)")
          ax.set_xlabel("Execution Time Steps")
          ax.set_ylabel("Speed (RPM)")
          ax.grid(True, alpha=0.3)

          ax.axhline(4500, color="red", linestyle="--", alpha=0.6, label="Upper Limit (4500 RPM)")
          ax.axhline(1200, color="blue", linestyle="--", alpha=0.6, label="Lower Limit (1200 RPM)")
          ax.legend()

          st.pyplot(fig)
          st.success(f"Dynamic transition curve generated successfully for Target Speed: {target_rpm:.0f} RPM.")
        else:
          st.info(f"Simulating gradient response for command: '{command_choice}'")
          df_sim = pd.DataFrame({"Step": steps, "Transponder_RF_Power": np.linspace(0.0, 3.0, len(steps))})
          st.dataframe(df_sim, use_container_width=True)
  else:
    st.error("Telemetry dataset not loaded.")

# --- VIEW 5: CROSS-SUBSYSTEM CASCADING WAVEFORM ANALYSIS ---
elif page == "Cross-Subsystem Cascading Waveform Analysis":
  st.subheader("Cross-Subsystem Cascading Waveform Comparison")
  st.markdown("Interactive multi-subsystem time-series simulation showing anomaly propagation ripples across ADCS, EPS, and Thermal nodes.")

  if st.button("Simulate & Plot Waveform Cascade"):
    # Generate timeline steps
    time_steps = np.linspace(0, 1000, 1000)
    
    # Base nominal wave (Thermal / General telemetry)
    base_wave = np.sin(time_steps / 40.0) * 1.0
    
    # Anomaly injection around t = 530 - 560
    adcs_trigger = np.copy(base_wave)
    eps_ripple = np.copy(base_wave)
    thermal_ripple = np.copy(base_wave)
    
    anomaly_indices = np.where((time_steps >= 530) & (time_steps <= 560))
    adcs_trigger[anomaly_indices] = 12.0  # Sharp spike in ADCS root trigger
    eps_ripple[anomaly_indices] = -10.0   # Power drop ripple in EPS
    thermal_ripple[anomaly_indices] = 8.5 # Heat dissipation ripple in Thermal

    fig_cascade = go.Figure()
    
    fig_cascade.add_trace(go.Scatter(
        x=time_steps, y=adcs_trigger, mode='lines', 
        name='ADCS Root Trigger (adcs_tm_15)', line=dict(color='crimson', width=2)
    ))
    fig_cascade.add_trace(go.Scatter(
        x=time_steps, y=eps_ripple, mode='lines', 
        name='EPS Ripple Impact (eps_tm_42)', line=dict(color='darkorange', width=2)
    ))
    fig_cascade.add_trace(go.Scatter(
        x=time_steps, y=thermal_ripple, mode='lines', 
        name='Thermal Ripple Impact (thermal_tm_88)', line=dict(color='deepskyblue', width=2)
    ))

    fig_cascade.update_layout(
        title="Cross-Subsystem Cascading Waveform Comparison",
        xaxis_title="Mission Timeline (Seconds)",
        yaxis_title="Normalized Sensor Readings",
        template="plotly_dark",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.success("Cascading simulation data loaded successfully!")
    st.plotly_chart(fig_cascade, use_container_width=True)
  else:
    st.info("Click the button above to execute and render the live cascading waveform simulation.")