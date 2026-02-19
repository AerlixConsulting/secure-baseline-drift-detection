from __future__ import annotations
from datetime import date
from pathlib import Path
import argparse
import json

def main() -> None:
    ap = argparse.ArgumentParser(description="Generate drift report (reference).")
    ap.add_argument("--host", default="web-server-01")
    ap.add_argument("--finding", default="SSH root login enabled")
    ap.add_argument("--severity", default="High")
    args = ap.parse_args()

    report = {
        "generated": date.today().isoformat(),
        "host": args.host,
        "finding": args.finding,
        "severity": args.severity,
        "recommended_action": "Restore baseline setting and verify",
        "verification_required": True,
        "notes": "Synthetic example for portfolio demonstration",
    }

    out_dir = Path("generated")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"drift-report-{report['generated']}.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
