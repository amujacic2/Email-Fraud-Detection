"""Hand-typed scams with no headers or links must be flagged; ordinary mail must not."""

import subprocess
import sys
from pathlib import Path

import pytest

from emailfraud.model import train_from_csv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "emails.csv"

SCAMS = {
    "tax refund": "Dear Sir, We noticed an error in your tax return. You are owed a refund of $1,284. Reply with your full name, date of birth and bank details so we can deposit it.",
    "account locked": "Hello, your bank account has been locked due to suspicious activity. Click here to unlock it and confirm your card number.",
    "advance fee": "Dear friend, I am Prince Ahmed from Nigeria. I have $15,000,000 to transfer and need your help. You will receive 30 percent. Please send your full name and account number.",
    "job scam": "Congratulations! You have been selected for a work from home job paying $5000 weekly. No experience needed. Send your SSN and a copy of your ID to start today.",
    "boss scam": "Hi, are you at your desk? I need you to do a quick task for me. Reply as soon as you see this. Do not call.",
    "crypto": "Double your Bitcoin in 24 hours! Guaranteed returns. Send 0.5 BTC to our wallet and receive 1 BTC back.",
    "delivery fee": "Your package could not be delivered. Pay a $1.99 redelivery fee here: http://track-parcel.top/pay",
    "inheritance": "I am a lawyer. A relative of yours died leaving 8.5 million dollars. Contact me with your details to claim the inheritance.",
    "free prize": "You won a free iPhone. Click the link to claim now.",
    "virus": "Viruses detected! Your computer is infected. Click here to remove them now.",
}
LEGIT = {
    "meeting": "Hi Sam, can we move our meeting to 3pm tomorrow? Thanks, Alex",
    "lunch": "Hey, are you free for lunch tomorrow around noon?",
    "maintenance": "Subject: URGENT: maintenance\n\nOur servers will be down immediately after 10pm. Please save your work.",
    "receipt": "Your payment was processed and your package is on the way. Track it at https://www.amazon.com/progress/123. Thanks!",
    "invoice": "Hi Dana, the invoice for the design review vendor is attached. Please approve it by Friday.",
    "birthday": "Happy birthday Casey! Hope you have a wonderful day.",
    "bank notice": "Your monthly statement is ready. Sign in to the app to view it. We will never ask for your password by email.",
}


@pytest.fixture(scope="module")
def model():
    if not DATA.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_data.py")], check=True)
    return train_from_csv(DATA)[0]


@pytest.mark.parametrize("name", SCAMS)
def test_scam_is_flagged(model, name):
    result = model.explain(SCAMS[name])
    assert result["label"] == "fraud", result
    assert result["risk"] in ("medium", "high")


@pytest.mark.parametrize("name", LEGIT)
def test_legit_is_not_flagged(model, name):
    result = model.explain(LEGIT[name])
    assert result["label"] == "legitimate", result
