# main.py - Dual-Objective Telemetry Pipeline with Dynamic Thresholds, Real Status Rules & Lock Status
import os
import sys
import time
import datetime
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt
import re

def plot_autoencoder_reconstruction(model, windowed_data, device, sample_idx=0, feature_idx=0):
  """Passes a specific test window through the model and plots real vs reconstructed telemetry curves."""
  model.eval()
  with torch.no_grad():
    original_window = windowed_data[sample_idx] # Shape: (seq_len, n_features)
    tensor_window = torch.tensor(original_window, dtype=torch.float32).unsqueeze(0).to(device)
    
    reconstructed_tensor = model(tensor_window)
    reconstructed_window = reconstructed_tensor.squeeze(0).cpu().numpy()

  os.makedirs("plots", exist_ok=True)
  plot_path = "plots/reconstruction_comparison.png"

  plt.figure(figsize=(10, 4))
  plt.plot(original_window[:, feature_idx], label='Original Telemetry (PCA Component)', color='royalblue', alpha=0.8)
  plt.plot(reconstructed_window[:, feature_idx], label='Autoencoder Reconstructed', color='darkorange', linestyle='--', linewidth=2)
  
  plt.title(f"Autoencoder Reconstruction Check (Sample Window {sample_idx}, Feature {feature_idx})")
  plt.xlabel("Time Step in Window (Seconds)")
  plt.ylabel("Normalized Feature Value")
  plt.legend()
  plt.grid(True, alpha=0.3)
  plt.tight_layout()
  
  plt.savefig(plot_path)
  plt.close()
  print(f"[PLOT] Reconstruction comparison chart saved successfully to {plot_path}")

# Ensure local 'src' path is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# --- 1. IMPORT YOUR EXISTING MODULES ---
try:
  from models.autoencoder import TelemetryLSTMAutoencoder
  from dependency_mapper import SubsystemDependencyMapper
  print(">>> Successfully loaded local modules from src/")
except ImportError as e:
  print(f">>> Warning: Could not import modular files directly ({e}). Using inline fallbacks.")
  
  class TelemetryLSTMAutoencoder(nn.Module):
    def __init__(self, seq_len, n_features, embedding_dim=32):
      super(TelemetryLSTMAutoencoder, self).__init__()
      self.encoder = nn.LSTM(input_size=n_features, hidden_size=64, batch_first=True)
      self.decoder = nn.LSTM(input_size=64, hidden_size=n_features, batch_first=True)
    def forward(self, x):
      _, (h, _) = self.encoder(x)
      dec_in = h[-1].unsqueeze(1).repeat(1, x.shape[1], 1)
      out, _ = self.decoder(dec_in)
      return out

  class SubsystemDependencyMapper:
    def __init__(self):
      pass
    def build_correlation_graph(self, df, feature_cols, threshold=0.75):
      return None
    def trace_cascading_impact(self, trigger_node, max_depth=4):
      return {"trigger_source": trigger_node, "affected_nodes": {}, "total_affected_count": 0}


# --- 2. DEVICE CONFIGURATION FOR MACBOOK AIR M3 ---
if torch.backends.mps.is_available():
  device = torch.device("mps")
  print("Using Apple Silicon GPU (MPS) acceleration.")
else:
  device = torch.device("cpu")
  print("MPS not available, falling back to CPU.")


# --- 3. SUBSYSTEM PCA PIPELINE CLASS ---
class SubsystemPipeline:
  def __init__(self, subsystem_name, variance_threshold=0.95):
    self.subsystem_name = subsystem_name
    self.scaler = StandardScaler()
    self.pca = PCA(n_components=variance_threshold)

  def process_and_reduce(self, df_subsystem_params):
    scaled_data = self.scaler.fit_transform(df_subsystem_params)
    reduced_data = self.pca.fit_transform(scaled_data)
    print(
        f"[{self.subsystem_name}] Reduced dimensions from"
        f" {df_subsystem_params.shape[1]} parameters to"
        f" {reduced_data.shape[1]} principal components."
    )
    return reduced_data


# --- 4. SLIDING WINDOW & REAL TELEMETRY RULE FUNCTIONS ---
def create_sliding_windows(data_matrix, seq_len=60):
  windows = []
  for i in range(len(data_matrix) - seq_len):
    window = data_matrix[i : i + seq_len]
    windows.append(window)
  return np.array(windows)

