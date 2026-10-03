"""Rerender and verify the preserved default checkpoint, from any working directory."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "baseline" / "Fantasy_Tileset_Prototype55"

if __name__ == "__main__":
    for name in ("render_example.py", "verify_scaffold.py"):
        print(f"Running Prototype55 {name}", flush=True)
        subprocess.run([sys.executable, str(BASELINE / name)], cwd=BASELINE, check=True)
    print("Baseline preview: " + str(BASELINE / "examples/jungle_mixed/generated/preview.png"))
    print("This is Prototype55, not the later World20 reference.")
