# Missing pieces and next steps

## Preserved

- Complete Prototype55 compact core, unchanged
- Python rendering and Tiled export source, required runtime PNGs, and authored/observed input JSON
- Five original later PNG references in the companion ZIP
- Current design direction and known issues
- Portable run/verification commands and fresh validation evidence

## Missing or not supplied

- Scripts that produced Terrain Families11, Mixed Terrain19, and World20
- Later quiet-swamp, alpine/snow-tree, bright-jungle, scrub, and desert-wetland asset/material changes
- The later sampling-period repair and Boundary19 implementation
- Latest 16×16 scene, exact placement records/seeds, resource assignments, shoreline, and river topology as editable source
- Original art atlases and extraction tool packs; the baseline's ready-to-render runtime assets are present
- A browser renderer, game runtime, general seeded geography generator, and Git history

The resource-key PNG is an image. It is not a substituted JSON scene. If a new scene is traced or inferred from a reference, label it a reconstruction and record uncertainties.

The historical World20 implementation reportedly imported shared scene/coast/river/resource code, woodland structure, and assets from several later matrix directories; some alpine functions were extracted from another script using AST. Those later dependencies are absent. A future reconstruction should consolidate them into ordinary modules rather than relying on transient directories or script extraction. Preserve individual materials/sprites, anchors, scales, variants, semantic layers, shared-edge rivers, global texture coordinates, boundary weights, feature clearings, and depth sorting.

## Proposed staged work, subject to the user's next request

### A. Establish a safe working checkpoint

Reproduce the default baseline and preserve it unchanged. Make a working copy outside `baseline/`. Record the input files, dependency versions, render command, and image checksum. Inspect the genuine screenshot benchmarks before setting visual acceptance criteria.

### B. Restore the later family system incrementally

Implement independent biome/vegetation/relief rules in the working copy. Start with the four-by-four matrix, including diagnostic views without objects. Reconstruct one missing family at a time, retaining the intended swamp continuity and large resource compositions. Any new asset creation requires a separately requested scope.

### C. Repair material continuity before elaborate mixed maps

Test flat homogeneous regions and horizontal/vertical repeat boundaries. Then add small two-biome and four-biome junction scenes. Keep tile interiors pure and transition bands narrow; compare at native and enlarged views. Record measured material ownership and visual critique separately.

### D. Rebuild a representative map

Author a new, explicitly reconstructed map input with known semantic cells, placements, shared-edge river routes, and shoreline. Exact historical World20 reproduction is not promised. Address the polygon coastline, river elbows/sources, and repetitive mountain silhouette while preserving the known family/scale constraints.

### E. Browser rendering and map generation

Only after the offline checkpoint is stable and reviewed, design the browser asset pipeline and rendering contract. Then treat geography generation as its own task, with connectivity, passability, resource placement, and river topology rules. Do not package an image viewer as though it were the missing game renderer.

## Checkpoint discipline

For each new iteration, save source, runtime assets, semantic inputs, dependency versions, generation commands, previews, diagnostics, and validation results in a portable archive or repository. Include both a clean map and useful diagnostic overlays. Keep provenance and gaps explicit so the next continuation does not depend on transient working files.
