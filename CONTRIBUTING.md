# Contributing

Thanks for helping improve Email Fraud Detection!

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python scripts/generate_data.py
pytest
```

## Adding a detection signal

1. Add the feature to `extract_features` in `src/emailfraud/features.py` and append its name to `FEATURE_NAMES`.
2. Give it a weight in `rule_score` if it should affect the rule-based risk directly.
3. Add tests in `tests/test_features.py` covering a positive case **and** a close negative case (false positives matter).
4. Mention it in the README signal table.

## Style

`ruff check .` and `ruff format .` must pass. CI enforces both.

## Data

Never commit real emails or personal data. Anonymise samples before sharing them in issues.
