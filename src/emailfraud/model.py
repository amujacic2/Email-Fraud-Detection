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

from .features import SIGNAL_NAMES, extract_features, feature_vector, parse_email, rule_score

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

    def ml_proba(self, emails: list[str]) -> np.ndarray:
        """Probability from the trained text + feature model alone."""
        return self.clf.predict_proba(self._matrix(emails))[:, 1]

    def predict_proba(self, emails: list[str]) -> np.ndarray:
        """Hybrid score: noisy-OR of the ML probability and the transparent rule score.

        The rules keep obvious attacks flagged even when the training data is small or
        narrow; the ML model adds vocabulary the rules do not know about.
        """
        ml = self.ml_proba(emails)
        rules = np.array([rule_score(extract_features(e)) for e in emails])
        return 1.0 - (1.0 - ml) * (1.0 - rules)

    def explain(self, raw: str) -> dict:
        """Score one email and list the heuristic signals that fired."""
        ml = float(self.ml_proba([raw])[0])
        feats = extract_features(raw)
        rules = rule_score(feats)
        score = 1.0 - (1.0 - ml) * (1.0 - rules)
        signals = [n for n in SIGNAL_NAMES if feats[n] > 0]
        risk = "high" if score >= 0.8 else "medium" if score >= 0.5 else "low"
        return {
            "score": score,
            "label": "fraud" if score >= 0.5 else "legitimate",
            "risk": risk,
            "signals": signals,
            "ml_score": ml,
            "rule_score": rules,
        }

    def save(self, path: Path = DEFAULT_MODEL) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path: Path = DEFAULT_MODEL) -> "FraudDetector":
        return joblib.load(path)


def cross_validate(csv_path: Path, folds: int = 5, seed: int = 42) -> dict[str, float]:
    """Stratified k-fold cross-validation; returns mean precision, recall, F1 and ROC-AUC."""
    from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
    from sklearn.model_selection import StratifiedKFold

    df = pd.read_csv(csv_path)
    texts, labels = df["text"].tolist(), np.array(df["label"].tolist())
    scores: dict[str, list[float]] = {"precision": [], "recall": [], "f1": [], "roc_auc": []}
    for tr, te in StratifiedKFold(folds, shuffle=True, random_state=seed).split(texts, labels):
        model = FraudDetector().fit([texts[i] for i in tr], labels[tr].tolist())
        proba = model.predict_proba([texts[i] for i in te])
        pred = (proba >= 0.5).astype(int)
        scores["precision"].append(precision_score(labels[te], pred, zero_division=0))
        scores["recall"].append(recall_score(labels[te], pred, zero_division=0))
        scores["f1"].append(f1_score(labels[te], pred, zero_division=0))
        scores["roc_auc"].append(roc_auc_score(labels[te], proba))
    return {k: float(np.mean(v)) for k, v in scores.items()}


def train_from_csv(csv_path: Path, test_size: float = 0.25, seed: int = 42):
    """Train on a CSV with `text` and `label` (1 = fraud) columns; return (model, report)."""
    df = pd.read_csv(csv_path)
    x_train, x_test, y_train, y_test = train_test_split(
        df["text"].tolist(),
        df["label"].tolist(),
        test_size=test_size,
        random_state=seed,
        stratify=df["label"],
    )
    model = FraudDetector().fit(x_train, y_train)
    preds = (model.predict_proba(x_test) >= 0.5).astype(int)
    report = classification_report(y_test, preds, target_names=["legitimate", "fraud"], zero_division=0)
    return model, report
