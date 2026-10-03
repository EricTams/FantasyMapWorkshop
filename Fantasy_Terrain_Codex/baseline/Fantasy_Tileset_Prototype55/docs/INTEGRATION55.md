# Prototype55 integration

This bounded checkpoint is reviewed through55 and adds shared-edge river topology to the accepted botanical49/50, creature51, cold52, climate-relief53 and real-jungle54 families. The default is `examples/jungle_mixed`, using the source55 eight-edge brook and real broadleaf/palm jungle. The implementation inventory remains 41 implemented prototypes, 11 partial concepts and 29 not built across the 81-concept guide.

## Runtime and portable inputs

The core contains 130 canonical runtime PNGs and 25 input layouts: 16 authored and nine observed. All 91 non-mushroom PNGs from48 are unchanged. Four historical mushroom PNGs were removed from the current runtime and replaced by five real-jungle PNGs from54; historical archives retain the earlier art.

The package uses Python, NumPy, Pillow and SciPy. Runtime asset paths resolve relative to the package. Canonical PNGs use 8-bit channels: RGB for opaque materials and RGBA for straight-alpha sprites. Generated diagnostic masks use 16-bit grayscale PNG. Material alpha, source category codes and Tiled GIDs are different data.

Each input has `scene.json`, `shoreline.json` and `features.json`. Terrain rows and forest rows define cell identities. `hill_cells`, `mountain_cells` and `ice_cells` are independent lists. Shoreline polygons supply coast geometry. Authored rivers use explicit `river_edges`; observed inputs retain their source-visible `river_digitization` evidence. Copy an authored example, edit these fields and rerun the renderer. Hidden source river spans must remain unconnected unless a new route is deliberately authored as a separate design.

From the package directory:

```sh
python -m pip install -r requirements.txt
python render_example.py
python verify_scaffold.py
python render_example.py --example examples/river_junctions
python render_example.py --example examples/cold_frontier
python render_scene.py examples/observed_layouts/arboria_opening
```

`KitScene(scene, shoreline, features)` prepares whole-world fields. `render()` returns the full image; `render(box=(x,y,width,height))` samples the same fields for exact chunks. `object_instances()` returns depth-sorted `(depth_y, image, left, top, name)` tuples, including mountains, upright vegetation/actors/sites, projected oil, ice edges and resource objects. Render order is ground/coast/cold/ice material, hill underlay, vegetation interior, rivers, vineyard rows, context-dependent aquatic resources, then the shared object list.

## Shared edge river topology

`river_edges.py` compiles `scene.json` routes with integer grid corners in `[x,y]` order. Every consecutive pair must be one horizontal or vertical unit edge and stay within the map. Routes become canonical edge records such as `V:x:y` or `H:x:y`, with grid endpoints and adjacent owning cells in `[row,column]` order plus their N/E/S/W sides. Boundary edges can have one owning cell. Multiple routes can share one semantic edge record. Connectivity, endpoint nodes and junction nodes are recorded; local painted centerline meander stays within the documented narrow corridor around the shared edge.

The default brook has eight edges and nodes `[[4,0],[4,1],[4,2],[3,2],[3,3],[4,3],[4,4],[4,5],[4,6]]`. `examples/river_junctions` supplies an additional authored topology case. Source references for this checkpoint are `civ4_matched_v55/shared/river_edges.py` and `civ4_matched_v55/authored_river_migration.json`; these are provenance references, not external runtime dependencies.

`qa/authored_river_migration55.json` records explicit replacements for `authored_brook` and `authored_headwater_to_coast` in eight layouts: creature_coast, draft_fantasy_spice_proposal, generic_relief_fantasy, generic_river_pine, jungle_mixed, mixed_junctions, scarlet_pepper_valley and wildlife_water_test. It retains each previous path and the input hashes. No authored interior-cutting route remains. The nine observed layouts and all 27 of their input JSON files are unchanged; their traces remain diagnostic evidence and are never silently snapped or joined.

## Independent semantic axes and Tiled export

Input terrain codes are sand0, grass1, water2, plains3, tundra4, snow5 and unknown255. Vegetation is D broadleaf, P pine or J jungle. H/M relief remains independent; unknown terrain is never inferred from a hill or tree. Pack ice is an independent feature over water2 and never substitutes snow5 terrain. Resources and improvements retain their own category registries.

Semantic GIDs1–10 retain sand1, grass2, water3, plains4, unknown5, D6, P7, H8, M9 and J10. Tundra is11, snow12 and pack ice13. Visible sprite GIDs begin at14. Layer IDs are separate from GIDs:

- Layer1: visible sample-specific baked ground, vegetation interior, river, vineyard and aquatic-resource passes
- Layer2: visible depth-sorted upright vegetation, ice edges, actors and sites
- Layer3: hidden terrain semantic IDs
- Layer4: hidden vegetation semantic IDs
- Layer5: hidden logical cell identities, including explicit river-side flags
- Layer6: hidden source river traces or compiled authored route centerlines, with provenance
- Layer7: hidden independent H/M relief semantic IDs
- Layer8: hidden resource identities and recorded render-pass metadata
- Layer9: hidden independent improvement identities
- Layer10: hidden independent ice semantic IDs; the underlying terrain remains water
- Layer11: hidden authored shared-edge river records, including edge IDs, grid endpoints, adjacent cell sides and route membership

`generated/river_edges.json` accompanies the Tiled sample and records the input mode, provenance, routes and compiled topology. Observed traces do not acquire invented edge records. River geometry is painted once in the baked ground; layers6/11 are semantic records and do not duplicate visible paint.

Tiled uses a sample-specific ground image plus named depth-sorted sprites. These cached images are disposable exports; reusable canonical assets and semantic inputs remain in the core. Editing hidden Tiled records alone does not rerender the baked art: update input JSON and rerun the renderer. The export is for an origin-aligned 128px orthogonal grid. Warped/perspective observed inputs render with `render_scene.py`.

Validation checks JSON/XML, relative file references, semantics and exact visible-pixel reconstruction. Native Tiled GUI and downstream-engine testing have not been performed. No claim of native-editor or complete game integration is made.

All 90 unknown bases in the nine observed layouts remain unknown. Verified category/cell records and prior missing-feature repair audits carry forward. Authored examples are not evidence of actual Civ4 resource placement; late strategic and precious source cells remain unverified.

## Accepted families and rendering limits

- Botanicals49/50: indigo flowers, resin trees with corrected attached bark flows, cocoon trees, honey reeds and giant pod-fruit use upright resource sprites and owned contact clearings
- Creatures51: riding horses, giant red crabs and Leviathans. Crabs and Leviathans use the actual `painted_waterline` treatment in a water-clipped baked ground pass. They are excluded from visible Tiled actors to avoid duplicate drawing
- Pearl clams retain the43 water treatment and remain partial because their tinted floating-shell appearance is unresolved. Giant red crabs also remain partial because coherent physical water contact is still weak. Leviathans have a reviewed surfacing treatment but remain prototype artwork
- Cold52: frost heath, snowfields, pack-ice material and three edge sprites. The repeated rectangular ice pattern and outer footprint remain unresolved
- Relief53: 12 climate variants selected from explicit sand, tundra or snow terrain. Unknown bases retain the neutral original relief
- Jungle54: dense broadleaf/palm interior and four rooted edges replace the old mushrooms at every J cell. No mushroom fallback remains in the current runtime
- Rivers55: explicit authored shared-edge topology, route migration, edge ownership and independent Tiled metadata; observed evidence is preserved separately

Vineyard rows remain one world lattice over wine-cell unions, with press bays and independent upright presses. No duplicate grape-plot objects are drawn. Oil/Black ichor alone scales height by projected cell height; other mineral objects remain upright. Gold and silver rely strongly on yellow versus white color and are closer in grayscale.

## Delivery and scope

The compact core contains ONE complete default Tiled sample at `examples/jungle_mixed/generated/sample.tmj`, all canonical runtime PNGs and every input layout. Other inputs render independently with the core alone. Extra prebuilt cache packs and frozen artwork-source packs are optional. Each deliverable archive must be no larger than 18,000,000 bytes. Source screenshots are excluded.

This is not a complete Civ4-equivalent set. Implemented means a tested reusable prototype, not finished variants, animation, full adjacency coverage or aesthetic superiority. Repeating meadow structures and vegetation, angular generic coasts, geometric biome edges, neat resource clearings, vine outer-end clipping and incomplete source mappings remain visible limits. Original Sun-maize, Smallholding and Castle settlement growth concepts remain partial. Current city art does not complete the accepted central-keep and growth-dependent roof-density progression. General collision/navigation and complete game integration are not supplied.

`fantasy_translation_guide.json` retains 81 concepts and records the latest Jungle direction override. Accepted Spices remain Scarlet pepper bushes. Optional34 crimson seedpods remain an unaccepted off-default draft. `mapping_registry.json` gives the current implementation inventory. Historical versioned integration and QA files describe their named earlier checkpoints, including former staging holds; they are retained unchanged and do not supersede this55 contract.
