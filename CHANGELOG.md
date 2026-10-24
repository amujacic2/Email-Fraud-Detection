# Changelog

## 0.3.0
- Fix: hand-typed scam emails without headers or links (tax refund, advance-fee, job, crypto, boss/BEC, delivery-fee, prize scams) were scored low risk.
- New language signals: `pii_request`, `scam_phrases`, `generic_greeting`, `secrecy`, `click_cta`, `bec_pattern`, `large_amount`.
- Rule score rebalanced so scam language alone can raise the risk.
- Training data is now composed from varied building blocks instead of a few fixed templates, with more legitimate hard negatives.
- 17 new regression tests for plain-text scams and look-alike legitimate mail.

## 0.2.0
- New signals: SPF/DKIM/DMARC failures, display-name spoofing, lookalike (typosquat/leetspeak) domains, punycode, risky attachments.
- Hybrid scoring: transparent rule score combined with the ML probability (noisy-OR).
- FastAPI service (`POST /scan`, `GET /health`) and a browser UI at `/`.
- `emailfraud evaluate` for k-fold cross-validation.
- Harder synthetic dataset with hard negatives and subtle fraud.
- Dockerfile, Makefile, ruff linting, expanded CI, contribution docs.

## 0.1.0
- Initial release: heuristic features, TF-IDF logistic regression, CLI, tests.

## 0.3.1
- Fix: "Model not found" error. The model path is now anchored to the project folder (works from any directory) and a demo model is trained automatically on first use.

## 0.3.2
- Redesigned web UI: score gauge, plain-English signal explanations, example emails, drag-and-drop .eml files, scan history, light/dark theme, mobile layout.
