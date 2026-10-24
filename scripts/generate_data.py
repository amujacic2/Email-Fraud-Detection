"""Generate a synthetic labelled email dataset (data/emails.csv).

The data is template-based and for demonstration only. Swap in a real corpus
(e.g. Enron + Nazario phishing) with the same `text,label` columns for real use.
"""

import csv
import random
from pathlib import Path

random.seed(7)

BRANDS = ["PayPal", "Amazon", "Netflix", "Chase Bank", "Microsoft", "Apple", "DHL"]
NAMES = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley"]
TOPICS = ["Q3 budget", "project roadmap", "team offsite", "hiring plan", "release notes", "design review"]

FRAUD = [
    ("security@{b}-alerts.{tld}", "support@mail-{tld}.ru",
     "URGENT: your {b} account has been suspended",
     "Dear customer, your account will be closed within 24 hours. Verify your account immediately: "
     "http://{ip}/login/{b}?id=88 . Enter your password and credentials to restore access!!!"),
    ("lottery@{tld}.com", "claims@free-{tld}.com",
     "You are a WINNER of the international lottery",
     "Congratulations! You won 5 million dollars. To claim your prize send your bank account details "
     "and a small processing fee by gift card or bitcoin. Act now, limited time!"),
    ("ceo@company-mail.{tld}", "ceo.private@gmail.com",
     "Quick favor needed ASAP",
     "I am in a meeting and cannot talk. Please buy 5 gift card codes and send me the numbers immediately. "
     "I will refund you today. Do not tell anyone."),
    ("billing@{b}.com", "billing@{b}-pay.{tld}",
     "Final notice: unpaid invoice",
     "<html><body>Your payment failed. <a href=\"http://bit.ly/3x{n}\">www.{b}.com/billing</a> "
     "<form action=\"http://{ip}/pay\"><input name=\"pin\"></form> Update your login and PIN now.</body></html>"),
    ("prince@royal-{tld}.com", "prince@royal-{tld}.com",
     "Confidential business proposal - inheritance transfer",
     "I am the legal counsel of a late client with an inheritance of 12 million. I need your help with a "
     "wire transfer and your social security number to release the funds. Reply urgent."),
]

LEGIT = [
    ("{n1}@company.com", "{n1}@company.com", "Notes from the {t} meeting",
     "Hi team, attached are the notes from today's {t} discussion. Let me know if I missed anything and "
     "we can review it on Thursday."),
    ("{n1}@company.com", "{n1}@company.com", "Lunch tomorrow?",
     "Hey {n2}, are you free for lunch tomorrow around noon? There is a new place near the office."),
    ("noreply@github.com", "noreply@github.com", "[repo] Pull request merged",
     "Your pull request has been merged into main. View it at https://github.com/org/repo/pull/{n}."),
    ("hr@company.com", "hr@company.com", "Updated {t} schedule",
     "Please find the updated schedule for the {t}. Calendar invites will follow shortly. Thanks, {n1}."),
    ("{n1}@university.edu", "{n1}@university.edu", "Re: question about the assignment",
     "Thanks for your question, {n2}. The deadline is next Friday and office hours are Tuesday afternoon."),
]


def render(tpl: tuple) -> str:
    frm, reply, subj, body = tpl
    ctx = dict(
        b=random.choice(BRANDS).lower().replace(" ", ""),
        tld=random.choice(["xyz", "top", "click", "ru", "info"]),
        ip=".".join(str(random.randint(11, 250)) for _ in range(4)),
        n=random.randint(100, 999),
        n1=random.choice(NAMES).lower(),
        n2=random.choice(NAMES),
        t=random.choice(TOPICS),
    )
    fmt = lambda s: s.format(**ctx)
    return f"From: {fmt(frm)}\nReply-To: {fmt(reply)}\nSubject: {fmt(subj)}\n\n{fmt(body)}\n"


def main() -> None:
    rows = [(render(random.choice(FRAUD)), 1) for _ in range(150)]
    rows += [(render(random.choice(LEGIT)), 0) for _ in range(150)]
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
