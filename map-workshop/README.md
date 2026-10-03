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
- Uses grassland, plains, desert, broadleaf, pine and jungle. Later swamp, scrub, desert-wetland and snowy alpine art is missing and is not represented as recovered work. Older pine assets currently represent wooded hills.
- Current aesthetic limits: obvious forest cell shapes, residual texture repetition, some long river reaches and angular elbows, repeated mountain silhouettes, and occasional crowded resource/mountain tiles. No claim of Civ4 quality parity.
- Rendering is synchronous Canvas 2D with a loading overlay and debounced controls. A worker and chunk caching would be appropriate before increasing map size significantly.
- No runtime service, package, telemetry, publishing or deployment. Ground-cover artwork is newly generated (see assets/ground/provenance.json). Other assets copied unchanged from `../Fantasy_Terrain_Codex/baseline/Fantasy_Tileset_Prototype55/assets`; original provenance and rights remain unchanged.

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
