# Full LSTM training loop

A complete, runnable program that forecasts tomorrow's maximum temperature from
the past 30 days of observations at Kraków-Balice. Requires the `[torch]` extra:

```bash
pip install imgw-meteo[torch]
```

```python
import torch
import torch.nn as nn

from imgw_meteo import IMGWClient

# ---------------------------------------------------------------------------
# 1. Build dataloaders from standardized IMGW data.
# ---------------------------------------------------------------------------
loaders = (
    IMGWClient()
    .select(
        frequency="daily",
        station_type="synop",
        years=range(2010, 2026),
        stations=["250190390"],      # Kraków-Balice
    )
    .get_dataloaders(
        features=["TMAX", "TMIN", "STD"],
        targets=["TMAX"],
        input_window=30,
        horizon=1,
        batch_size=64,
        normalize="zscore",          # features only; target stays in °C
        fill_missing="forward",
    )
)
train_dl, val_dl, test_dl = loaders


# ---------------------------------------------------------------------------
# 2. A small LSTM regressor.
# ---------------------------------------------------------------------------
class Forecaster(nn.Module):
    def __init__(self, n_features: int, hidden: int = 32):
        super().__init__()
        self.lstm = nn.LSTM(n_features, hidden, batch_first=True)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x):            # x: (batch, window, n_features)
        out, _ = self.lstm(x)
        return self.head(out[:, -1:])  # (batch, 1, 1) → predict last step


model = Forecaster(n_features=len(loaders.feature_names))
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()


# ---------------------------------------------------------------------------
# 3. Train, tracking validation loss (in real °C² since targets are unscaled).
# ---------------------------------------------------------------------------
def run_epoch(dl, train: bool):
    model.train(train)
    total, n = 0.0, 0
    for x, y in dl:
        if train:
            opt.zero_grad()
        pred = model(x)
        loss = loss_fn(pred, y)
        if train:
            loss.backward()
            opt.step()
        total += loss.item() * len(x)
        n += len(x)
    return total / max(n, 1)


for epoch in range(10):
    tr = run_epoch(train_dl, train=True)
    with torch.no_grad():
        va = run_epoch(val_dl, train=False)
    print(f"epoch {epoch:2d}  train MSE {tr:6.2f}  val MSE {va:6.2f}")


# ---------------------------------------------------------------------------
# 4. Evaluate on the held-out test split (RMSE in °C).
# ---------------------------------------------------------------------------
with torch.no_grad():
    test_mse = run_epoch(test_dl, train=False)
print(f"test RMSE: {test_mse ** 0.5:.2f} °C")
```

## Notes

- **Interpretable loss.** Because targets are left in physical units, the MSE is
  in °C² and the RMSE is in °C — no inverse-transform needed to read results.
- **No leakage.** The chronological split means the model is validated and
  tested on time periods strictly after what it trained on.
- **Swap the task easily.** Change `targets` to `["SMDB"]` to forecast
  precipitation, or `horizon=7` to predict a week ahead; the loop is unchanged.
```
