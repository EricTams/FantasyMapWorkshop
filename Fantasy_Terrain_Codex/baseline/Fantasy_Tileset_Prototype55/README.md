# Fantasy Tileset Prototype55

Bounded prototype checkpoint, reviewed through55. The default `examples/jungle_mixed` combines real broadleaf/palm jungle with the source55 eight-edge river route. This reusable Python/PNG kit renders semantic input JSON with globally sampled materials, neighbor masks and extracted sprites. It is not a complete Civ4 replacement.

The current inventory has 130 canonical runtime PNGs and 25 input layouts: 16 authored and nine observed. All 91 non-mushroom PNGs from48 are retained unchanged; four historical mushroom PNGs were replaced by five real-jungle PNGs from54. Across the 81 guide concepts, 41 are implemented prototypes, 11 are partial and 29 are not built. See `mapping_registry.json` and `docs/INTEGRATION55.md` for the complete scope and usage.

## Quick start

Python 3.10 or newer is required. Install `requirements.txt`, then run from this folder:

```sh
python -m pip install -r requirements.txt
python render_example.py
python verify_scaffold.py
```

The compact core carries all runtime PNGs and all input layouts, plus ONE complete prebuilt default Tiled sample at `examples/jungle_mixed/generated/sample.tmj`. Extra cached exports and artwork-source packs are optional. Every other input renders independently with the core alone:

```sh
python render_example.py --example examples/river_junctions
python render_example.py --example examples/cold_frontier
python render_example.py --example examples/botanical_grove
python render_example.py --example examples/creature_coast
python render_scene.py examples/observed_layouts/arboria_opening
```

`render_example.py` exports an exact visible-layer Tiled reconstruction for an origin-aligned 128px orthogonal grid. Observed warped/perspective layouts use `render_scene.py`. Validation covers JSON/XML, relative references, independent semantic axes and visible-pixel reconstruction; native Tiled GUI testing has not been performed.

## Current contracts

- Semantic GIDs1–10 retain their meanings; tundra is11, snow12 and independent pack ice13. Visible sprites begin at14. Ice is hidden layer10; authored shared-edge river topology is hidden layer11. Relief, resource and improvement identities remain independent
- `river_edges.py` accepts integer grid-corner routes made of unit shared edges. `qa/authored_river_migration55.json` records the explicit eight-layout migration and retains the former paths. No authored interior-cutting route remains. The nine observed layouts and their diagnostic river traces are unchanged
- J means real jungle under the latest recorded direction override. Accepted Spices are Scarlet pepper bushes. Optional34 crimson seedpods remain an unaccepted off-default draft
- Clams and crabs retain partial physical water contact; Leviathans are an implemented prototype. Repeated rectangular pack ice, material repetition, angular generic coasts, geometric biome boundaries, neat clearings, vine-end clipping and gold/silver color reliance remain limitations

Every deliverable archive is limited to 18,000,000 bytes. Optional frozen artwork sources are needed only to re-extract native assets, not to render or export maps. Source screenshots are excluded. Historical versioned integration and QA documents retain their original checkpoint claims; this README and `docs/INTEGRATION55.md` define the current55 contract.