def create_sequence_classification_windows(features_matrix, labels_array, seq_len=60):
  X, y = [], []
  for i in range(len(features_matrix) - seq_len):
    X.append(features_matrix[i : i + seq_len])
    y.append(labels_array[i + seq_len])
  return np.array(X), np.array(y)

def check_telemetry_rules(row):
  """Strictly uses actual telemetry status registers and real sensor limits safely handling data types."""
  warnings = []
  
  # 1. Real Receiver Carrier Lock Status Registers
  if "TTC_RX-1_CAR_LOCK_STS" in row:
    lock_status_1 = str(row["TTC_RX-1_CAR_LOCK_STS"]).strip()
    if lock_status_1 == "UNLOCK":
      warnings.append("Alert: Receiver 1 Carrier Lock is UNLOCKED")

  if "TTC_RX-2_CAR_LOCK_STS" in row:
    lock_status_2 = str(row["TTC_RX-2_CAR_LOCK_STS"]).strip()
    if lock_status_2 == "UNLOCK":
      warnings.append("Alert: Receiver 2 Carrier Lock is UNLOCKED")

  # 2. Real Thermal Sensor Checks across actual dataframe columns containing 'TMP'
  for col in row.index:
    if "TMP" in col and pd.notnull(row[col]):
      try:
        val = float(row[col])
        if val > 85.0: # Standard safe engineering upper bound threshold
          warnings.append(f"Alert: Thermal Overlimit on {col} ({val} C)")
      except (ValueError, TypeError):
        pass # Skip if value is a string that cannot be parsed as a float

  # 3. Real Bus / Line Dropout Check (Checking for hard electrical/voltage failures at 0V)
  for col in row.index:
    if "VOLT" in col or "POS_" in col:
      if pd.notnull(row[col]):
        try:
          val = float(row[col])
          if val == 0.0:
            warnings.append(f"Alert: Bus Rail Collapse - {col} is at 0V")
        except (ValueError, TypeError):
          pass

  return warnings

def compute_dynamic_mse_threshold(model, dataloader, device, k=3.0):
  """Computes dynamic reconstruction error threshold: Mean + k * StdDev across baseline windows."""
  model.eval()
  mses = []
  criterion = nn.MSELoss(reduction='none')
  with torch.no_grad():
    for (batch_x,) in dataloader:
      batch_x = batch_x.to(device)
      reconstructed = model(batch_x)
      loss = criterion(reconstructed, batch_x).mean(dim=(1, 2))
      mses.extend(loss.cpu().numpy())
  
  mean_mse = np.mean(mses)
  std_mse = np.std(mses)
  dynamic_thresh = mean_mse + (k * std_mse)
  print(f"[DYNAMIC THRESHOLD] Baseline MSE Mean: {mean_mse:.5f} | Std: {std_mse:.5f} | Computed Threshold ({k}σ): {dynamic_thresh:.5f}")
  return dynamic_thresh


# --- 5A. MODEL 1: UNSUPERVISED LSTM AUTOENCODER ---
def train_autoencoder_on_m3(windowed_data, device, epochs=2, batch_size=32):
  tensor_data = torch.tensor(windowed_data, dtype=torch.float32)
  dataset = TensorDataset(tensor_data)
  dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

  n_features = windowed_data.shape[2]
  seq_len = windowed_data.shape[1]

  model = TelemetryLSTMAutoencoder(seq_len=seq_len, n_features=n_features).to(device)
  criterion = nn.MSELoss()
  optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

  print(f"Starting Autoencoder Training on M3 GPU ({device})...")
  model.train()

  for epoch in range(epochs):
    total_loss = 0
    for (batch_x,) in dataloader:
      batch_x = batch_x.to(device)
      optimizer.zero_grad()
      reconstructed = model(batch_x)
      loss = criterion(reconstructed, batch_x)
      loss.backward()
      optimizer.step()
      total_loss += loss.item()

    print(f"Autoencoder Epoch [{epoch+1}/{epochs}], Loss: {total_loss/len(dataloader):.6f}")

  print("Autoencoder Training complete!")
  return model, dataloader


