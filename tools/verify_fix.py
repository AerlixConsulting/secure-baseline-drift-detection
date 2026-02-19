from __future__ import annotations
from datetime import date
from pathlib import Path
import argparse

def main() -> None:
    ap = argparse.ArgumentParser(description="Create verification record (reference).")
    ap.add_argument("--finding", required=True)
    ap.add_argument("--method", default="Configuration check + service restart validation")
    ap.add_argument("--verifier", default="Security Officer")
    args = ap.parse_args()

    content = f"""Verification Record (Generated)

Date: {date.today().isoformat()}
Finding: {args.finding}
Verification Method: {args.method}
Verifier: {args.verifier}
Result: Verified (reference)
"""
    out_dir = Path("generated")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"verification-{date.today().isoformat()}.md"
    out_path.write_text(content, encoding="utf-8")
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
