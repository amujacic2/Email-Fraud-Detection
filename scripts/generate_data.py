"""Generate a synthetic labelled email dataset (data/emails.csv).

Emails are composed from varied building blocks (greeting, scam story, ask, closer, optional
headers/links) so the classifier cannot simply memorise a handful of templates. The data still
contains hard cases: legitimate mail that sounds urgent or mentions money, and subtle fraud with
a calm tone. It is synthetic and for demonstration only: for real use, swap in a genuine corpus
(e.g. Enron + Nazario phishing) with the same `text,label` columns.
"""

import csv
import random
from pathlib import Path

random.seed(7)

BRANDS = ["PayPal", "Amazon", "Netflix", "Chase", "Microsoft", "Apple", "DHL"]
NAMES = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Dana", "Chris"]
TOPICS = ["Q3 budget", "project roadmap", "team offsite", "hiring plan", "release notes", "design review"]
FAIL = "Authentication-Results: mx.example.net; spf=fail; dkim=none; dmarc=fail\n"
PASS = "Authentication-Results: mx.example.net; spf=pass; dkim=pass; dmarc=pass\n"

F_GREET = [
    "Dear customer,",
    "Dear friend,",
    "Dear Sir/Madam,",
    "Hello,",
    "Attention beneficiary,",
    "Greetings,",
    "Dear valued member,",
    "Hi,",
    "Dear account holder,",
    "Congratulations!",
    "",
]
F_CLOSE = [
    "Act now!",
    "Reply urgently.",
    "Thank you for your cooperation.",
    "Do not tell anyone.",
    "Regards, Support Team",
    "God bless you.",
    "Respond within 24 hours or the offer expires.",
    "Kindly confirm receipt.",
    "",
    "Best regards,\nSecurity Department",
]
F_CTA = [
    "Click here: {url}",
    "Follow this link to continue: {url}",
    "Verify now at {url}",
    "Log in at {url}",
    "",
    "",
]
F_ASK = [
    "Reply with your full name, date of birth and bank details.",
    "Send your account number and password to confirm your identity.",
    "Please provide your social security number and a copy of your ID.",
    "Confirm your card number and CVV to proceed.",
    "Kindly send your full name and address so we can process this.",
    "Enter your login credentials to restore access.",
    "",
]
# Scam stories: (subject, body)
F_STORY = [
    (
        "Tax refund waiting",
        "We noticed an error in your tax return. You are owed a refund of ${amt}. It will be deposited once verified.",
    ),
    (
        "Account locked",
        "Your {B} account has been locked due to suspicious activity. Unlock it to avoid permanent suspension.",
    ),
    (
        "Business proposal",
        "I am Prince {N} from Nigeria. I have ${amt2} million to transfer out of the country and need a trusted partner. You will receive 30 percent.",
    ),
    (
        "Work from home",
        "You have been selected for a work from home job earning ${amt} weekly. No experience needed. Start today.",
    ),
    (
        "Quick task",
        "Are you at your desk? I need you to do a quick task for me. Reply as soon as you see this. I am in a meeting and cannot talk.",
    ),
    (
        "Double your Bitcoin",
        "Double your Bitcoin in 24 hours. Guaranteed returns. Send 0.5 BTC to our wallet and receive 1 BTC back.",
    ),
    (
        "Package not delivered",
        "Your package could not be delivered. Pay a $1.99 redelivery fee to reschedule.",
    ),
    (
        "Inheritance claim",
        "A late client of mine died leaving ${amt2} million dollars with no next of kin. As a beneficiary you can claim the inheritance. Keep this confidential.",
    ),
    ("You won!", "You have won a free iPhone in our monthly draw. Claim your prize now before it expires."),
    (
        "Lottery winner",
        "Your email was selected as the winner of the international lottery, ${amt2} million dollars. A small processing fee by gift card is required.",
    ),
    (
        "Invoice overdue",
        "Your payment failed and your invoice is overdue. Update your payment method immediately to avoid legal action.",
    ),
    (
        "Security alert",
        "Unusual sign-in detected on your account. Your password may be compromised. Verify your account immediately.",
    ),
    (
        "Change of bank details",
        "Please note our change of bank details. Wire transfer the outstanding invoice today and keep this private.",
    ),
    (
        "Virus detected",
        "Viruses detected: your computer is infected. Call support or click the link to remove them now.",
    ),
    (
        "Charity request",
        "I am dying of cancer and want to donate my fortune of ${amt2} million to you. Please send your bank account details.",
    ),
    (
        "Your {B} receipt",
        "Thanks for your order. Review the details of your purchase here. If you did not make this purchase please sign in.",
    ),
]
F_HEAD = [
    "",
    "",
    "From: security@{b}-alerts.{tld}\nReply-To: support@mail-{tld}.ru\n" + FAIL,
    'From: "{B} Support" <service@{b}-secure.{tld}>\n' + FAIL,
    "From: lottery@free-{tld}.com\nReply-To: claims@gmail.com\n",
    "From: ceo@company-mail.{tld}\nReply-To: ceo.private@gmail.com\n",
    "From: hr@c0mpany.com\n" + FAIL,
]