# --- 5B. MODEL 2: SUPERVISED SEQUENCE CLASSIFIER (LOCK RISK PREDICTION) ---
class LockStateLSTMClassifier(nn.Module):
  def __init__(self, seq_len, n_features):
    super(LockStateLSTMClassifier, self).__init__()
    self.lstm = nn.LSTM(input_size=n_features, hidden_size=32, batch_first=True)
    self.fc = nn.Sequential(
        nn.Linear(32, 16),
        nn.ReLU(),
        nn.Linear(16, 1),
        nn.Sigmoid()
    )
  def forward(self, x):
    _, (h, _) = self.lstm(x)
    out = self.fc(h[-1])
    return out

def train_lock_classifier_on_m3(X_data, y_data, device, epochs=2, batch_size=32):
  tensor_x = torch.tensor(X_data, dtype=torch.float32)
  tensor_y = torch.tensor(y_data, dtype=torch.float32).unsqueeze(1)
  dataset = TensorDataset(tensor_x, tensor_y)
  dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

  n_features = X_data.shape[2]
  seq_len = X_data.shape[1]

  model = LockStateLSTMClassifier(seq_len=seq_len, n_features=n_features).to(device)
  criterion = nn.BCELoss()
  optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

  print(f"Starting Lock State Classifier Training on M3 GPU ({device})...")
  model.train()

  for epoch in range(epochs):
    total_loss = 0
    for batch_x, batch_y in dataloader:
      batch_x, batch_y = batch_x.to(device), batch_y.to(device)
      optimizer.zero_grad()
      preds = model(batch_x)
      loss = criterion(preds, batch_y)
      loss.backward()
      optimizer.step()
      total_loss += loss.item()

    print(f"Classifier Epoch [{epoch+1}/{epochs}], Loss: {total_loss/len(dataloader):.6f}")

  print("Lock State Classifier Training complete!")
  return model


# --- 6. REAL TELEMETRY DATA LOADER & CLEANER ---
def load_real_telemetry_data(file_path="iosys_test_09102026-081918385_r1.txt"):
  print(f"Loading actual telemetry file from {file_path}...")
  df = pd.read_csv(file_path, low_memory=False)

  df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d-%b-%Y %H:%M:%S.%f', errors='coerce')
  df = df.sort_values('Timestamp').reset_index(drop=True)

  if 'TTC_RX-1_CAR_LOCK_STS' in df.columns:
    df['TTC_RX-1_CAR_LOCK_STS'] = df['TTC_RX-1_CAR_LOCK_STS'].fillna('UNKNOWN')
  if 'TTC_RX-2_CAR_LOCK_STS' in df.columns:
    df['TTC_RX-2_CAR_LOCK_STS'] = df['TTC_RX-2_CAR_LOCK_STS'].fillna('UNKNOWN')

  temp_cols = [col for col in df.columns if 'TMP' in col]
  if temp_cols:
    df[temp_cols] = df[temp_cols].ffill().bfill()

  df['RX1_Lock_Binary'] = (df['TTC_RX-1_CAR_LOCK_STS'] == 'LOCK').astype(int)
  df['RX2_Lock_Binary'] = (df['TTC_RX-2_CAR_LOCK_STS'] == 'LOCK').astype(int)
  if 'TTC_RX-1_AGC' in df.columns:
    df['AGC_Rolling_Mean'] = df['TTC_RX-1_AGC'].ffill().rolling(window=10, min_periods=1).mean()

  df_numeric = df.select_dtypes(include=[np.number]).fillna(0)
  print(f"Loaded {len(df)} rows and extracted {df_numeric.shape[1]} numeric parameters.")
  return df, df_numeric


# --- 7. ENHANCED DEPENDENCY MAPPER WITH CROSS-COUPLING ---
class EnhancedDependencyMapper:
  def __init__(self, df, numeric_cols, threshold=0.65):
    self.numeric_df = df[numeric_cols]
    self.corr_matrix = self.numeric_df.corr().abs()
    self.threshold = threshold

  def trace_cascading_impact(self, trigger_node, max_depth=4):
    """Deep graph traversal capturing cross-subsystem coupling (Thermal, Power, Attitude)."""
    affected_nodes = {}
    visited = set()

    def _traverse(current_node, current_depth):
      if current_depth > max_depth or current_node in visited:
        return
      visited.add(current_node)

      if current_node in self.corr_matrix:
        correlated = self.corr_matrix[current_node]
        for neighbor, weight in correlated.items():
          if neighbor != current_node and weight >= self.threshold:
            affected_nodes[neighbor] = {
                "depth": current_depth,
                "correlation_weight": round(weight, 3)
            }
            _traverse(neighbor, current_depth + 1)

    _traverse(trigger_node, 1)
    return {
        "trigger_source": trigger_node,
        "affected_nodes": affected_nodes,
        "total_affected_count": len(affected_nodes)
    }


