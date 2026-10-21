import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


class LSTMEncoder(nn.Module):

  def __init__(self, seq_len, n_features, embedding_dim=64):
    super(LSTMEncoder, self).__init__()
    self.lstm1 = nn.LSTM(
        input_size=n_features,
        hidden_size=128,
        num_layers=1,
        batch_first=True,
    )
    self.lstm2 = nn.LSTM(
        input_size=128,
        hidden_size=embedding_dim,
        num_layers=1,
        batch_first=True,
    )

  def forward(self, x):
    x, (hidden, _) = self.lstm1(x)
    x, (hidden, _) = self.lstm2(x)
    return hidden[-1]  # Return latent representation


class LSTMDecoder(nn.Module):

  def __init__(self, seq_len, n_features, embedding_dim=64):
    super(LSTMDecoder, self).__init__()
    self.seq_len = seq_len
    self.lstm1 = nn.LSTM(
        input_size=embedding_dim,
        hidden_size=embedding_dim,
        num_layers=1,
        batch_first=True,
    )
    self.lstm2 = nn.LSTM(
        input_size=embedding_dim,
        hidden_size=128,
        num_layers=1,
        batch_first=True,
    )
    self.output_layer = nn.Linear(128, n_features)

  def forward(self, x):
    # Repeat vector across the sequence length dimension
    x = x.unsqueeze(1).repeat(1, self.seq_len, 1)
    x, _ = self.lstm1(x)
    x, _ = self.lstm2(x)
    return self.output_layer(x)


class TelemetryLSTMAutoencoder(nn.Module):

  def __init__(self, seq_len, n_features, embedding_dim=64):
    super(TelemetryLSTMAutoencoder, self).__init__()
    self.encoder = LSTMEncoder(seq_len, n_features, embedding_dim)
    self.decoder = LSTMDecoder(seq_len, n_features, embedding_dim)

  def forward(self, x):
    latent = self.encoder(x)
    reconstructed = self.decoder(latent)
    return reconstructed


def train_autoencoder(model, train_data, epochs=20, batch_size=32, lr=0.001):
  """Trains the autoencoder on normal nominal telemetry sequences."""
  dataset = TensorDataset(torch.tensor(train_data, dtype=torch.float32))
  dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

  criterion = nn.MSELoss()
  optimizer = torch.optim.Adam(model.parameters(), lr=lr)

  model.train()
  for epoch in range(epochs):
    total_loss = 0
    for (batch_x,) in dataloader:
      optimizer.zero_grad()
      reconstructed = model(batch_x)
      loss = criterion(reconstructed, batch_x)
      loss.backward()
      optimizer.step()
      total_loss += loss.item()

    print(
        f"Epoch [{epoch+1}/{epochs}], Loss:"
        f" {total_loss/len(dataloader):.6f}"
    )

  return model


def detect_anomalies(model, test_data, threshold_percentile=95):
  """Computes reconstruction error (MSE) and flags anomalies based on a dynamic

  threshold.
  """
  model.eval()
  with torch.no_grad():
    test_tensor = torch.tensor(test_data, dtype=torch.float32)
    reconstructed = model(test_tensor)
    # Calculate Mean Squared Error per sequence window
    mse = torch.mean(torch.pow(test_tensor - reconstructed, 2), dim=(1, 2)).numpy()

  # Set threshold dynamically based on validation reconstruction error distribution
  threshold = np.percentile(mse, threshold_percentile)
  anomalies = mse > threshold

  return mse, anomalies, threshold