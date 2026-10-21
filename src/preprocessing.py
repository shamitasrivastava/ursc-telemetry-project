import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


class TelemetryPreprocessor:

  def __init__(self, telemetry_df, telecommand_df=None):
    self.telemetry_df = telemetry_df
    self.telecommand_df = telecommand_df
    self.scaler = MinMaxScaler()

  def clean_and_align(self, timestamp_col="timestamp"):
    """Aligns telemetry and telecommand streams on a unified timeline."""
    self.telemetry_df[timestamp_col] = pd.to_datetime(
        self.telemetry_df[timestamp_col]
    )
    self.telemetry_df = self.telemetry_df.sort_values(timestamp_col).reset_index(
        drop=True
    )

    # Handle missing values using forward fill (standard for continuous satellite sensors)
    self.telemetry_df = self.telemetry_df.ffill().bfill()
    return self.telemetry_df

  def extract_rolling_features(self, feature_cols, window_size=60):
    """Extracts rolling statistical features to capture temporal trends."""
    df_features = pd.DataFrame()

    for col in feature_cols:
      # Rolling Mean
      df_features[f"{col}_mean"] = (
          self.telemetry_df[col].rolling(window=window_size).mean()
      )
      # Rolling Standard Deviation (Volatility)
      df_features[f"{col}_std"] = (
          self.telemetry_df[col].rolling(window=window_size).std()
      )
      # Rate of Change (First Derivative)
      df_features[f"{col}_roc"] = self.telemetry_df[col].diff()

    # Drop NaNs created by rolling windows and merge back
    df_features = df_features.bfill().ffill()
    return df_features