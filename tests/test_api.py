import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from emailfraud import api
from emailfraud.model import train_from_csv

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def client(tmp_path_factory, monkeypatch_module):
    data = ROOT / "data" / "emails.csv"
    if not data.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_data.py")], check=True)
    path = tmp_path_factory.mktemp("m") / "model.joblib"
    train_from_csv(data)[0].save(path)
    monkeypatch_module.setenv("EMAILFRAUD_MODEL", str(path))
    api.get_model.cache_clear()
    return TestClient(api.app)


@pytest.fixture(scope="module")
def monkeypatch_module():
    from _pytest.monkeypatch import MonkeyPatch

    mp = MonkeyPatch()
    yield mp
    mp.undo()


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_scan_flags_phishing(client):
    raw = "From: x@evil.xyz\nSubject: URGENT\n\nVerify your account immediately http://10.0.0.1/login password!!!"
    body = client.post("/scan", json={"raw": raw}).json()
    assert body["label"] == "fraud"
    assert "has_ip_url" in body["signals"]


def test_scan_rejects_empty(client):
    assert client.post("/scan", json={"raw": ""}).status_code == 422


def test_index_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "Email Fraud Detection" in r.text
