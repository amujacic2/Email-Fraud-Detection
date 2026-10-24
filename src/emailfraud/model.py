"""Train, save, load, and score the fraud classifier."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from .features import FEATURE_NAMES, extract_features, feature_vector, parse_email

DEFAULT_MODEL = Path("models/model.joblib")


class FraudDetector:
    """TF-IDF over text combined with scaled heuristic features -> logistic regression."""

    def __init__(self) -> None:
        self.tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, stop_words="english")
        self.scaler = StandardScaler()
        self.clf = LogisticRegression(max_iter=1000, class_weight="balanced")

    def _text(self, raw: str) -> str:
        subject, body, _ = parse_email(raw)
        return f"{subject} {body}"

    def _matrix(self, emails: list[str], fit: bool = False):
        texts = [self._text(e) for e in emails]
        dense = np.array([feature_vector(e) for e in emails])
        if fit:
            text_part = self.tfidf.fit_transform(texts)
            dense_part = self.scaler.fit_transform(dense)
        else:
            text_part = self.tfidf.transform(texts)
            dense_part = self.scaler.transform(dense)
        return hstack([text_part, csr_matrix(dense_part)]).tocsr()

    def fit(self, emails: list[str], labels: list[int]) -> "FraudDetector":
        self.clf.fit(self._matrix(emails, fit=True), labels)
        return self

    def predict_proba(self, emails: list[str]) -> np.ndarray:
        return self.clf.predict_proba(self._matrix(emails))[:, 1]

    def explain(self, raw: str) -> dict:
        """Score one email and list the heuristic signals that fired."""
        score = float(self.predict_proba([raw])[0])
        feats = extract_features(raw)
        signals = [n for n in FEATURE_NAMES if feats[n] > 0 and n not in ("upper_ratio", "num_urls")]
        return {"score": score, "label": "fraud" if score >= 0.5 else "legitimate", "signals": signals}

    def save(self, path: Path = DEFAULT_MODEL) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path: Path = DEFAULT_MODEL) -> "FraudDetector":
        return joblib.load(path)


def train_from_csv(csv_path: Path, test_size: float = 0.25, seed: int = 42):
    """Train on a CSV with `text` and `label` (1 = fraud) columns; return (model, report)."""
    df = pd.read_csv(csv_path)
    x_train, x_test, y_train, y_test = train_test_split(
        df["text"].tolist(), df["label"].tolist(), test_size=test_size, random_state=seed, stratify=df["label"]
    )
    model = FraudDetector().fit(x_train, y_train)
    preds = (model.predict_proba(x_test) >= 0.5).astype(int)
    report = classification_report(y_test, preds, target_names=["legitimate", "fraud"], zero_division=0)
    return model, report
