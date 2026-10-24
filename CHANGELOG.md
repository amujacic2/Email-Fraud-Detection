# Changelog

## 0.2.0
- New signals: SPF/DKIM/DMARC failures, display-name spoofing, lookalike (typosquat/leetspeak) domains, punycode, risky attachments.
- Hybrid scoring: transparent rule score combined with the ML probability (noisy-OR).
- FastAPI service (`POST /scan`, `GET /health`) and a browser UI at `/`.
- `emailfraud evaluate` for k-fold cross-validation.
- Harder synthetic dataset with hard negatives and subtle fraud.
- Dockerfile, Makefile, ruff linting, expanded CI, contribution docs.

## 0.1.0
- Initial release: heuristic features, TF-IDF logistic regression, CLI, tests.
