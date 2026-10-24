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
    assert f["lookalike_domain"] == 0


def test_link_text_mismatch_detected():
    raw = 'Subject: Hi\n\n<a href="http://evil.example.top/x">www.paypal.com</a>'
    f = extract_features(raw)
    assert f["link_text_mismatch"] == 1
    assert f["has_suspicious_tld"] == 1


def test_auth_failures_counted():
    raw = "From: a@b.com\nAuthentication-Results: mx; spf=fail; dkim=pass; dmarc=fail\nSubject: x\n\nhi"
    assert extract_features(raw)["auth_failures"] == 2


def test_display_name_spoof():
    spoof = 'From: "PayPal Support" <help@random-host.net>\nSubject: x\n\nhi'
    real = 'From: "PayPal" <service@paypal.com>\nSubject: x\n\nhi'
    assert extract_features(spoof)["display_name_spoof"] == 1
    assert extract_features(real)["display_name_spoof"] == 0


def test_lookalike_domain_leet_and_hyphen():
    assert extract_features("Subject: x\n\nsee http://paypa1.com/login")["lookalike_domain"] == 1
    assert extract_features("Subject: x\n\nsee http://paypal-secure.xyz/a")["lookalike_domain"] == 1
    assert extract_features("Subject: x\n\nsee https://www.paypal.com/help")["lookalike_domain"] == 0
    assert extract_features("Subject: x\n\nsee https://shop.purchase.com/a")["lookalike_domain"] == 0


def test_punycode_and_risky_attachment():
    assert extract_features("Subject: x\n\nhttp://xn--pypal-4ve.com/")["has_punycode"] == 1
    raw = (
        "Subject: invoice\nMIME-Version: 1.0\nContent-Type: multipart/mixed; boundary=B\n\n"
        "--B\nContent-Type: text/plain\n\nsee attached\n"
        "--B\nContent-Type: application/octet-stream\n"
        'Content-Disposition: attachment; filename="invoice.pdf.exe"\n\nMZ\n--B--\n'
    )
    assert extract_features(raw)["risky_attachment"] == 1
