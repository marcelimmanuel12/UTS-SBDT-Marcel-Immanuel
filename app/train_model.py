"""Buat model demonstrasi dari data SINTETIS; bukan model produksi perbankan."""
from pathlib import Path
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_model(path: str = "models/risk_model.joblib") -> str:
    rng = np.random.default_rng(2026)
    amount = rng.uniform(5_000, 20_000_000, size=600)
    tx_count = rng.integers(0, 24, size=600)
    new_device = rng.integers(0, 2, size=600)
    x = np.column_stack([amount, tx_count, new_device])
    # Label sengaja sintetis agar ada contoh inference end-to-end.
    signal = (amount / 7_500_000) + (tx_count / 8.0) + new_device * 1.25
    y = (signal + rng.normal(0, .45, size=600) > 2.7).astype(int)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=500, random_state=2026)),
    ])
    pipeline.fit(x, y)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, out)
    return str(out)


if __name__ == "__main__":
    print(build_model())
