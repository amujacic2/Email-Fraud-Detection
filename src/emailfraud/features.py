"""Hand-crafted heuristic features that signal phishing or fraud."""

import re
from email import message_from_string
from email.message import Message
from urllib.parse import urlparse

URL_RE = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)
IP_HOST_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "cutt.ly"}
SUSPICIOUS_TLDS = {"xyz", "top", "click", "support", "info", "ru", "tk", "work", "zip"}
URGENCY_WORDS = (
    "urgent", "immediately", "act now", "within 24 hours", "suspended",
    "verify your account", "final notice", "expires", "limited time", "asap",
)
MONEY_WORDS = (
    "wire transfer", "gift card", "bitcoin", "inheritance", "lottery", "winner",
    "prize", "million", "payment", "invoice", "refund", "bank account",
)
CREDENTIAL_WORDS = ("password", "login", "ssn", "social security", "pin", "credentials", "otp")

FEATURE_NAMES = [
    "num_urls", "has_ip_url", "has_shortener", "has_suspicious_tld", "has_at_in_url",
    "urgency_hits", "money_hits", "credential_hits", "exclaim_count",
    "upper_ratio", "reply_to_mismatch", "html_form", "link_text_mismatch",
]


def parse_email(raw: str) -> tuple[str, str, Message]:
    """Return (subject, body, message) from raw RFC822 text or a plain string."""
    msg = message_from_string(raw)
    subject = msg.get("Subject", "") or ""
    if msg.is_multipart():
        parts = []
        for p in msg.walk():
            if p.get_content_type() in ("text/plain", "text/html"):
                payload = p.get_payload(decode=True)
                if payload is not None:
                    parts.append(payload.decode(p.get_content_charset() or "utf-8", "replace"))
        body = "\n".join(parts)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode(msg.get_content_charset() or "utf-8", "replace")
        else:
            body = str(msg.get_payload())
    return subject, body, msg


def _domain(addr: str) -> str:
    m = re.search(r"@([\w.-]+)", addr or "")
    return m.group(1).lower() if m else ""


def _count(text: str, words: tuple[str, ...]) -> int:
    return sum(text.count(w) for w in words)


def extract_features(raw: str) -> dict[str, float]:
    """Compute heuristic features for a raw email (headers optional)."""
    subject, body, msg = parse_email(raw)
    text = f"{subject}\n{body}"
    lower = text.lower()
    urls = URL_RE.findall(text)
    hosts = [(urlparse(u).hostname or "").lower() for u in urls]

    letters = [c for c in text if c.isalpha()]
    upper_ratio = sum(c.isupper() for c in letters) / len(letters) if letters else 0.0

    from_dom = _domain(msg.get("From", ""))
    reply_dom = _domain(msg.get("Reply-To", ""))

    mismatch = 0
    for m in re.finditer(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", text, re.I | re.S):
        href_host = (urlparse(m.group(1)).hostname or "").lower()
        shown = re.search(r"([\w-]+\.)+[a-z]{2,}", m.group(2), re.I)
        if shown and href_host and shown.group(0).lower() not in href_host:
            mismatch = 1

    return {
        "num_urls": float(len(urls)),
        "has_ip_url": float(any(IP_HOST_RE.match(h) for h in hosts)),
        "has_shortener": float(any(h in SHORTENERS for h in hosts)),
        "has_suspicious_tld": float(any(h.rsplit(".", 1)[-1] in SUSPICIOUS_TLDS for h in hosts if "." in h)),
        "has_at_in_url": float(any("@" in u for u in urls)),
        "urgency_hits": float(_count(lower, URGENCY_WORDS)),
        "money_hits": float(_count(lower, MONEY_WORDS)),
        "credential_hits": float(_count(lower, CREDENTIAL_WORDS)),
        "exclaim_count": float(text.count("!")),
        "upper_ratio": upper_ratio,
        "reply_to_mismatch": float(bool(from_dom and reply_dom and from_dom != reply_dom)),
        "html_form": float("<form" in lower),
        "link_text_mismatch": float(mismatch),
    }


def feature_vector(raw: str) -> list[float]:
    feats = extract_features(raw)
    return [feats[name] for name in FEATURE_NAMES]
