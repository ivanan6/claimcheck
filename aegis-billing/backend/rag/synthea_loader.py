"""Lightweight readers for the local Synthea CSV sample."""
from __future__ import annotations

import csv
from pathlib import Path


_BACKEND_DIR = Path(__file__).resolve().parents[1]
_PROJECT_DIR = _BACKEND_DIR.parent
_SYNTHEA_DIR = _PROJECT_DIR / "data" / "synthea_csv"


def _count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def synthea_summary() -> dict:
    files = {
        "patients": _SYNTHEA_DIR / "patients.csv",
        "encounters": _SYNTHEA_DIR / "encounters.csv",
        "conditions": _SYNTHEA_DIR / "conditions.csv",
        "procedures": _SYNTHEA_DIR / "procedures.csv",
        "claims": _SYNTHEA_DIR / "claims.csv",
        "payers": _SYNTHEA_DIR / "payers.csv",
    }
    return {
        "path": str(_SYNTHEA_DIR.relative_to(_PROJECT_DIR)),
        "files_present": {name: path.exists() for name, path in files.items()},
        "row_counts": {name: _count_rows(path) for name, path in files.items()},
    }


def sample_patients(limit: int = 5) -> list[dict]:
    path = _SYNTHEA_DIR / "patients.csv"
    if not path.exists():
        return []

    patients: list[dict] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            patients.append(
                {
                    "id": row.get("Id"),
                    "birthdate": row.get("BIRTHDATE"),
                    "first": row.get("FIRST"),
                    "last": row.get("LAST"),
                    "gender": row.get("GENDER"),
                    "city": row.get("CITY"),
                    "state": row.get("STATE"),
                }
            )
            if len(patients) >= limit:
                break
    return patients

