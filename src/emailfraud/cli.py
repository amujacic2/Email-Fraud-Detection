"""Command line interface: train a model or scan emails."""

import argparse
import json
import sys
from pathlib import Path

from .model import DEFAULT_MODEL, FraudDetector, train_from_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="emailfraud", description="Email fraud detection")
    sub = parser.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("train", help="train a model from a CSV (columns: text,label)")
    t.add_argument("--data", type=Path, default=Path("data/emails.csv"))
    t.add_argument("--out", type=Path, default=DEFAULT_MODEL)

    s = sub.add_parser("scan", help="score one or more .eml/.txt files (or '-' for stdin)")
    s.add_argument("files", nargs="+")
    s.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    s.add_argument("--json", action="store_true", help="emit JSON")

    args = parser.parse_args(argv)

    if args.cmd == "train":
        model, report = train_from_csv(args.data)
        model.save(args.out)
        print(report)
        print(f"Model saved to {args.out}")
        return 0

    model = FraudDetector.load(args.model)
    results = []
    for f in args.files:
        raw = sys.stdin.read() if f == "-" else Path(f).read_text(encoding="utf-8", errors="replace")
        results.append({"file": f, **model.explain(raw)})
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            signals = ", ".join(r["signals"]) or "none"
            print(f"{r['file']}: {r['label'].upper()} (score {r['score']:.2f}) signals: {signals}")
    return 1 if any(r["label"] == "fraud" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
