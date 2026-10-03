"""Verify portable source and optional reference checksums without third-party packages."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parent


def verify(records, required):
    checked = 0
    missing = []
    errors = []
    for record in records:
        relative = Path(record["path"])
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"Unsafe manifest path: {relative}")
            continue
        path = ROOT / relative
        if not path.is_file():
            missing.append(str(relative))
            continue
        content = path.read_bytes()
        if len(content) != record["size_bytes"] or hashlib.sha256(content).hexdigest() != record["sha256"]:
            errors.append(f"Checksum mismatch: {relative}")
        else:
            checked += 1
    if required:
        errors.extend(f"Missing: {p}" for p in missing)
    return checked, missing, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-references", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    source, _, errors = verify(manifest["source_files"], required=True)
    references, missing, ref_errors = verify(manifest["reference_files"], required=args.require_references)
    errors.extend(ref_errors)
    print(json.dumps({"source_files_verified": source, "reference_files_verified": references,
                      "missing_optional_references": missing if not args.require_references else [],
                      "errors": errors, "status": "passed" if not errors else "failed"}, indent=2))
    raise SystemExit(1 if errors else 0)
