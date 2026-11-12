from pathlib import Path
from tempfile import TemporaryDirectory

import joblib
from app.train_model import build_model


def test_model_training_and_inference():
    with TemporaryDirectory() as tmp:
        path = build_model(str(Path(tmp) / "risk.joblib"))
        model = joblib.load(path)
        low = model.predict_proba([[50_000, 1, 0]])[0][1]
        high = model.predict_proba([[20_000_000, 20, 1]])[0][1]
        assert 0 <= low <= 1 and 0 <= high <= 1
        assert high > low
