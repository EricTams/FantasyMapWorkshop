# Fantasy Terrain: portable Codex handoff

This package gives you a runnable, preserved **Prototype55 Python baseline** and a clear route to continue the terrain project in Codex.

**The newer renderer and editable inputs that produced World20, Terrain Families11, and Mixed Terrain19 are missing.** Their PNGs survive in the companion reference ZIP. They are visual targets, not a reproducible source checkpoint or accepted final art. Running this package produces the older Prototype55 example, not World20.

## Start in Codex

Unzip the source ZIP, open `Fantasy_Terrain_Codex` in Codex, and copy the companion ZIP's `references` folder beside this README. Paste this prompt:

> Read AGENTS.md and CODEX_HANDOFF.md. Verify the package and reproduce the untouched Prototype55 default render. Inspect all five reference PNGs. Inventory the gap between the preserved baseline and the later design in docs/LATEST_DESIGN.md, then propose a small, testable reconstruction plan before editing. Keep the baseline intact and distinguish recovered files from new reconstruction. Do not claim World20 is reproducible yet. Do not start a browser port, general geography generator, art regeneration, or deployment in this first task.

## Open and run

1. Extract `Fantasy_Terrain_Codex_Source.zip` and open its `Fantasy_Terrain_Codex` folder in Codex.
2. Extract `Fantasy_Terrain_Codex_References.zip` into the same parent directory. Its `Fantasy_Terrain_Codex/references` folder should sit next to this README. If your extractor creates a second folder, move its `references` folder into this one. The references are not needed to run the baseline.
3. Read `CODEX_HANDOFF.md` and `AGENTS.md` before making changes.
4. With Python 3.10 or newer installed, run these commands from this folder:

```sh
python -m venv .venv
```

Activate the environment:

```sh
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then:

```sh
python -m pip install -r requirements-tested.txt
python verify_package.py --require-references
python run_baseline.py
```

If you only downloaded the source ZIP, omit `--require-references`. On systems that name Python `python3`, use that for the initial environment command. The tested dependency versions require a Python version with compatible wheels; Python 3.12 is the tested choice. The baseline's broader requirements are available through `requirements.txt` if you deliberately use a different environment.

Open the result:

- `baseline/Fantasy_Tileset_Prototype55/examples/jungle_mixed/generated/preview.png`
- `baseline/Fantasy_Tileset_Prototype55/examples/jungle_mixed/generated/sample.tmj` for the prebuilt Tiled export

The launcher rerenders the default example and runs the baseline verifier. It does not install dependencies, generate new artwork, open a server, or deploy anything.

## Contents

- `baseline/Fantasy_Tileset_Prototype55/`: all **338 original core files**, byte-for-byte preserved from the supplied archive, including 130 runtime PNGs, 25 input layouts, Python renderer/exporter, and one complete cached Tiled example
- `CODEX_HANDOFF.md`: ready-to-use continuation brief and first-task prompt
- `docs/LATEST_DESIGN.md`: later design direction and known visual problems
- `docs/RECONSTRUCTION_PLAN.md`: missing pieces and staged next work
- `docs/VALIDATION.md` and `validation/`: exact checks performed for this export
- `PACKAGE_MANIFEST.json`: source checksums and expected reference checksums
- `references/`: five original PNGs, supplied by the companion ZIP

No browser app, general seeded geography generator, Git repository/history, or recovered World20 source is included. The baseline contains authored JSON layouts and deterministic rendering/placement; that does not make it a general map generator. Optional original artwork atlases/exporters from older archives are not required to run it and are not included.

The project aims for reusable fantasy strategy-map art that exceeds Civ4 readability. Automated checks establish technical integrity, not that visual goal. See `docs/LATEST_DESIGN.md` for genuine Civ4 benchmark links and the unresolved art issues.

Both ZIPs are below 18,000,000 bytes. No copyrighted Civ4 screenshot pixels are bundled as game assets. No new license or redistribution rights are granted by this packaging; review asset provenance before public distribution.