# --- 8. PARAMETER UPPER/LOWER LIMITS & GRADUAL RAMP CONFIGURATION ---
TELEMETRY_OPERATIONAL_LIMITS = {
    "RW_SPEED_RPM": {"LL": 1200.0, "UL": 4500.0},
    "TTC_RX-1_AGC": {"LL": -110.0, "UL": -50.0},
    "BATTERY_VOLTAGE_V": {"LL": 28.0, "UL": 34.5},
}

def simulate_gradual_command_ramps(command_str):
  """Simulates gradual parameter response curves dynamically based on the command value

  and validates them against Upper/Lower Limits.
  """
  cmd_upper = command_str.upper()

  if "SPEED" in cmd_upper or "RW" in cmd_upper:
    numbers = re.findall(r"\d+", command_str)
    target_rpm = float(numbers[-1]) if numbers else 4500.0
    start_rpm = 1200.0

    ll = TELEMETRY_OPERATIONAL_LIMITS["RW_SPEED_RPM"]["LL"]
    ul = TELEMETRY_OPERATIONAL_LIMITS["RW_SPEED_RPM"]["UL"]

    print(f"[SIMULATION] Reaction Wheel speed adjustment initiated. Target: {target_rpm} RPM")

    if target_rpm < ll:
      print(f"  -> [WARNING] Target {target_rpm} RPM violates LOWER LIMIT ({ll} RPM)! Subsystem under-speed risk.")
    elif target_rpm > ul:
      print(f"  -> [WARNING] Target {target_rpm} RPM violates UPPER LIMIT ({ul} RPM)! Subsystem saturation risk.")
    else:
      print(f"  -> [CORRIDOR] Target {target_rpm} RPM is within safe operating limits [LL: {ll} | UL: {ul}]")

    for step in range(1, 4):
      current_rpm = start_rpm + ((target_rpm - start_rpm) * (step / 3.0))
      print(f"  -> [RAMP STEP {step}/3] RW_SPEED_RPM: {current_rpm:.1f} RPM")
      time.sleep(0.15)
      
  elif "TTC" in cmd_upper or "ON" in cmd_upper:
    print("[SIMULATION] Transponder command dropped. Executing state transition...")
    print("  -> [STATE] TTC TX Status: TOGGLING | RF Power Output: Stabilizing...")
    time.sleep(0.2)


# --- 9. INTEGRATED TERMINAL ENGINE ---
def export_execution_report():
  log_path = "logs/telemetry_audit_log.csv"
  if os.path.exists(log_path):
    df = pd.read_csv(log_path)
    with open("isro_report_xband-m-on.tst", "w") as f:
      f.write("ISRO GROUND STATION TELEMETRY EXECUTION REPORT\n")
      f.write("Procedure File: xband-m-on.tst\n")
      f.write("==================================================\n")
      for _, row in df.tail(20).iterrows():
        clean_ts = str(row['Timestamp']).replace('.strftime', '')
        f.write(
            f"[{clean_ts}] COMMAND: {str(row['Telecommand']):<25} |"
            f" STATUS: [{row['Status']}] (MSE: {row['Autoencoder_MSE']})\n"
        )

def compute_command_execution_delay(orbit_type="LEO (URSC Orbit)", altitude_km=550):
  c = 299792.458
  propagation_delay_sec = (altitude_km / c) * 2
  obc_processing_sec = 0.025
  hardware_actuation_sec = 0.150
  total_latency_sec = propagation_delay_sec + obc_processing_sec + hardware_actuation_sec
  return {
      "Propagation (ms)": round(propagation_delay_sec * 1000, 2),
      "OBC Processing (ms)": round(obc_processing_sec * 1000, 2),
      "Hardware Actuation (ms)": round(hardware_actuation_sec * 1000, 2),
      "Total Latency (ms)": round(total_latency_sec * 1000, 2)
  }

