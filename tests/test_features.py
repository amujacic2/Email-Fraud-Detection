from emailfraud.features import extract_features

PHISH = (
    "From: security@paypal-alerts.xyz\nReply-To: help@evil.ru\n"
    "Subject: URGENT: account suspended\n\n"
    "Verify your account immediately at http://192.168.4.4/login and enter your password!!!"
)
HAM = "From: sam@company.com\nSubject: Lunch\n\nHey, are you free for lunch tomorrow?"


def test_phishing_signals_fire():
    f = extract_features(PHISH)
    assert f["has_ip_url"] == 1
    assert f["urgency_hits"] >= 2
    assert f["credential_hits"] >= 1
    assert f["reply_to_mismatch"] == 1
    assert f["exclaim_count"] == 3


def test_legitimate_email_is_quiet():
    f = extract_features(HAM)
    assert f["num_urls"] == 0
    assert f["urgency_hits"] == 0
    assert f["reply_to_mismatch"] == 0


def test_link_text_mismatch_detected():
    raw = 'Subject: Hi\n\n<a href="http://evil.example.top/x">www.paypal.com</a>'
    f = extract_features(raw)
    assert f["link_text_mismatch"] == 1
    assert f["has_suspicious_tld"] == 1
