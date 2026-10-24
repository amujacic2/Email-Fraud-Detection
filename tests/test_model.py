import subprocess
import sys
from pathlib import Path

import pytest

from emailfraud.model import FraudDetector, train_from_csv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "emails.csv"


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    if not DATA.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_data.py")], check=True)
    model, report = train_from_csv(DATA)
    return model, report


def test_model_separates_classes(trained):
    model, _ = trained
    fraud = "Subject: URGENT winner\n\nYou won a prize! Send gift card and bank account now http://10.1.2.3/claim"
    ham = "Subject: Team notes\n\nHi team, notes from the design review are attached."
    assert model.explain(fraud)["label"] == "fraud"
    assert model.explain(ham)["label"] == "legitimate"


def test_save_and_load_roundtrip(trained, tmp_path):
    model, _ = trained
    path = tmp_path / "m.joblib"
    model.save(path)
    loaded = FraudDetector.load(path)
    sample = "Subject: hi\n\nverify your account immediately"
    assert loaded.predict_proba([sample])[0] == pytest.approx(model.predict_proba([sample])[0])