class IntegratedTerminalEngine:
  def __init__(self, autoencoder, classifier, windowed_data, raw_df, numeric_cols, dynamic_threshold):
    self.autoencoder = autoencoder
    self.classifier = classifier
    self.windowed_data = windowed_data
    self.raw_df = raw_df
    self.dynamic_threshold = dynamic_threshold
    
    self.mapper = EnhancedDependencyMapper(raw_df, numeric_cols=list(numeric_cols[:40]), threshold=0.65)

    os.makedirs("logs", exist_ok=True)
    self.log_file = "logs/telemetry_audit_log.csv"
    if not os.path.exists(self.log_file):
      pd.DataFrame(columns=[
          "Timestamp", "Telecommand", "Autoencoder_MSE", "Unlock_Risk_Pct", 
          "Rule_Warnings", "Cascading_Impact_Count", "Status"
      ]).to_csv(self.log_file, index=False)

  def log_audit_event(self, cmd, recon_error, lock_prob, rule_warnings_str, impact_count, status_str):
    new_row = {
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Telecommand": cmd,
        "Autoencoder_MSE": round(recon_error, 5),
        "Unlock_Risk_Pct": round(lock_prob * 100, 2),
        "Rule_Warnings": rule_warnings_str,
        "Cascading_Impact_Count": impact_count,
        "Status": status_str
    }
    df_log = pd.read_csv(self.log_file)
    df_log = pd.concat([df_log, pd.DataFrame([new_row])], ignore_index=True)
    df_log.to_csv(self.log_file, index=False)

  def execute_send_check_loop(self, command_str):
    print(f"\n[SEND] Transmitting Telecommand: {command_str}")
    
    simulate_gradual_command_ramps(command_str)

    delay_metrics = compute_command_execution_delay("LEO", 550)
    print(f"[UPLINK] RF Propagation Delay : {delay_metrics['Propagation (ms)']} ms")
    print(f"[OBC]    Command Decoding      : {delay_metrics['OBC Processing (ms)']} ms")
    print(f"[HARDWARE] Actuation & Response: {delay_metrics['Hardware Actuation (ms)']} ms")
    print(f"[TIMING] Total Execution Delay  : {delay_metrics['Total Latency (ms)']} ms")
    time.sleep(0.3)

    print(f"[CHECK] Running Dual-Model Diagnostics & Real Status Rule Checks...")
    
    self.autoencoder.eval()
    self.classifier.eval()
    with torch.no_grad():
      sample_idx = np.random.randint(0, len(self.windowed_data))
      target_tensor = torch.tensor(self.windowed_data[sample_idx], dtype=torch.float32).unsqueeze(0).to(device)
      
      reconstructed = self.autoencoder(target_tensor)
      recon_error = torch.mean((target_tensor - reconstructed) ** 2).item()
      lock_prob = self.classifier(target_tensor).item()

      original_window = self.windowed_data[sample_idx]
      reconstructed_window = reconstructed.squeeze(0).cpu().numpy()
      
      os.makedirs("plots", exist_ok=True)
      plt.figure(figsize=(10, 4))
      plt.plot(original_window[:, 0], label=f'Original Telemetry ({command_str})', color='royalblue', alpha=0.8)
      plt.plot(reconstructed_window[:, 0], label='Autoencoder Reconstructed', color='darkorange', linestyle='--', linewidth=2)
      plt.title(f"Live Reconstruction Check for Command: '{command_str}' (MSE: {recon_error:.5f} | Threshold: {self.dynamic_threshold:.5f})")
      plt.xlabel("Time Step in Window (Seconds)")
      plt.ylabel("Normalized Feature Value")
      plt.legend()
      plt.grid(True, alpha=0.3)
      plt.tight_layout()
      plt.savefig("plots/reconstruction_comparison.png")
      plt.close()

    time.sleep(0.4)
    
    # Run real status register checks on a random sample row from raw dataframe
    sample_row = self.raw_df.sample(n=1).iloc[0]
    rule_warnings = check_telemetry_rules(sample_row)
    rule_warnings_str = " | ".join(rule_warnings) if rule_warnings else "None"

    cascade_summary = ""
    impact_count = 0
    if self.mapper and hasattr(self.mapper, "trace_cascading_impact"):
      try:
        numeric_cols = self.raw_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
          sample_node = numeric_cols[0]
          impact_report = self.mapper.trace_cascading_impact(trigger_node=sample_node, max_depth=4)
          impact_count = impact_report['total_affected_count']
          cascade_summary = f" | Cross-Coupled Nodes Impacted (Depth 4): {impact_count}"
      except Exception as e:
        pass

    is_anomalous = recon_error > self.dynamic_threshold
    lock_risk_threshold = 0.50
    is_lock_risk = lock_prob > lock_risk_threshold
    has_rule_violations = len(rule_warnings) > 0

    if not is_anomalous and not is_lock_risk and not has_rule_violations:
      status_str = "HEALTHY & LOCKED"
      print(f"[CHECKED] Status: {status_str}")
      print(f"  -> Reconstruction MSE : {recon_error:.5f} (Dynamic Threshold: {self.dynamic_threshold:.5f}) -> [NOMINAL]")
      print(f"  -> Receiver Unlock Risk : {lock_prob*100:.1f}% -> [LOCKED]")
      print(f"  -> Status Flag Checks   : ALL NOMINAL{cascade_summary}")
    else:
      status_str = "RISK / ANOMALY DETECTED"
      print(f"[ALERT] Status: {status_str}")
      print(f"  -> Reconstruction MSE : {recon_error:.5f} (Dynamic Threshold: {self.dynamic_threshold:.5f})")
      if is_anomalous:
        print(f"     [!] WARNING: MSE exceeded threshold!")
      print(f"  -> Receiver Unlock Risk : {lock_prob*100:.1f}%")
      if is_lock_risk:
        print(f"     [!] WARNING: High risk of receiver loss of lock!")
      if has_rule_violations:
        print(f"     [!] HARDWARE / STATUS ALERTS: {rule_warnings_str}")
      if cascade_summary:
        print(f"  -> {cascade_summary}")

    self.log_audit_event(command_str, recon_error, lock_prob, rule_warnings_str, impact_count, status_str)
    export_execution_report()
    print(f"[AUDIT] Telecommand logged and execution report updated successfully.")