L_HEAD = [
    "From: {n1}@company.com\n" + PASS,
    "From: {n1}@company.com\n",
    "",
    "From: hr@company.com\n" + PASS,
    "From: noreply@github.com\n" + PASS,
    "From: {n1}@university.edu\n" + PASS,
    "From: mom@family.net\n",
]
L_BODY = [
    (
        "Notes from the {t} meeting",
        "Hi team, attached are the notes from today's {t} discussion. Let me know if I missed anything and we can review on Thursday.",
    ),
    (
        "Lunch tomorrow?",
        "Hey {N2}, are you free for lunch tomorrow around noon? There is a new place near the office.",
    ),
    ("Meeting moved", "Hi {N2}, can we move our meeting to 3pm tomorrow? Thanks, {N1}"),
    (
        "Pull request merged",
        "Your pull request has been merged into main. View it at https://github.com/org/repo/pull/{n}.",
    ),
    (
        "Updated {t} schedule",
        "Please find the updated schedule for the {t}. Calendar invites will follow shortly. Thanks, {N1}.",
    ),
    (
        "Re: question about the assignment",
        "Thanks for your question, {N2}. The deadline is next Friday and office hours are Tuesday afternoon.",
    ),
    (
        "URGENT: scheduled maintenance tonight",
        "Our servers will be down immediately after 10pm for maintenance. Please save your work. Status: https://status.company.com/incidents/{n}",
    ),
    (
        "Your Amazon order has shipped",
        "Your payment was processed and your package is on the way. Track it at https://www.amazon.com/progress/{n}. Thanks!",
    ),
    (
        "Your invoice is ready",
        "Your monthly invoice for {t} is available. Sign in at https://account.microsoft.com to download it.",
    ),
    (
        "Expense refund approved",
        "Hi {N2}, your refund for the offsite was approved and will arrive with the next payment run. No action needed.",
    ),
    ("Sunday dinner", "Can you bring dessert on Sunday? Love you! Mom"),
    (
        "Quick question",
        "Hey, quick question about the {t}. Do you have a minute to chat this afternoon? Thanks.",
    ),
    (
        "Happy birthday!",
        "Happy birthday {N2}! Hope you have a wonderful day. We are all getting cake at 3pm!",
    ),
    (
        "Password reset requested",
        "You asked to reset your password for your account. If this was you, use the link: https://accounts.google.com/reset/{n}. If not, ignore this email.",
    ),
    (
        "Bank statement available",
        "Your monthly statement is ready. Sign in to the Chase app to view it. We will never ask for your password by email.",
    ),
    (
        "Interview schedule",
        "Hi {N2}, we would like to schedule your interview for the {t} role next Tuesday. Please reply with your availability.",
    ),
    (
        "Conference invite",
        "You are invited to our annual conference. Registration is free and details are on the website. Hope to see you there, {N1}.",
    ),
    (
        "Wire confirmation",
        "Hi {N2}, the wire for the {t} vendor invoice went out today as agreed with finance. Receipt attached.",
    ),
]


def ctx() -> dict:
    b = random.choice(BRANDS)
    return dict(
        b=b.lower(),
        B=b,
        tld=random.choice(["xyz", "top", "click", "ru", "info", "com", "net"]),
        ip=".".join(str(random.randint(11, 250)) for _ in range(4)),
        n=random.randint(100, 999),
        n1=random.choice(NAMES).lower(),
        N1=random.choice(NAMES),
        N2=random.choice(NAMES),
        N=random.choice(NAMES),
        t=random.choice(TOPICS),
        amt=f"{random.randint(1, 9)},{random.randint(100, 999)}",
        amt2=random.randint(2, 40),
    )


def fraud() -> str:
    c = ctx()
    c["url"] = random.choice(
        [
            f"http://{c['ip']}/login",
            f"http://bit.ly/3x{c['n']}",
            f"http://{c['b']}-secure.{c['tld']}/verify",
            f"https://{c['b']}.com-verify.{c['tld']}/a",
        ]
    )
    subj, story = random.choice(F_STORY)
    parts = [
        random.choice(F_GREET),
        story,
        random.choice(F_ASK),
        random.choice(F_CTA),
        random.choice(F_CLOSE),
    ]
    body = "\n".join(p for p in parts if p)
    return (random.choice(F_HEAD) + "Subject: " + subj + "\n\n" + body + "\n").format(**c)


def legit() -> str:
    c = ctx()
    subj, body = random.choice(L_BODY)
    return (random.choice(L_HEAD) + "Subject: " + subj + "\n\n" + body + "\n").format(**c)


def main() -> None:
    rows = [(fraud(), 1) for _ in range(600)] + [(legit(), 0) for _ in range(600)]
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
