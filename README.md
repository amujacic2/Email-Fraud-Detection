# Email Fraud Detection

Detects phishing and fraudulent emails by combining two signals:

1. **Heuristic features** ([features.py](src/emailfraud/features.py)): IP-address links, URL shorteners, suspicious TLDs, urgency / money / credential language, `Reply-To` vs `From` mismatch, HTML forms, and link text that does not match its target.
2. **Text model** ([model.py](src/emailfraud/model.py)): TF-IDF (1-2 grams) concatenated with the scaled heuristic features, fed to a logistic regression.

Each scan returns a fraud score plus the list of heuristic signals that fired, so results are explainable.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows; use `source .venv/bin/activate` elsewhere
pip install -r requirements.txt
pip install -e .

python scripts/generate_data.py   # builds data/emails.csv (synthetic)
emailfraud train                  # trains and saves models/model.joblib
emailfraud scan suspicious.eml    # exit code 1 if any email is flagged
emailfraud scan a.eml b.eml --json
```

## Tests

```bash
pytest
```

CI runs the same steps on Python 3.11-3.13 via [GitHub Actions](.github/workflows/ci.yml).

## Important caveat

The bundled dataset is **synthetic and template-based**, so the near-perfect metrics it produces are not representative of real-world performance. For real use, train on a genuine corpus (for example the Enron emails as legitimate and the Nazario phishing corpus as fraud) in the same `text,label` CSV format (`label` 1 = fraud):

```bash
emailfraud train --data path/to/real_emails.csv
```

## Layout

```
src/emailfraud/   features, model, CLI
scripts/          synthetic data generator
tests/            pytest suite
data/             emails.csv (generated)
models/           trained model (git-ignored)
```

## License

MIT
