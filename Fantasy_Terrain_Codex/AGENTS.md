# Instructions for Codex

## Read first

Read `README.md`, `CODEX_HANDOFF.md`, `docs/LATEST_DESIGN.md`, and `docs/RECONSTRUCTION_PLAN.md`. The preserved baseline's `README.md` and `docs/INTEGRATION55.md` describe only Prototype55.

## Truth and preservation

- The source of World20, Terrain Families11, and Mixed Terrain19 is absent. Their PNG references are not source code. Do not imply that the latest implementation has been recovered or can already be reproduced.
- Preserve `baseline/Fantasy_Tileset_Prototype55` as the historical checkpoint. Create a separate working copy for new implementation, preserving all runtime asset paths. Do not rewrite the preserved checksums to conceal differences.
- New reconstruction code must be identified as new work, with explicit assumptions. Keep any inferred layouts separate from recovered/authored historical inputs.
- Do not treat Prototype55 documentation as approval to undo later design decisions.
- No art regeneration, browser port, publishing, deployment, or push is implied by this handoff. Obtain the user's requested task before starting those stages.

## Working method

1. Run `python verify_package.py` after extraction. With the companion references installed, add `--require-references`.
2. In the tested Python environment, run `python run_baseline.py` and inspect the resulting pixels.
3. Inspect the actual reference PNGs before image-dependent implementation. If they are absent, use the companion ZIP rather than guessing from prose.
4. Change one visual subsystem at a time; keep semantic inputs separate from rendering.
5. Preserve authored shared-edge river topology and independent terrain, vegetation, relief, resource, and improvement identities.
6. Use repeatable seeds and record commands, versions, inputs, and output checksums for new work.
7. Test material continuity with a flat single-material field as well as mixed maps. Do not hide periodic sampling errors with wider biome blending.
8. Show each meaningful visual iteration with actionable critique. Compare against genuine Civ4 screenshots, not only the previous generated version.
9. Keep technical validation separate from aesthetic judgment. Never describe passed pixel/geometry tests as Civ4 quality parity.
10. Save source, asset changes, semantic inputs, and output previews together at every new checkpoint.

## Design guardrails

The full specifications are in `docs/LATEST_DESIGN.md`. Especially preserve clear tile identity, walkable swamp, bright jungle, shared alpine forest+hills, shared rocky mountains, large fantasy resources, connected forests, and between-tile rivers. Do not shrink resources into icons, reintroduce mushroom jungle, add road spam, or broaden transitions into half-grass/half-desert tile interiors.
