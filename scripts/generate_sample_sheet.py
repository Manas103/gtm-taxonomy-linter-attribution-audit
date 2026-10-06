"""Writes data/launch_sheet.csv, a small, genuinely clean example campaign
launch sheet, used as the CI linting demonstration. Re-run to regenerate it
exactly (fixed seed)."""
from __future__ import annotations

import csv
from pathlib import Path

from tracking_audit.launch_sheet import build_valid_rows
from tracking_audit.registry import build_registry

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "launch_sheet.csv"
SEED = 20260705


def main() -> int:
    registry = build_registry()
    rows = build_valid_rows(SEED, registry, n=20)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["row_id", "url"])
        for row in rows:
            writer.writerow([row.row_id, row.url])
    print(f"wrote {len(rows)} rows to {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
