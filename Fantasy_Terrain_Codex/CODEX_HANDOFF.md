# Codex continuation brief

## What is actually available

This is a recovery-and-continuation package, not the latest project source. The preserved source is `baseline/Fantasy_Tileset_Prototype55`, an offline Python/NumPy/Pillow/SciPy renderer. It includes its runtime assets, semantic JSON layouts, shared-edge river model, Tiled exporter, verification script, and one cached example.

Later visual output survives separately:

| Reference | Purpose |
| --- | --- |
| `references/World_20_Clean_Native.png` | Latest full map without the grid overlay; 2048 × 1536 |
| `references/World_20_Dashed_Native.png` | Same later map with tile-grid aid; 2048 × 1536 |
| `references/World_20_Resource_Key.png` | Resource/cell key; 1408 × 730 |
| `references/Terrain_Families_Revision11.png` | Four base biomes × clear/forest/hills/forest+hills; 664 × 724 |
| `references/Mixed_Terrain_Revision19_2x.png` | Mixed-biome seam and adjacency reference; 1024 × 832 |

These are iterative references, not accepted final quality. Their source scripts, newer asset variants, later material pipeline, and editable map inputs were not recovered. Prototype55 predates the newer biome model, snowy conifers, bright jungle, quieter swamp, desert reeds/palms, fine-period sampler repair, and Boundary19 transitions.

## Recommended first Codex request

> Read AGENTS.md and CODEX_HANDOFF.md. Verify the package and reproduce the untouched Prototype55 default render. Inspect all five reference PNGs. Inventory the gap between the preserved baseline and the later design in docs/LATEST_DESIGN.md, then propose a small, testable reconstruction plan before editing. Keep the baseline intact and distinguish recovered files from new reconstruction. Do not claim World20 is reproducible yet. Do not start a browser port, general geography generator, art regeneration, or deployment in this first task.

## Existing entry points

Run from `baseline/Fantasy_Tileset_Prototype55`:

```sh
python render_example.py
python verify_scaffold.py
python render_example.py --example examples/river_junctions
python verify_scaffold.py --example examples/river_junctions
python render_scene.py examples/observed_layouts/arboria_opening
```

- `KitScene` in `kit_renderer.py` renders a semantic scene, handles global fields, and exposes depth-sorted objects.
- Each example has `scene.json`, `shoreline.json`, and `features.json`.
- `river_edges.py` compiles integer grid-corner routes into shared-edge records.
- `render_example.py` builds the origin-aligned 128px orthogonal Tiled sample. Its visible ground is baked, with upright objects layered separately.
- `render_scene.py` renders the wider set of layouts, including observed warped/perspective inputs, without requiring Tiled export.
- `verify_scaffold.py` checks canonical assets, supported Tiled structure/references, semantic identity, and exact visible-layer reconstruction. It is not a native Tiled GUI test.

The older base terrain codes and climate-relief variants do not directly implement the later four-biome design. Inspect and map them deliberately; do not silently rename old categories and call that a reconstruction.

## Future sequencing

1. Preserve and reproduce this baseline; inventory missing pieces.
2. Reconstruct the later biome and material behavior against the PNGs and design brief, with explicit assumptions and small diagnostic scenes.
3. Improve the unresolved coast, river geometry, and mountain composition while retaining tile identity and resource scale.
4. Once the offline source checkpoint is reproducible and visually reviewed, plan a browser renderer for the eventual GitHub Pages game.
5. Treat general seeded geography generation as a separate phase. Fixed texture/placement seeds and an authored 16×16 layout do not already solve that phase.

Every stage needs its own approved scope. Packaging this handoff did not implement stages 2–5.
