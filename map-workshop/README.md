# Atlas — Fantasy Map Workshop

A local, dependency-free browser prototype built from the preserved Fantasy Terrain Prototype55 PNG assets. New geography and rendering code; this does **not** recover the missing World20 implementation.

## Run

From this folder:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open http://127.0.0.1:4173 in a browser. Use Chrome or another standard browser for downloads; the Codex embedded browser did not complete a download during testing. No package installation or build is required. JavaScript modules need HTTP serving, rather than opening index.html as a file.

Sliders regenerate after a brief pause. A fixed seed preserves the underlying noise fields when settings change. The die picks a new seed. Drag to pan; scroll or use +/− to zoom; Fit resets the camera. Focus the map for arrow-key panning, +/− zoom, and 0 to fit. PNG export is the clean 2048×1536 world without the UI or grid; JSON includes generator version, seed, settings, projection, cells and shared-edge river routes. Resource labels are included in hover inspection.

## Design and boundaries

- 16×16 logical square tiles projected to 128×96 pixels, with upright sprites.
- One connected landmass, always bordered by ocean. Maximum coverage is capped at 196 of 256 cells to retain that border.
- Seeded elevation/moisture fields drive terrain, relief and vegetation. A coast-rooted shortest-path tree generates acyclic rivers on grid edges. This is a gameplay-oriented drainage approximation, not a hydrological simulation: local uphill segments may occur.
- Terrain, vegetation, relief and resource identities are independent. Resources are biome-dependent. Their actual alpha silhouettes reserve canopy clearance; surrounding forest density falls off smoothly over roughly one to two tiles with seeded irregularity. Thinning crosses tile borders, overlapping influences do not multiply, and tree sizes stay unchanged. Placement is not yet balanced for multiplayer or tested for complete sprite collision avoidance.
- Coastlines follow the union of logical land tiles, with small softened corners and edge weathering. The coast now receives the full displacement, using the same coordinates as the interior. A shared inverse displacement field drives biome ownership, material coordinates, forest boundaries, river distances and tree clearance. Rivers use a union distance field with varying widths, textured water and source tapering; the logical shared-edge graph is unchanged.
- Original materials are globally sampled with overlapping repeat boundaries and reduced contrast. Biome crossfades occupy narrow edge bands. Vegetation is drawn on a globally seeded lattice and sprites are sorted by their ground contact depth.
- Four terrain families: grassland, plains, swamp and desert. Each supports flat, forest, hills and forest+hills. Flat forests use broadleaf, scrub, jungle and desert wetland respectively. All forest+hills use shared Alpine conifers, green ground, modest snow and hills; mountains remain shared rocky sprites. Swamp and wetland materials and scrub/reed/Alpine art are new reconstructions, not recovered World20 assets.
- Current aesthetic limits: obvious forest cell shapes, residual texture repetition, some long river reaches and angular elbows, repeated mountain silhouettes, and occasional crowded resource/mountain tiles. No claim of Civ4 quality parity.
- Rendering is synchronous Canvas 2D with a loading overlay and debounced controls. A worker and chunk caching would be appropriate before increasing map size significantly.
- No runtime service, package, telemetry, publishing or deployment. New family vegetation artwork uses built-in imagegen (see assets/families/provenance.json); unused ground-cover experiments are retained in assets/ground. Other assets copied unchanged from `../Fantasy_Terrain_Codex/baseline/Fantasy_Tileset_Prototype55/assets`; original provenance and rights remain unchanged.

## Files

- `generator.js`: pure seeded geography, settings, drainage and map data.
- `vegetation.js`: alpha-weighted visual centers, occupied sprite footprints for river/resource clearance, and seeded resource density falloff; ground anchors and depth ordering remain independent.
- `geometry.js`: shared displacement, biome weights, tile coast distances and river distances.
- `renderer.js`: material sampling, coasts, vegetation, rivers and resource art.
- `app.js`: controls, camera, tile inspection and exports.
- `tests/generator.test.mjs`: deterministic replay, connected land, resource/relief constraints, river bounds/adjacency/cycles and control extremes over 80 seeds.
- `tests/materials.html`: flat-field and mixed-field rendering diagnostics.
- `checkpoints/v1/`: original browser milestone.
- `checkpoints/v2/`: shared interior displacement with reduced coastal displacement.
- `checkpoints/v3/`: full shared coastal displacement, with identical seed and geography for comparison.
- `checkpoints/v4/`: canopy-aware river clearance. Tree candidates whose visible footprint crosses the channel/bank margin are rejected; roots are not shifted. Horizontal rivers therefore reserve extra space for foreground crowns. `tests/forest-rivers.html` verifies channel visibility with the actual broadleaf, pine and jungle sprites.

Run tests with Node 20+:

```sh
node --test tests/*.test.mjs
```

Preserve each meaningful iteration in Git, including semantic inputs and previews; never overwrite the historical baseline to match the new renderer.

- `checkpoints/v5/`: gradual resource clearings and actual resource silhouette protection, with the same default semantic world as v4.

- `checkpoints/v6/`: individual white stags and scarlet pepper bushes, using preserved native anchors and pair layouts at 90% native size. Each sorts independently with trees. Foliage behind a resource can overlap; foreground foliage protects the upper 84–85% of stag/bush alpha while allowing lower-edge overlap. Crystals remain single sprites. Broad thinning and river clearance remain unchanged. See `tests/resource-groups.html` for enlarged woodland examples.

- `checkpoints/v7/`: reduce tree retention probability to 82% of its previous value, retaining the same deterministic candidate positions, scales and woodland extent. This thins canopy density without changing the forest-coverage slider or semantic map.

