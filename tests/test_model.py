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
    fraud = (
        "Subject: URGENT winner\n\nYou won a prize! Send gift card and bank account now http://10.1.2.3/claim"
    )
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


HAND_FRAUD = [
    'From: "Microsoft 365" <no-reply@micros0ft-support.top>\nSubject: Password expires today\n\n'
    "Your password expires in 2 hours. Keep your password here: http://bit.ly/keep-pw",
    "Subject: Dear beneficiary\n\nYou are the winner of 2 million dollars lottery. Send your bank account and a "
    "gift card for the processing fee. Act now!",
    "From: boss@corp-mail.ru\nReply-To: boss@gmail.com\nSubject: Urgent task\n\n"
    "Buy gift card codes immediately and reply with the numbers. Do not tell anyone.",
]
HAND_LEGIT = [
    "From: dana@company.com\nSubject: Standup moved\n\nStandup is moved to 10:30 tomorrow. Same room as usual.",
    "From: noreply@github.com\nSubject: [repo] New issue\n\nSomeone opened an issue: https://github.com/org/repo/issues/12",
    "From: mom@family.net\nSubject: Sunday dinner\n\nCan you bring dessert on Sunday? Love you!",
]


def test_handwritten_emails_outside_templates(trained):
    model, _ = trained
    assert all(model.explain(e)["label"] == "fraud" for e in HAND_FRAUD)
    assert all(model.explain(e)["label"] == "legitimate" for e in HAND_LEGIT)
