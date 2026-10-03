"""World-space material coast compositor, 128 px per gameplay cell by default.

Only masks, material sampling and placement are procedural. Visible texture comes
from the supplied authored material images. No generated rocks, foam outlines,
lighting bevel or bright continuous beach ribbon is added.

Minimal use::
    polygon, evidence = load_trace('corsica_shoreline.json', cell_size=128)
    materials = load_materials('shared/materials')
    result = render_coast((0, 0, 640, 640), polygon, materials,
                          edge_evidence=evidence)
    result.image.save('coast.png')

``box`` is (world_x, world_y, width, height), in integer pixels. Polygon vertices
are world-pixel coordinates, optionally already closed. A clip closing edge
still affects polygon membership, but NEVER coast distance, sand, bank, or
shallows. Inferred edges are rendered, but ``nearest_coast_status`` distinguishes
them from visible evidence. This module makes no exact source-fidelity claim.

Texture means and crossfades depend only on complete source materials. Every
sample and mask uses world coordinates, so independent chunks are byte-identical
to the corresponding part of a whole render. Optional forest input must likewise
be a world-coordinate callable/WorldMask, or a correctly cropped global array.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence
import json

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter

NO_COAST, VISIBLE, INFERRED, AUTHORED, ANALYSIS_CLIPPED = range(5)
STATUS_CODES = {"visible": VISIBLE, "inferred": INFERRED,
                "authored": AUTHORED, "analysis_clipped": ANALYSIS_CLIPPED}
STATUS_NAMES = {v: k for k, v in STATUS_CODES.items()} | {NO_COAST: "none"}
REQUIRED_MATERIALS = ("meadow", "deep_water", "shallow_water", "shore")


@dataclass(frozen=True)
class CoastConfig:
    """Lengths scale with cell_size; default values describe a 128 px cell."""
    cell_size: float = 128.0
    seed: int = 26
    antialias: float = 0.70
    max_sand_width: float = 10.0
    sand_threshold: float = 0.48
    forest_sand_suppression: float = 0.94
    shallow_min_width: float = 7.0
    shallow_max_width: float = 30.0
    shallow_strength: float = 0.88
    deep_contrast: float = 0.52
    shallow_contrast: float = 0.68
    material_scale: float = 1.30
    material_overlap: float = 0.125


# Coast-only pass27: baseline pass26 ownership/camera remain unchanged.
COAST27_CONFIG = CoastConfig(deep_contrast=.40, shallow_contrast=.84,
    max_sand_width=12, sand_threshold=.26, forest_sand_suppression=.60,
    shallow_min_width=9, shallow_max_width=24, shallow_strength=.95)

_SHALLOW_CACHE = {}

def _calibrated_shallow(source):
    """Reuse authored bottom/caustic detail without its panel-wide depth gradient.

    Calibration and every statistic use the full source, never a render chunk.
    A brighter source-water subset supplies the target mean, not a painted color.
    """
    key = id(source)
    cached = _SHALLOW_CACHE.get(key)
    if cached is not None and cached[0] is source:
        return cached[1]
    a = np.asarray(source, dtype=float)[..., :3]
    lit = a[..., 1] >= np.percentile(a[..., 1], 67)
    mean = a[lit].mean(0) * .45 + a.mean((0, 1)) * .55
    broad = gaussian_filter(a, sigma=(23, 23, 0), mode="wrap")
    derivative = np.clip(mean + (a-broad)*.92 + (broad-a.mean((0,1)))*.15, 0, 255)
    _SHALLOW_CACHE[key] = (source, derivative)
    return derivative


@dataclass
class CoastFields:
    land_mask: np.ndarray
    signed_distance: np.ndarray
    coast_distance: np.ndarray
    nearest_coast_status: np.ndarray
    nearest_coast_edge: np.ndarray
    nearest_boundary_status: np.ndarray
    coast_x: np.ndarray
    coast_y: np.ndarray


@dataclass
class CoastRender:
    image: Image.Image
    land_alpha: np.ndarray
    land_mask: np.ndarray
    signed_distance: np.ndarray
    coast_distance: np.ndarray
    nearest_coast_status: np.ndarray
    sand_alpha: np.ndarray
    shallow_alpha: np.ndarray
    bank_alpha: np.ndarray

    @property
    def terrain_weights(self) -> np.ndarray:
        """[land, water] weights; sums to one and preserves polygon ownership."""
        return np.stack((self.land_alpha, 1.0 - self.land_alpha))

    @property
    def visible_evidence(self) -> np.ndarray:
        """Nearest physical edge is source-visible, rather than inferred/authored."""
        return self.nearest_coast_status == VISIBLE


@dataclass(frozen=True)
class WorldMask:
    """A full-world proximity mask sampled without any chunk-local filtering.

    Values are clipped to [0, 1]. The (x, y) origin locates the mask's upper-left
    corner; pixels_per_sample allows a coarser mask. Values beyond it use outside.
    """
    values: np.ndarray
    origin: tuple[float, float] = (0.0, 0.0)
    pixels_per_sample: float = 1.0
    outside: float = 0.0

    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        return np.clip(map_coordinates(np.asarray(self.values, dtype=float),
            [(y - self.origin[1]) / self.pixels_per_sample - 0.5,
             (x - self.origin[0]) / self.pixels_per_sample - 0.5],
            order=1, mode="constant", cval=self.outside, prefilter=False), 0, 1)


def load_trace(trace: str | Path | Mapping, cell_size: float = 128.0,
               origin: tuple[float, float] = (0.0, 0.0)) -> tuple[np.ndarray, list]:
    """Read benchmark fractional-grid vertices without resmoothing their shape."""
    if not isinstance(trace, Mapping):
        trace = json.loads(Path(trace).read_text())
    points = np.asarray(trace["fractional_grid_polygon"], dtype=float)
    return points * float(cell_size) + np.asarray(origin), list(trace.get("edge_evidence", []))


def load_materials(directory: str | Path) -> dict[str, np.ndarray]:
    root = Path(directory)
    result = {key: np.asarray(Image.open(root / f"{key}.png").convert("RGB"),
                              dtype=float) for key in REQUIRED_MATERIALS}
    for key in ("forest_floor", "woodland"):
        if (root / f"{key}.png").exists():
            result[key] = np.asarray(Image.open(root / f"{key}.png").convert("RGB"), dtype=float)
    return result


def _step(a, b, x):
    t = np.clip((x - a) / np.maximum(np.asarray(b) - a, 1e-9), 0, 1)
    return t * t * (3.0 - 2.0 * t)


def _noise(x, y, scale, seed):
    """Smooth hashed value noise used for masks, never for painted objects."""
    u, v = x / scale, y / scale
    ix, iy = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64)
    fx, fy = u - ix, v - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

    def lattice(a, b):
        # Bounded signed-int arithmetic avoids platform-dependent uint overflow.
        n = (a * 374761393 + b * 668265263 + int(seed) * 1442695) & 0x7fffffff
        n = ((n ^ (n >> 13)) * 1274126177) & 0x7fffffff
        return (n ^ (n >> 16)) / 2147483647.0
    top = lattice(ix, iy) * (1 - fx) + lattice(ix + 1, iy) * fx
    bottom = lattice(ix, iy + 1) * (1 - fx) + lattice(ix + 1, iy + 1) * fx
    return top * (1 - fy) + bottom * fy


def _prepare_polygon(points, edge_evidence):
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 3:
        raise ValueError("polygon must contain at least three (x, y) vertices")
    if not np.isfinite(points).all():
        raise ValueError("polygon contains non-finite coordinates")
    if not np.array_equal(points[0], points[-1]):
        points = np.concatenate((points, points[:1]), axis=0)
    count = len(points) - 1
    statuses = np.full(count, AUTHORED, dtype=np.uint8)
    if isinstance(edge_evidence, Mapping):
        edge_evidence = edge_evidence.get("edge_evidence", edge_evidence)
    if edge_evidence is not None and len(edge_evidence):
        if len(edge_evidence) != count:
            raise ValueError(f"expected evidence for {count} edges, got {len(edge_evidence)}")
        seen = set()
        for i, evidence in enumerate(edge_evidence):
            if isinstance(evidence, Mapping):
                k = int(evidence.get("from_vertex", i))
                end = int(evidence.get("to_vertex", (k + 1) % count))
                if not 0 <= k < count or end not in (k + 1, (k + 1) % count):
                    raise ValueError("edge evidence must describe consecutive polygon vertices")
                status = evidence.get("status", "authored")
            else:
                k, status = i, str(evidence)
            if k in seen:
                raise ValueError(f"duplicate evidence for edge {k}")
            if status not in STATUS_CODES:
                raise ValueError(f"unknown shoreline evidence status: {status!r}")
            seen.add(k)
            statuses[k] = STATUS_CODES[status]
    return points, statuses


def _grid(box):
    if len(box) != 4 or any(int(v) != v for v in box):
        raise ValueError("box must be integer (world_x, world_y, width, height)")
    x0, y0, width, height = map(int, box)
    if width <= 0 or height <= 0:
        raise ValueError("box dimensions must be positive")
    y, x = np.mgrid[y0:y0 + height, x0:x0 + width]
    return x.astype(float) + 0.5, y.astype(float) + 0.5


def polygon_fields(polygon, box, edge_evidence=None) -> CoastFields:
    """Exact vector membership + distances at pixel centers, including concavities.

    ``signed_distance`` is positive on land and negative in water, measured to
    any classification edge. ``coast_distance`` measures only physical edges.
    Its value is +inf where no physical edge exists. Distance tie-breaking is
    vertex-order stable, independent of the requested render box.
    """
    points, statuses = _prepare_polygon(polygon, edge_evidence)
    x, y = _grid(box)
    inside = np.zeros(x.shape, dtype=bool)
    boundary_d2 = np.full(x.shape, np.inf)
    coast_d2 = np.full(x.shape, np.inf)
    boundary_status = np.full(x.shape, NO_COAST, dtype=np.uint8)
    coast_status = np.full(x.shape, NO_COAST, dtype=np.uint8)
    coast_edge = np.full(x.shape, -1, dtype=np.int32)
    cx, cy = x.copy(), y.copy()
    for k, (a, b) in enumerate(zip(points[:-1], points[1:])):
        dx, dy = b - a
        length2 = dx * dx + dy * dy
        if length2 < 1e-16:
            continue
        if abs(dy) > 1e-12:
            inside ^= ((a[1] > y) != (b[1] > y)) & (x < dx * (y - a[1]) / dy + a[0])
        t = np.clip(((x - a[0]) * dx + (y - a[1]) * dy) / length2, 0, 1)
        px, py = a[0] + t * dx, a[1] + t * dy
        d2 = (x - px) ** 2 + (y - py) ** 2
        closer = d2 < boundary_d2
        boundary_d2[closer] = d2[closer]
        boundary_status[closer] = statuses[k]
        if statuses[k] == ANALYSIS_CLIPPED:
            continue
        closer = d2 < coast_d2
        coast_d2[closer] = d2[closer]
        coast_status[closer] = statuses[k]
        coast_edge[closer] = k
        cx[closer], cy[closer] = px[closer], py[closer]
    return CoastFields(inside, np.where(inside, 1.0, -1.0) * np.sqrt(boundary_d2),
                       np.sqrt(coast_d2), coast_status, coast_edge,
                       boundary_status, cx, cy)


def sample_material(material, x, y, scale=1.0, offset=(0.0, 0.0), overlap=0.125):
    """Sample a continuous periodic material field at absolute world coordinates.

    A small overlap crossfade hides the non-tileable atlas crop's outside edges.
    Unlike per-chunk normalization, this operation has no dependence on box size.
    The repetition period is source_size minus the overlap band.
    """
    source = np.asarray(material, dtype=np.float64)
    if source.ndim != 3 or source.shape[2] < 3 or min(source.shape[:2]) < 2:
        raise ValueError("material must be an HxWx3 image with both dimensions >= 2")
    source = source[:, :, :3]
    h, w = source.shape[:2]
    if not 0 <= overlap < 0.5:
        raise ValueError("material overlap must be in [0, 0.5)")
    bx, by = max(1.0, w * overlap), max(1.0, h * overlap)
    u, v = np.mod(x * scale + offset[0], w - bx), np.mod(y * scale + offset[1], h - by)
    wx, wy = _step(0, bx, u), _step(0, by, v)
    u2, v2 = np.minimum(u + w - bx, w - 1), np.minimum(v + h - by, h - 1)

    def at(xx, yy):
        return np.stack([map_coordinates(source[:, :, c], [yy, xx], order=1,
                         mode="nearest", prefilter=False) for c in range(3)], axis=2)
    # Sampling is restricted to source pixels and their bilinear mixtures.
    return ((at(u, v) * wx[..., None] + at(u2, v) * (1 - wx[..., None])) * wy[..., None]
            + (at(u, v2) * wx[..., None] + at(u2, v2) * (1 - wx[..., None])) * (1 - wy[..., None]))


def render_coast(box, polygon, materials: Mapping[str, np.ndarray],
                 edge_evidence=None, forest_proximity=None,
                 config: CoastConfig | None = None) -> CoastRender:
    """Render an arbitrary world-pixel box with explicit ownership and diagnostics.

    Material values may be uint8/float arrays or PIL images, in 0..255 RGB. A
    forest-proximity callable receives world pixel centers ``(x, y)`` and returns
    0..1 values. An array must already match this exact box; no blur or distance
    transform is performed on a local chunk. Forest proximity suppresses exposed
    sand; it does not add trees or change the polygon's ownership.
    """
    config = config or CoastConfig()
    if config.cell_size <= 0 or config.material_scale <= 0 or config.antialias < 0:
        raise ValueError("cell_size/material_scale must be positive; antialias nonnegative")
    if not 0 <= config.forest_sand_suppression <= 1 or not 0 <= config.shallow_strength <= 1:
        raise ValueError("forest_sand_suppression and shallow_strength must be in [0, 1]")
    if config.max_sand_width < 0 or not 0 <= config.shallow_min_width <= config.shallow_max_width:
        raise ValueError("coast widths must be nonnegative with min <= max")
    missing = [key for key in REQUIRED_MATERIALS if key not in materials]
    if missing:
        raise ValueError(f"missing material arrays: {', '.join(missing)}")
    fields = polygon_fields(polygon, box, edge_evidence)
    x, y = _grid(box)
    unit = config.cell_size / 128.0
    seed = config.seed
    forest = np.zeros(x.shape, dtype=float)
    if forest_proximity is not None:
        forest = np.asarray(forest_proximity(x, y) if callable(forest_proximity)
                            else forest_proximity, dtype=float)
        if forest.ndim == 0:
            forest = np.full(x.shape, float(forest))
        if forest.shape != x.shape or not np.isfinite(forest).all():
            raise ValueError("forest_proximity must be a finite 0..1 world field matching box")
        forest = np.clip(forest, 0, 1)

    def sampled(name, factor=1.0, offset=(0.0, 0.0)):
        return sample_material(materials[name], x, y,
            config.material_scale * factor / unit, offset, config.material_overlap)

    meadow = sampled("meadow")
    shore = sampled("shore", 1.04, (71, 29))
    deep_source = np.asarray(materials["deep_water"], dtype=float)[..., :3]
    shallow_source = _calibrated_shallow(materials["shallow_water"])
    deep_mean, shallow_mean = deep_source.mean((0, 1)), shallow_source.mean((0, 1))
    # Source means are fixed globally. Quiet the water's original white wavelets
    # rather than adding a procedural sparkling layer or a bright coastline rim.
    deep_tex = sampled("deep_water", 0.93)
    deep = deep_mean + (deep_tex - deep_mean) * config.deep_contrast
    shallow_tex = sample_material(shallow_source, x, y, config.material_scale * 1.08 / unit,
                                  (37, 101), config.material_overlap)
    shallow = shallow_mean + (shallow_tex - shallow_mean) * config.shallow_contrast

    # Coast-relative masks sample noise at the closest *physical* shore point.
    # The coarser field chooses exposed sandy reaches; the fine field breaks up
    # their widths. Non-sandy reaches genuinely allow grass to contact the water.
    cx, cy = fields.coast_x, fields.coast_y
    broad = 0.76 * _noise(cx, cy, 87 * unit, seed + 11) + 0.24 * _noise(cx, cy, 39 * unit, seed + 29)
    fine = _noise(x, y, 7.7 * unit, seed + 47)
    exposure = _step(config.sand_threshold, 0.78, broad)
    exposure *= 1.0 - config.forest_sand_suppression * forest
    exposure *= _step(.24, .65, _noise(cx, cy, 37 * unit, seed + 227))
    sand_width = config.max_sand_width * unit * exposure * (0.55 + 0.65 * fine)
    sand_presence = _step(0.55 * unit, 1.5 * unit, sand_width)
    distance = fields.coast_distance
    sand = sand_presence * (1 - _step(np.maximum(0, sand_width - 1.4 * unit),
                                       sand_width + 1.4 * unit, distance))
    sand *= fields.land_mask
    land = meadow * (1 - sand[..., None]) + shore * sand[..., None]

    # A subdued material contact at the wet land edge. There is no normal-based
    # bevel and no color-only dark stroke: bank pixels retain supplied textures.
    bank_patch = _step(0.27, 0.65, _noise(cx, cy, 21 * unit, seed + 83))
    bank_width = unit * (1.70 + 3.0 * exposure) * (0.6 + 0.7 * fine)
    bank = bank_patch * (1 - _step(0.0, bank_width, distance)) * fields.land_mask
    if "forest_floor" in materials:
        bank_material = shore * .58 + sampled("forest_floor", 1.04, (71, 29)) * .33
    else:
        bank_material = (meadow * (0.56 + 0.16 * forest[..., None])
                         + shore * (0.25 - 0.12 * forest[..., None]))
    land = land * (1 - bank[..., None]) + bank_material * bank[..., None]

    # A submerged, irregular shelf, independent of whether the dry edge is sandy.
    # Width and bottom visibility vary in world-space rather than forming a rim.
    depth_patch = _noise(cx, cy, 65 * unit, seed + 137)
    shelf_detail = _noise(x, y, 17 * unit, seed + 193)
    shelf_reaches = _noise(cx, cy, 34 * unit, seed + 251)
    shallow_width = unit * (config.shallow_min_width + 3 +
        2 * (config.shallow_max_width - config.shallow_min_width) * depth_patch +
        10 * exposure) * (.50 + .80 * shelf_reaches)
    # Keep actual authored seabed pixels legible in discrete broad patches. A
    # narrower, texture-broken depth boundary replaces the soft color glow.
    depth = (distance + unit * 5.0 * (shelf_detail - .5)) / shallow_width
    shelf = 1 - _step(.46, .96, depth)
    bottom_patches = _step(.34, .67, _noise(x, y, 31 * unit, seed + 307))
    shallow_alpha = shelf * config.shallow_strength * (.12 + .72 * bottom_patches)
    shallow_alpha *= ~fields.land_mask
    # Suppress source whitecaps only in the near-shore physical water. Beyond
    # this bounded band deep-water pixels are identical to the pass26 baseline.
    quiet = (1 - _step(0.0, shallow_width + 12 * unit, distance)) * (~fields.land_mask)
    coastal_deep = deep_mean + (deep-deep_mean) * (1 - .78 * quiet[..., None])
    water = coastal_deep * (1 - shallow_alpha[..., None]) + shallow * shallow_alpha[..., None]

    if config.antialias > 0:
        land_alpha = _step(-config.antialias * unit, config.antialias * unit, fields.signed_distance)
        # Artificial closing edges do not receive a cosmetic water-line blend.
        land_alpha = np.where(fields.nearest_boundary_status == ANALYSIS_CLIPPED,
                              fields.land_mask.astype(float), land_alpha)
    else:
        land_alpha = fields.land_mask.astype(float)
    rgb = water * (1 - land_alpha[..., None]) + land * land_alpha[..., None]
    image = Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8), "RGB")
    return CoastRender(image, land_alpha, fields.land_mask, fields.signed_distance,
                       fields.coast_distance, fields.nearest_coast_status,
                       sand, shallow_alpha, bank)


def render_trace(trace, box, materials, *, origin=(0.0, 0.0),
                 forest_proximity=None, config=None) -> CoastRender:
    """Convenience wrapper for the benchmark trace JSON/dict format."""
    config = config or CoastConfig()
    polygon, evidence = load_trace(trace, config.cell_size, origin)
    return render_coast(box, polygon, materials, evidence, forest_proximity, config)
