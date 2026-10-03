# Validation for this export

Validated on 2026-10-02 in Linux, using Python 3.12.14, NumPy 2.3.5, Pillow 12.3.0, and SciPy 1.17.0. These packages were already installed; a clean virtual-environment installation was not tested.

## Passed

- The supplied baseline ZIP passes CRC validation and contains no absolute or parent-traversal archive paths.
- All 337 entries in the baseline's original SHA256SUMS match. All 338 original files are preserved unchanged in this source package.
- A fresh extraction of the portable package runs `python run_baseline.py` successfully. The default render is byte-identical to the archived outputs; no original file changed during rerendering.
- The default verifier checks 130 canonical assets, 60 Tiled-relative references, 48 semantic cells, 11 masks, and eight shared river edges. Visible-layer reconstruction has a maximum channel difference of zero.
- The default preview SHA-256 is `753ec5d92d0d6f3cc256226d22c426a0401295d779737875f8ed3a2105010ebc`.
- `render_example.py --example examples/river_junctions` and its matching verifier pass, with nine shared edges, three routes, two junction nodes, and zero reconstruction difference.
- `render_scene.py examples/observed_layouts/arboria_opening` runs successfully; its runtime QA reports zero chunk difference and all 12 checked known land/water centers matching.
- All 25 Python files parse. All 109 initial JSON files parse, including 25 scene inputs. Added validation-report JSON is also parsed during final packaging.
- All five later reference PNGs decode and retain their original file checksums and dimensions. The package verifier checks them after the companion folder is installed.
- Source/reference archives are separately CRC-checked, cleanly extract into one project folder, and each stays below 18,000,000 bytes.

The detailed JSON results are in `validation/`. `PACKAGE_MANIFEST.json` records checksums for all source files except itself, plus the expected five original reference PNGs. `python verify_package.py --require-references` checks both parts without third-party dependencies. Checksums establish file integrity relative to this package, not provenance authentication.

## Scope and limits

Only the default, river-junction, and observed Arboria scenes were freshly rendered for this export; all 25 layouts were not rerun. Existing historical QA files inside the baseline retain their original checkpoint claims and are not new test results.

Native Tiled GUI, Windows/macOS execution, fresh dependency installation, browser runtime, and game integration were not tested. No latest-source recovery, new artwork, browser port, or deployment occurred. World20 was not reproduced. Its object counts, biome implementation numbers, and later sampler/boundary details are historical handoff context where identified, not newly validated source behavior.

The default preview and later family/map references were inspected visually to confirm the substantial version gap. This is not visual acceptance: the latest reference still has angular coastlines, canal-like river geometry, and repeated isolated mountain cones. Technical tests do not establish Civ4 aesthetic parity.
