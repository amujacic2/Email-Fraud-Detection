"""Generate a synthetic labelled email dataset (data/emails.csv).

The data is template-based and for demonstration only. It includes hard cases:
legitimate mail that sounds urgent or contains links, and subtle fraud with no
scary keywords (only a lookalike domain or failed authentication). Swap in a real
corpus (e.g. Enron + Nazario phishing) with the same `text,label` columns for real use.
"""

import csv
import random
from pathlib import Path

random.seed(7)

BRANDS = ["PayPal", "Amazon", "Netflix", "Chase", "Microsoft", "Apple", "DHL"]
NAMES = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley"]
TOPICS = ["Q3 budget", "project roadmap", "team offsite", "hiring plan", "release notes", "design review"]
FAIL = "Authentication-Results: mx.example.net; spf=fail; dkim=none; dmarc=fail\n"
PASS = "Authentication-Results: mx.example.net; spf=pass; dkim=pass; dmarc=pass\n"

# (headers, subject, body)
FRAUD = [
    (
        "From: security@{b}-alerts.{tld}\nReply-To: support@mail-{tld}.ru\n" + FAIL,
        "URGENT: your {B} account has been suspended",
        "Dear customer, your account will be closed within 24 hours. Verify your account immediately: "
        "http://{ip}/login/{b}?id=88 . Enter your password and credentials to restore access!!!",
    ),
    (
        "From: lottery@{tld}.com\nReply-To: claims@free-{tld}.com\n",
        "You are a WINNER of the international lottery",
        "Congratulations! You won 5 million dollars. To claim your prize send your bank account details "
        "and a small processing fee by gift card or bitcoin. Act now, limited time!",
    ),
    (
        'From: "{B} Support" <ceo@company-mail.{tld}>\nReply-To: ceo.private@gmail.com\n',
        "Quick favor needed ASAP",
        "I am in a meeting and cannot talk. Please buy 5 gift card codes and send me the numbers immediately. "
        "I will refund you today. Do not tell anyone.",
    ),
    (
        "From: billing@{b}-pay.{tld}\n" + FAIL,
        "Final notice: unpaid invoice",
        '<html><body>Your payment failed. <a href="http://bit.ly/3x{n}">www.{b}.com/billing</a> '
        '<form action="http://{ip}/pay"><input name="pin"></form> Update your login and PIN now.</body></html>',
    ),
    (
        "From: prince@royal-{tld}.com\n",
        "Confidential business proposal - inheritance transfer",
        "I am the legal counsel of a late client with an inheritance of 12 million. I need your help with a "
        "wire transfer and your social security number to release the funds. Reply urgent.",
    ),
    # Subtle: calm tone, only a lookalike domain + failed auth.
    (
        'From: "{B}" <service@{b}-secure.{tld}>\n' + FAIL,
        "Your {B} receipt",
        "Thanks for your order. You can review the details of your purchase here: https://{b}-secure.{tld}/orders/{n}. "
        "If you did not make this purchase please sign in to review.",
    ),
    (
        "From: hr@c0mpany.com\n" + FAIL,
        "Updated {t} document",
        "Please review the attached {t} document before our call. Open the file and sign in with your company account.",
    ),
]

LEGIT = [
    (
        "From: {n1}@company.com\n" + PASS,
        "Notes from the {t} meeting",
        "Hi team, attached are the notes from today's {t} discussion. Let me know if I missed anything and "
        "we can review it on Thursday.",
    ),
    (
        "From: {n1}@company.com\n" + PASS,
        "Lunch tomorrow?",
        "Hey {N2}, are you free for lunch tomorrow around noon? There is a new place near the office.",
    ),
    (
        "From: noreply@github.com\n" + PASS,
        "[repo] Pull request merged",
        "Your pull request has been merged into main. View it at https://github.com/org/repo/pull/{n}.",
    ),
    (
        "From: hr@company.com\n" + PASS,
        "Updated {t} schedule",
        "Please find the updated schedule for the {t}. Calendar invites will follow shortly. Thanks, {N1}.",
    ),
    (
        "From: {n1}@university.edu\n" + PASS,
        "Re: question about the assignment",
        "Thanks for your question, {N2}. The deadline is next Friday and office hours are Tuesday afternoon.",
    ),
    # Hard negatives: urgent tone, links, money words, real brands.
    (
        "From: it@company.com\n" + PASS,
        "URGENT: scheduled maintenance tonight",
        "Our servers will be down immediately after 10pm for maintenance. Please save your work. "
        "Status page: https://status.company.com/incidents/{n}",
    ),
    (
        'From: "Amazon" <order-update@amazon.com>\n' + PASS,
        "Your Amazon order has shipped",
        "Your payment was processed and your package is on the way. Track it at https://www.amazon.com/progress/{n}. Thanks!",
    ),
    (
        "From: billing@microsoft.com\n" + PASS,
        "Your invoice is ready",
        "Your monthly invoice for {t} is available. Sign in at https://account.microsoft.com to download it.",
    ),
    (
        "From: {n1}@company.com\n" + PASS,
        "Reminder: expense refund approved",
        "Hi {N2}, your refund for the offsite was approved and will arrive with the next payment run. No action needed.",
    ),
]


def render(tpl: tuple) -> str:
    headers, subj, body = tpl
    b = random.choice(BRANDS)
    ctx = dict(
        b=b.lower(),
        B=b,
        tld=random.choice(["xyz", "top", "click", "ru", "info", "com", "net"]),
        ip=".".join(str(random.randint(11, 250)) for _ in range(4)),
        n=random.randint(100, 999),
        n1=random.choice(NAMES).lower(),
        N1=random.choice(NAMES),
        N2=random.choice(NAMES),
        t=random.choice(TOPICS),
    )
    text = headers + "Subject: " + subj + "\n\n" + body + "\n"
    return text.format(**ctx)


def main() -> None:
    rows = [(render(random.choice(FRAUD)), 1) for _ in range(300)]
    rows += [(render(random.choice(LEGIT)), 0) for _ in range(300)]
    random.shuffle(rows)
    out = Path(__file__).resolve().parent.parent / "data" / "emails.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["text", "label"])
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