# --- 10. MAIN ORCHESTRATION WORKFLOW ---
def run_pipeline():
  print("Initializing URSC Pipeline with Dynamic Thresholds, Real Status Rules & Lock Classification...")

  subsystem_name = "IOSYS"

  raw_df, df_numeric = load_real_telemetry_data("iosys_test_09102026-081918385_r1.txt")

  pipeline = SubsystemPipeline(subsystem_name=subsystem_name, variance_threshold=0.95)
  reduced_features = pipeline.process_and_reduce(df_numeric)

  seq_len = 60
  windowed_data = create_sliding_windows(reduced_features, seq_len=seq_len)
  
  lock_labels = (raw_df['TTC_RX-1_CAR_LOCK_STS'] != 'LOCK').astype(int).values
  X_cls, y_cls = create_sequence_classification_windows(reduced_features, lock_labels, seq_len=seq_len)

  print(f"[{subsystem_name}] Autoencoder Tensor Shape: {windowed_data.shape}")
  print(f"[{subsystem_name}] Classifier Tensor Shape  : {X_cls.shape}")

  trained_autoencoder, train_loader = train_autoencoder_on_m3(windowed_data, device, epochs=2)
  trained_classifier = train_lock_classifier_on_m3(X_cls, y_cls, device, epochs=2)
  
  dynamic_threshold = compute_dynamic_mse_threshold(trained_autoencoder, train_loader, device, k=3.0)

  plot_autoencoder_reconstruction(trained_autoencoder, windowed_data, device, sample_idx=10, feature_idx=0)

  print("\n" + "="*50)
  print("SPACE STATION OPERATOR TERMINAL (REAL STATUS REGISTERS & DYNAMIC THRESHOLDS)")
  print("Connected to telemetry file, models, depth-4 dependency mapper, and CSV logger.")
  print("Type telecommands (e.g., 'TC_EXEC_CMD 1', 'SET_RW_SPEED 1500', 'SET_RW_SPEED 800', 'TTC1_ON') or type 'exit' to quit.")
  print("="*50 + "\n")

  terminal = IntegratedTerminalEngine(trained_autoencoder, trained_classifier, windowed_data, raw_df, df_numeric.columns, dynamic_threshold)

  while True:
    try:
      cmd = input("URSC-CMD >>> ").strip()
      if cmd.lower() in ["exit", "quit"]:
        print(">>> Shutting down terminal. Audit logs saved in logs/telemetry_audit_log.csv")
        break
      if not cmd:
        continue
      terminal.execute_send_check_loop(cmd)
      print("-" * 50)
    except KeyboardInterrupt:
      print("\n>>> Exiting. Audit logs saved in logs/telemetry_audit_log.csv")
      break

if __name__ == "__main__":
  run_pipeline()