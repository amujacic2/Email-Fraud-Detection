FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 EMAILFRAUD_MODEL=/app/models/model.joblib
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
RUN pip install --no-cache-dir ".[api]"

# Build a demo model at image build time (synthetic data; mount your own model for real use).
RUN python scripts/generate_data.py && emailfraud train --data data/emails.csv --out models/model.joblib

EXPOSE 8000
CMD ["uvicorn", "emailfraud.api:app", "--host", "0.0.0.0", "--port", "8000"]
