class SelfLabeler:

  def __init__(self, df):
    self.df = df

  def apply_expert_heuristics(self, limits_dict):
    """Applies strict ISRO bus specifications and rule-based checks."""
    labels = np.zeros(len(self.df), dtype=int)  # 0: Normal

    for param, limits in limits_dict.items():
      if param in self.df.columns:
        # Hard limits check
        out_of_bounds = (self.df[param] < limits["min"]) | (
            self.df[param] > limits["max"]
        )
        labels[out_of_bounds] = 1  # 1: Critical Threshold Breach

        # Rate of change anomaly
        if "max_roc" in limits:
          roc = self.df[param].diff().abs()
          labels[roc > limits["max_roc"]] = 2  # 2: Rapid Spike Anomaly

    self.df["label"] = labels
    return self.df