- `checkpoints/v8/`: tree retention reduced from 82% to 55% of the original candidate density (about one third fewer than v7). Same candidate positions, scale and forest area; more ground shows through the canopy. Both in-app previews refreshed.

- `checkpoints/v9/`: sparse grass, moss, leaf litter and tiny stones beneath relief, trees and resources. Continuous clustered coverage blends across forest edges and resource clearings; entire patch silhouettes fade away from the displaced coast and riverbanks. Tree retention remains 55%.

- `checkpoints/v10/`: ground-cover sprites disabled after visual review. The detailed patches read as smudges; simplified tufts did not match the existing art. Experimental code and both atlases are retained for reference but are not loaded or drawn. Restores the clean v8 appearance, retaining 55% tree density.

- `checkpoints/v11/`: opening showcase uses seed `wildwood-184`, land 66, ruggedness 57, moisture 43, forest 65, resources 35. All implemented terrain, forest and relief types have at least 15 tiles each; map remains 16×16. Coverage is verified against actual opening form values by `tests/showcase.test.mjs`. Subsequent random seeds and slider changes are not forced to include every type.

- `checkpoints/v12/`: reconstruct the four-by-four terrain family system. Seed `wildwood-1701`, settings land 72 / ruggedness 62 / moisture 43 / forest 60 / resources 35 includes all 16 combinations plus mountains. Generator version is now 2, so earlier seed outputs intentionally differ. New `terrain.js` centralizes the forest+hills → Alpine rule. `tests/terrain-families.html` shows all 16 combinations at native size; linked below the map. Swamp remains continuous land with small procedural pools; desert forest retains sand with reeds, palms and water glimpses. Pool coverage is heuristic, not a reproduction of the historical 2.3% figure. Existing repeated hill placement and tiled forest extents remain visible limitations.

- `checkpoints/v13/`: scrub foliage recolored sage gray-green with brown woody branches using built-in imagegen. Only scrub uses `assets/families/sage-scrub-atlas.png`; other families retain their previous sprites. Prompt saved alongside the atlas.

- `checkpoints/v14/`: connected relief using `relief.js`. A deterministic branching graph joins neighboring relief cells through shared saddles, avoids closed loops, and supports a smooth height field. The existing displacement maps field shading and rock anchors together. Varied overlapping shoulders connect peaks; rocks depth-sort with trees/resources and respect visible river, coast and resource silhouettes. Alpine groves thin toward crests and snow follows elevation/shaded pockets. Semantic terrain and drainage are unchanged. `tests/connected-relief.html` shows hill chains, mountain foothills and an Alpine/river/resource transition. Existing rock silhouettes remain recognizable and clearance can introduce gaps.

- `checkpoints/v15/`: broad relief combines smooth two-dimensional tile support and rolling variation with a reduced ridge contribution in dense regions. Broad regions use larger area-distributed knolls, while narrow chains retain ridge-based shoulders. New `tests/relief-blocks.html` shows 3×3 hills, Alpine hills and a mountain core with foothills, linked below the map. Unit checks cover continuously raised block interiors and narrow ridge continuity. Semantic geography remains unchanged. Existing hill sprites still visibly repeat.

- `checkpoints/v16/`: larger mountain peaks (128–158 world pixels wide) and less low hill cover immediately around their bases, improving mountain prominence within broad foothill regions.

- `checkpoints/v17/`: adjacent mountains share broad rocky saddles and secondary crags; grassy interior knolls become rock. The 3×3 study now includes a full mountain massif. Mountain silhouettes are fitted against displaced northern boundaries: overlap into another mountain is allowed, while peaks bordering other terrain shift down or scale to fit. Existing river/coast/resource clearance remains active. 20 tests pass.

- `checkpoints/v18/`: reconstructed mineral art: silver-bearing mithril rock, embedded gemstones and dark voidstone. Following scale feedback, each tile uses three separated outcrops (62/37/29px widths) with independent depth/clearance. Smaller members currently reuse the same image. Built-in imagegen prompts saved in `assets/minerals/reconstructed/provenance.json`; original mineral art retained. Native-size comparison linked below the map.

- `checkpoints/v19/`: ruby-only gemstone outcrops on a simpler broad-faced stone base. Retains three separate members and existing placement. Built-in imagegen edit prompts saved beside `assets/minerals/reconstructed/rubies.png`; prior art preserved. Visually checked in native-size mineral study and refreshed both in-app previews.

- `checkpoints/v20/`: rough ruby crystal clusters replace the stone-heavy mounted gems. Minimal dark stone at the roots; existing three-member placement and scale retained. Built-in imagegen prompt saved in `assets/minerals/reconstructed/ruby-clusters-provenance.json`. Native-scale visual review and both in-app previews refreshed.

- `checkpoints/v21/`: default 28 × 28 showcase (784 tiles, 3584 × 2688 pixels), with a 16 × 16 size option. Seed `wildwood-1701` at opening settings naturally contains all eight resource types (84 sites) and all 16 terrain variants; other seeds/settings are not forced. Renderer, coast buckets, drainage and camera use world dimensions. World tour visits eight resources and six terrain landmarks, smoothly moves for 2.2 seconds then pauses for 3 seconds, and loops. Dragging, zooming, Fit, arrow keys, Escape, resizing, regeneration or hiding the browser tab stops the tour. Zoomed camera wraps horizontally across the ocean border and clamps vertically; Fit shows one centered overview. 22 tests pass; browser progression, manual interruption and exports verified.

- `checkpoints/v22/`: separate ground-shadow pass for white stags and aurochs. Soft multiply-blended contact and lower-right cast ellipses use the lower occupied sprite footprint for placement and render beneath all objects. Original sprites unchanged. Native-scale before/after study linked below map; 22 tests pass and both previews refreshed.
