"""Hand-crafted heuristic features that signal phishing or fraud."""

import math
import re
from email import message_from_string
from email.message import Message
from urllib.parse import urlparse

URL_RE = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)
IP_HOST_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "cutt.ly"}
SUSPICIOUS_TLDS = {"xyz", "top", "click", "support", "info", "ru", "tk", "work", "zip"}
RISKY_EXTENSIONS = {
    "exe",
    "scr",
    "js",
    "vbs",
    "bat",
    "cmd",
    "iso",
    "img",
    "jar",
    "msi",
    "html",
    "htm",
    "docm",
    "xlsm",
    "pptm",
    "lnk",
    "hta",
}
BRANDS = ("paypal", "amazon", "netflix", "chase", "microsoft", "apple", "dhl", "google", "facebook")
URGENCY_WORDS = (
    "urgent",
    "immediately",
    "act now",
    "within 24 hours",
    "suspended",
    "verify your account",
    "final notice",
    "expires",
    "limited time",
    "asap",
)
MONEY_WORDS = (
    "wire transfer",
    "gift card",
    "bitcoin",
    "inheritance",
    "lottery",
    "winner",
    "prize",
    "million",
    "payment",
    "invoice",
    "refund",
    "bank account",
)
CREDENTIAL_WORDS = ("password", "login", "ssn", "social security", "pin", "credentials", "otp")
LEET = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s", "4": "a", "$": "s"})
AUTH_FAIL_RE = re.compile(r"\b(spf|dkim|dmarc)=(fail|softfail|none|permerror|temperror)", re.I)

FEATURE_NAMES = [
    "num_urls",
    "has_ip_url",
    "has_shortener",
    "has_suspicious_tld",
    "has_at_in_url",
    "has_punycode",
    "urgency_hits",
    "money_hits",
    "credential_hits",
    "exclaim_count",
    "upper_ratio",
    "reply_to_mismatch",
    "html_form",
    "link_text_mismatch",
    "auth_failures",
    "display_name_spoof",
    "lookalike_domain",
    "risky_attachment",
]
# Features shown to users as human-readable signals (skip raw counts/ratios).
SIGNAL_NAMES = [n for n in FEATURE_NAMES if n not in ("num_urls", "upper_ratio")]


def parse_email(raw: str) -> tuple[str, str, Message]:
    """Return (subject, body, message) from raw RFC822 text or a plain string."""
    msg = message_from_string(raw)
    subject = str(msg.get("Subject", "") or "")
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


def _is_official(host: str, brand: str) -> bool:
    return host == f"{brand}.com" or host.endswith(f".{brand}.com")


def _lookalike(hosts: list[str]) -> bool:
    """True if a host imitates a known brand without being its official domain."""
    for host in hosts:
        if not host or IP_HOST_RE.match(host):
            continue
        labels = re.split(r"[.-]", host.translate(LEET))
        for brand in BRANDS:
            if any(label.startswith(brand) for label in labels) and not _is_official(host, brand):
                return True
    return False


def _display_name_spoof(from_header: str) -> bool:
    name = re.sub(r"<[^>]*>", "", from_header or "").strip(" \"'").lower()
    dom = _domain(from_header)
    if not name or not dom:
        return False
    return any(b in name and not _is_official(dom, b) for b in BRANDS)


def _risky_attachment(msg: Message) -> bool:
    for part in msg.walk():
        name = (part.get_filename() or "").lower()
        if not name:
            continue
        pieces = name.split(".")
        ext = pieces[-1]
        if ext in RISKY_EXTENSIONS or (len(pieces) > 2 and ext in ("exe", "scr", "js", "vbs")):
            return True
    return False


def extract_features(raw: str) -> dict[str, float]:
    """Compute heuristic features for a raw email (headers optional)."""
    subject, body, msg = parse_email(raw)
    text = f"{subject}\n{body}"
    lower = text.lower()
    urls = URL_RE.findall(text)
    hosts = [(urlparse(u).hostname or "").lower() for u in urls]

    letters = [c for c in text if c.isalpha()]
    upper_ratio = sum(c.isupper() for c in letters) / len(letters) if letters else 0.0

    from_header = str(msg.get("From", ""))
    from_dom = _domain(from_header)
    reply_dom = _domain(str(msg.get("Reply-To", "")))

    mismatch = 0
    for m in re.finditer(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", text, re.I | re.S):
        href_host = (urlparse(m.group(1)).hostname or "").lower()
        shown = re.search(r"([\w-]+\.)+[a-z]{2,}", m.group(2), re.I)
        if shown and href_host and shown.group(0).lower() not in href_host:
            mismatch = 1

    auth_failures = len(AUTH_FAIL_RE.findall(" ".join(msg.get_all("Authentication-Results", []) or [])))

    return {
        "num_urls": float(len(urls)),
        "has_ip_url": float(any(IP_HOST_RE.match(h) for h in hosts)),
        "has_shortener": float(any(h in SHORTENERS for h in hosts)),
        "has_suspicious_tld": float(any(h.rsplit(".", 1)[-1] in SUSPICIOUS_TLDS for h in hosts if "." in h)),
        "has_at_in_url": float(any("@" in u for u in urls)),
        "has_punycode": float(any("xn--" in h for h in hosts) or "xn--" in from_dom),
        "urgency_hits": float(_count(lower, URGENCY_WORDS)),
        "money_hits": float(_count(lower, MONEY_WORDS)),
        "credential_hits": float(_count(lower, CREDENTIAL_WORDS)),
        "exclaim_count": float(text.count("!")),
        "upper_ratio": upper_ratio,
        "reply_to_mismatch": float(bool(from_dom and reply_dom and from_dom != reply_dom)),
        "html_form": float("<form" in lower),
        "link_text_mismatch": float(mismatch),
        "auth_failures": float(auth_failures),
        "display_name_spoof": float(_display_name_spoof(from_header)),
        "lookalike_domain": float(_lookalike(hosts + ([from_dom] if from_dom else []))),
        "risky_attachment": float(_risky_attachment(msg)),
    }


def rule_score(feats: dict[str, float]) -> float:
    """Transparent rule-based risk in [0, 1] from weighted signals (no training needed)."""
    raw = (
        1.5 * feats["has_ip_url"]
        + 1.5 * feats["lookalike_domain"]
        + 1.5 * feats["risky_attachment"]
        + 1.2 * feats["display_name_spoof"]
        + 1.2 * feats["link_text_mismatch"]
        + 1.2 * feats["has_punycode"]
        + 1.0 * feats["has_at_in_url"]
        + 0.8 * min(feats["auth_failures"], 2)
        + 0.7 * feats["reply_to_mismatch"]
        + 0.6 * (feats["has_shortener"] + feats["has_suspicious_tld"] + feats["html_form"])
        + 0.5 * min(feats["urgency_hits"], 2)
        + 0.4 * min(feats["money_hits"], 2)
        + 0.4 * min(feats["credential_hits"], 1)
        + 0.3 * float(feats["exclaim_count"] >= 3)
    )
    return 1.0 - math.exp(-raw / 2.5)


def feature_vector(raw: str) -> list[float]:
    feats = extract_features(raw)
    return [feats[name] for name in FEATURE_NAMES]
