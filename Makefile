.PHONY: install data train evaluate test lint serve docker

install:
	pip install -e ".[dev]"

data:
	python scripts/generate_data.py

train: data
	emailfraud train

evaluate: data
	emailfraud evaluate

test:
	pytest

lint:
	ruff check . && ruff format --check .

serve: train
	uvicorn emailfraud.api:app --reload

docker:
	docker build -t email-fraud-detection . && docker run --rm -p 8000:8000 email-fraud-detection
