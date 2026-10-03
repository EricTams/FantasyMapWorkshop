# Later terrain direction

This brief preserves later design decisions so the older baseline can be continued without losing them. Numerical implementation details below are historical reports supplied with the handoff, not measurements freshly verified from missing source.

## Goal and model

Create reusable 2D fantasy strategy-map art with stronger readability than Civ4, eventually used in a GitHub Pages browser game. Keep terrain, vegetation, relief, resources, and improvements as distinct semantic axes. Ground need not remain visible through dense forest. Forest neighbors should connect naturally.

The latest World20 reference represents an authored 16×16 continent surrounded by ocean, reportedly with 18 resource tiles, 1110 depth-sorted objects, three river catchments/outlets, and two tributaries. It used fixed material/placement seeds, not general seeded geography generation. The reported cell width was 128 world pixels and projected cells were 128×96 pixels. None of those missing editable inputs have been reconstructed here.

## Biome families

Rows are grassland, plains, swamp, and desert. Columns are clear, flat forest, bare hills, and forest+hills.

- **Grassland forest:** dense woodland
- **Plains forest:** low woody scrub
- **Swamp forest:** bright lime/emerald jungle with palms and broadleaves, plus tiny coral accents. Jungle remains jungle; the mushroom direction was abandoned
- **Desert forest:** sandy wetland vegetation with dense reeds/plants/palms and only tiny water glimpses. Avoid a large oasis pool
- **Every forest+hills combination:** a shared alpine treatment with fuller conifers, visible but modest branch snow, and a little ground snow
- **Every mountain:** the same rocky, spiky mountain family, independent of base biome
- **Bare hills:** preserve the base ground; use smaller, more plentiful rounded bumps with light grey rock specks

The matrix11 PNG is the visual reference, not a claim that all of these art goals are fully satisfied.

## Walkable swamp

Passable cells should read as continuous walkable land. Swamp is calm olive wet grass/peat with quiet muddy seams; historically reported open water coverage is approximately 2.3%. Keep unified ground below hills and jungle edges. Preserve the jungle canopy and hill lighting while repairing the ground. Do not replace the region with water-heavy patchwork or disconnected islands.

## Materials and biome transitions

Tile identity must remain clear. A tile should not read as half desert/half grass because its neighbors differ. Avoid broad blended interiors, duplicate halos, and whole-tile color washes.

The later sampler repair reportedly exposed the true 128px fine repeat period instead of repeating a nonseamless 512px source four times inside a 512 field while blending only that field's outside edges. The aim was to remove false interior grid seams. Reconstruct carefully and retain a flat, single-material diagnostic so mixing cannot mask the defect.

Boundary19 reportedly used signed contours with 10–14px coherent lobes, 1.5–3px perturbations at a 3–7px clump scale, and a variable 6–10 world-pixel crossfade. The central 70% of tile width remained pure, with roughly 91%+ own-material coverage overall. Those are reconstruction clues; inspect the PNG and test any new implementation instead of assuming the numbers alone reproduce it.

## Resources and improvements

Resources should be impressive fantasy features composed across a whole tile, with minimal clutter. Their intentionally large scale is important. Do not turn them into small floating icons.

- Spices: scarlet pepper bushes, low green shrubs with obvious red elongated pepper fruit
- Deer: white stags
- No road spam
- No universal visual upgrade system; occasional deliberate swaps are acceptable

Prototype55 also preserves an off-default crimson seedpod proposal as historical content. It is not the accepted spice direction.

## Rivers and known unfinished visuals

Rivers run between tiles along shared-edge topology. Later map20 still has visible problems:

- Angular/notched polygon coastline
- Straight, canal-like reaches, square river elbows, and blunt sources
- Repeated isolated mountain cones

The next work should improve those without losing resource scale, semantic clarity, or connected forest massing. Neither World20, matrix11, nor boundary19 is accepted final quality.

## Quality benchmark

Use actual Civ4 screenshots as the visual benchmark, not only the previous generated result:

- https://www.sullla.com/Civ4/EpicSix/EP6-1.jpg
- https://www.sullla.com/Civ4/JWB-16.jpg
- https://www.sullla.com/Civ4/WCC/WCC-14.jpg

These links were supplied for comparison; availability was not rechecked during packaging. Screenshot pixels are not bundled or authorized as game assets. Show each iteration with concrete criticism and next changes. Automated geometric or pixel tests do not establish aesthetic parity or superiority.
