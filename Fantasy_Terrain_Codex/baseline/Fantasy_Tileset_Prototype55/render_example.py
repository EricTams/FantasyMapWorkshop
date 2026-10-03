"""Render an authored layout, export independent semantic axes and visible Tiled art."""
from pathlib import Path
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from kit_renderer import KitScene, T
from river_edges import compile_edges

ROOT = Path(__file__).resolve().parent
CODES = {'sand': 0, 'grass': 1, 'water': 2, 'plains': 3, 'tundra': 4, 'snow': 5, 'unknown': 255}
# The first ten GIDs preserve the previous terrain/forest/relief meanings.
SEMANTICS = [
    ('sand', 0, 'terrain', (204, 184, 141)),
    ('grass', 1, 'terrain', (82, 125, 51)),
    ('water', 2, 'terrain', (43, 85, 103)),
    ('plains', 3, 'terrain', (181, 165, 104)),
    ('unknown', 255, 'terrain', (79, 87, 83)),
    ('broadleaf_forest', -1, 'forest', (36, 66, 35)),
    ('pine_forest', -2, 'forest', (31, 65, 61)),
    ('hill', -3, 'relief', (143, 128, 102)),
    ('mountain', -4, 'relief', (106, 112, 119)),
    ('jungle', -5, 'forest', (44, 99, 55)),
    ('tundra', 4, 'terrain', (149, 146, 125)),
    ('snow', 5, 'terrain', (224, 233, 229)),
    ('ice', -6, 'ice', (158, 206, 217)),
]
TERRAIN_GIDS = {name: i + 1 for i, (name, _, axis, _) in enumerate(SEMANTICS) if axis == 'terrain'}
FOREST_GIDS = {'.': 0, 'D': 6, 'P': 7, 'J': 10}
ICE_GID = 13
OBJECT_FIRST_GID = len(SEMANTICS) + 1


def properties(values):
    """Keep independent boolean properties boolean in both JSON and XML exports."""
    return [{'name': key,
             'type': 'bool' if isinstance(value, bool) else 'int' if isinstance(value, int)
                     else 'float' if isinstance(value, float) else 'string',
             'value': value} for key, value in values.items()]


def write_tsx(path, name, records):
    ts = ET.Element('tileset', version='1.10', tiledversion='1.11.2', name=name,
                    tilewidth=str(T), tileheight=str(T), tilecount=str(len(records)),
                    columns='0', objectalignment='topleft')
    for i, (name, rel, props) in enumerate(records):
        with Image.open(path.parent / rel) as im:
            size = im.size
        tile = ET.SubElement(ts, 'tile', id=str(i), type=name)
        node = ET.SubElement(tile, 'properties')
        for prop in properties(props):
            value = str(prop['value']).lower() if prop['type'] == 'bool' else str(prop['value'])
            ET.SubElement(node, 'property', name=prop['name'], type=prop['type'], value=value)
        ET.SubElement(tile, 'image', source=rel, width=str(size[0]), height=str(size[1]))
    ET.indent(ts)
    ET.ElementTree(ts).write(path, encoding='UTF-8', xml_declaration=True)


def reconstruct(tmj):
    """Rebuild this export's visible image/object layers, using TSX top-left anchors."""
    data = json.loads(tmj.read_text())
    sprites = {}
    for link in data['tilesets']:
        p = (tmj.parent / link['source']).resolve()
        ts = ET.parse(p).getroot()
        assert ts.attrib['objectalignment'] == 'topleft'
        for tile in ts.findall('tile'):
            with Image.open(p.parent / tile.find('image').attrib['source']) as im:
                sprites[link['firstgid'] + int(tile.attrib['id'])] = im.convert('RGBA')
    canvas = Image.new('RGBA', (data['width'] * data['tilewidth'], data['height'] * data['tileheight']))
    for layer in data['layers']:
        if not layer.get('visible', True):
            continue
        assert layer.get('opacity', 1) == 1 and layer.get('x', 0) == layer.get('y', 0) == 0
        if layer['type'] == 'imagelayer':
            with Image.open(tmj.parent / layer['image']) as im:
                canvas.alpha_composite(im.convert('RGBA'), (0, 0))
        elif layer['type'] == 'objectgroup':
            for obj in layer['objects']:
                if 'gid' not in obj or not obj.get('visible', True):
                    continue
                sprite = sprites[obj['gid']]
                assert sprite.size == (obj['width'], obj['height']) and obj.get('rotation', 0) == 0
                assert round(obj['x']) == obj['x'] and round(obj['y']) == obj['y']
                canvas.alpha_composite(sprite, (round(obj['x']), round(obj['y'])))
        else:
            raise ValueError(f"Unsupported visible layer: {layer['type']}")
    return canvas.convert('RGB')


def ice_cells(scene):
    """Ice is an overlay axis and can never replace the underlying water identity."""
    height, width = len(scene['terrain_rows']), len(scene['terrain_rows'][0])
    cells = set()
    for cell in scene.get('ice_cells', []):
        assert len(cell) == 2 and all(type(v) is int for v in cell), cell
        row, col = cell
        assert 0 <= row < height and 0 <= col < width, cell
        assert (row, col) not in cells, f'Duplicate ice cell: {cell}'
        assert scene['terrain_rows'][row][col] == 'water', f'Ice requires underlying water: {cell}'
        cells.add((row, col))
    return cells


def mask_fields(kit):
    masks = {'land': kit.coast.land_alpha, 'forest_floor': kit.floor_mask,
             'forest_interior': kit.interior_mask, 'sand': kit.coast.sand_alpha,
             'shallow_water': kit.coast.shallow_alpha, 'bank': kit.coast.bank_alpha,
             'vegetation_clearance': kit.clearance_mask.astype(float)}
    if kit.river is not None:
        masks.update(river_water=kit.river.water_alpha, river_bank=kit.river.bank_alpha,
                     river_channel=kit.river.channel_mask.astype(float))
    if kit.fP.any():
        masks['pine_weight'] = kit.pine_weight
    if kit.fJ.any():
        masks['jungle_weight'] = kit.jungle_weight
    for name, mask in kit.cold_weights.items():
        masks[{'frost_heath': 'tundra_weight', 'snowfields': 'snow_weight'}[name]] = mask
    if kit.ice is not None:
        masks.update(ice_alpha=kit.ice.alpha, ice_valid=kit.ice.valid.astype(float))
    return masks


def render_kind(name, wildlife_names):
    if name.startswith('stag_shadow') or name.endswith('_shadow'):
        return 'shadow'
    if name in wildlife_names or name.startswith('white_stag'):
        return 'actor'
    if name.startswith('ice_edge_'):
        return 'ice_edge'
    if name.startswith('botanical_'):
        return 'botanical_resource'
    if name.startswith('mountain'):
        return 'mountain'
    if name.startswith('jungle_'):
        return 'jungle_edge'
    if '_edge_' in name:
        return 'tree'
    if name.startswith('scarlet_pepper'):
        return 'spices_scarlet_pepper'
    if name.startswith('crimson_spice'):
        return 'fantasy_spice_proposal'
    if name.startswith('vineyard_press_'):
        return 'vineyard_improvement'
    if name.startswith('mineral_'):
        return 'mineral_resource'
    return 'site_or_resource'


def tile_layer(layer_id, name, width, height, gids):
    return {'id': layer_id, 'name': name, 'type': 'tilelayer', 'width': width,
            'height': height, 'data': gids, 'x': 0, 'y': 0, 'opacity': 1, 'visible': False}


def object_layer(layer_id, name, objects, visible=False):
    return {'id': layer_id, 'name': name, 'type': 'objectgroup', 'draworder': 'index',
            'objects': objects, 'x': 0, 'y': 0, 'opacity': 1, 'visible': visible}


def cell_object(object_id, name, row, col, props):
    return {'id': object_id, 'name': name, 'x': col * T, 'y': row * T, 'width': T,
            'height': T, 'rotation': 0, 'visible': True,
            'properties': properties(dict(props, row=row, column=col))}


def river_export(scene, shape):
    """Keep authored edge topology and observed evidence in separate coordinate domains."""
    spec = scene.get('river_edges')
    evidence = scene.get('river_digitization', {})
    if spec:
        if evidence.get('paths'):
            raise ValueError('Choose authored shared-edge topology or source digitization, not both')
        paths, topology = compile_edges(spec, shape, T)
        mode = 'authored_shared_edges'
        provenance = spec.get('provenance', 'Explicit authored shared-edge routes')
        routes = spec.get('routes', [])
    else:
        paths, topology, routes = evidence.get('paths', []), None, []
        mode = 'source_trace' if paths else 'none'
        provenance = evidence.get('provenance', 'source-visible evidence; missing spans are not connected') if paths else 'none'
    record = {'status': 'Prototype55', 'input_mode': mode, 'provenance': provenance,
              'coordinate_order': 'integer grid corners [x,y]; adjacent cells [row,column]',
              'render_pass': 'baked_ground', 'topology': topology, 'routes': routes,
              'authored_spec': spec or None, 'source_digitization': evidence or None}
    return paths, record


def river_cell_sides(topology):
    sides = {}
    for edge in (topology or {}).get('edges', []):
        for owner in edge['adjacent_cells']:
            sides.setdefault(tuple(owner['cell']), set()).add(owner['side'])
    return sides


def river_path_properties(path, record):
    props = {'role': path.get('role', 'visible_main'),
             'evidence_provenance': record['provenance'], 'input_mode': record['input_mode'],
             'render_pass': 'baked_ground', 'semantic_only': True}
    if record['topology'] is not None:
        props.update(route_id=path['route_id'], semantic_edge_ids_json=json.dumps(path['semantic_edge_ids']),
                     route_metadata_json=json.dumps(next(route for route in record['routes'] if route['id'] == path['route_id'])))
    else:
        props['source_path_json'] = json.dumps(path)
    return props


def river_edge_properties(edge, paths, record):
    memberships = []
    for path, route in zip(paths, record['routes']):
        segments = [i for i, edge_id in enumerate(path['semantic_edge_ids']) if edge_id == edge['id']]
        if segments:
            memberships.append({'route_id': route['id'], 'segment_indices': segments,
                                'route_metadata': {key: value for key, value in route.items() if key != 'nodes'}})
    props = {'edge_id': edge['id'], 'grid_start_x': int(edge['grid_start'][0]),
             'grid_start_y': int(edge['grid_start'][1]), 'grid_end_x': int(edge['grid_end'][0]),
             'grid_end_y': int(edge['grid_end'][1]),
             'adjacent_cells_json': json.dumps(edge['adjacent_cells']),
             'route_memberships_json': json.dumps(memberships),
             'evidence_provenance': record['provenance'], 'semantic_only': True,
             'input_mode': 'authored_shared_edges', 'render_pass': 'baked_ground'}
    for i, owner in enumerate(edge['adjacent_cells']):
        props.update({f'owner_{i}_row': int(owner['cell'][0]),
                      f'owner_{i}_column': int(owner['cell'][1]), f'owner_{i}_side': owner['side']})
    return props


def build(example):
    example = example.resolve()
    scene = json.loads((example / 'scene.json').read_text())
    features = json.loads((example / 'features.json').read_text())
    frozen = ice_cells(scene)
    kit = KitScene(scene, example / 'shoreline.json', features)
    river_paths, river_record = river_export(scene, (kit.H, kit.W))
    assert river_record['topology'] == kit.river_edge_records
    river_sides = river_cell_sides(river_record['topology'])
    expected_y = [y * T for y in range(kit.H + 1)]
    expected_x = [[x * T for x in range(kit.W + 1)] for _ in range(kit.H + 1)]
    if (scene['geometry']['row_boundary_y'] != expected_y or
            scene['geometry']['column_boundary_x_by_row'] != expected_x or
            scene['crop_bounds_px'] != [0, 0, kit.W * T, kit.H * T]):
        raise ValueError('Tiled export requires an origin-aligned orthogonal 128px grid. Use render_scene.py for observed/warped scenes.')
    out = example / 'generated'
    out.mkdir(exist_ok=True)
    (out / 'river_edges.json').write_text(json.dumps(river_record, indent=2) + '\n')
    for directory in ('sprites', 'semantic_tiles', 'masks'):
        (out / directory).mkdir(exist_ok=True)
        # All files here are disposable derivatives, including obsolete masks/labels.
        for old in (out / directory).glob('*.png'):
            old.unlink()
    whole = kit.render()
    whole.save(out / 'preview.png')
    kit.grid(whole).save(out / 'grid.png')
    kit.render(include_objects=False).save(out / 'ground_and_forest_interior.png')
    masks = mask_fields(kit)
    for name, mask in masks.items():
        Image.fromarray(np.round(np.clip(mask, 0, 1) * 65535).astype('uint16')).save(out / 'masks' / f'{name}.png')
    wildlife = json.loads((ROOT / 'assets/wildlife/wildlife_manifest.json').read_text())
    wildlife_names = {q['name'] for q in wildlife['sprites']}
    records, lookup, objects = [], {}, []
    for depth, sprite, left, top, name in kit.object_instances():
        key = (name, sprite.size, hashlib.sha256(sprite.tobytes()).hexdigest())
        if key not in lookup:
            idx = len(records)
            filename = f'{idx:02d}_{name}.png'
            sprite.save(out / 'sprites' / filename)
            lookup[key] = idx
            records.append((name, 'sprites/' + filename,
                            {'asset_name': name, 'derived_at_render_size': True,
                             'render_kind': render_kind(name, wildlife_names)}))
        objects.append({'id': len(objects) + 1, 'name': name, 'gid': OBJECT_FIRST_GID + lookup[key],
                        'x': left, 'y': top, 'width': sprite.width, 'height': sprite.height,
                        'rotation': 0, 'visible': True,
                        'properties': properties({'depth_y': float(depth)})})
    write_tsx(out / 'objects.tsx', 'Rendered sprite instances', records)
    semantic = []
    for name, code, axis, color in SEMANTICS:
        Image.new('RGB', (T, T), color).save(out / 'semantic_tiles' / f'{name}.png')
        props = {'material_code': code, 'semantic_axis': axis, 'semantic_only': True}
        if axis == 'ice':
            props.update(independent_of_terrain=True, underlying_terrain_code=CODES['water'])
        semantic.append((name, f'semantic_tiles/{name}.png', props))
    write_tsx(out / 'semantics.tsx', 'Semantic IDs (hidden)', semantic)
    height, width = kit.ids.shape
    hills, mountains = {tuple(c) for c in scene.get('hill_cells', [])}, {tuple(c) for c in scene.get('mountain_cells', [])}
    cells = []
    for row in range(height):
        for col in range(width):
            cells.append(cell_object(len(objects) + len(cells) + 1, f'r{row}_c{col}', row, col,
                                     {'material_id': int(kit.ids[row, col]),
                                      'terrain_kind': scene['terrain_rows'][row][col],
                                      'forest': bool(kit.f[row, col]),
                                      'forest_kind': scene['forest_rows'][row][col],
                                      'relief_kind': 'M' if (row, col) in mountains else 'H' if (row, col) in hills else '.',
                                      'ice': (row, col) in frozen,
                                      **{f'river_{side}': side in river_sides.get((row, col), set())
                                         for side in 'NESW'}}))
    data = {'type': 'map', 'version': '1.10', 'tiledversion': '1.11.2', 'orientation': 'orthogonal',
            'renderorder': 'right-down', 'width': width, 'height': height, 'tilewidth': T,
            'tileheight': T, 'infinite': False, 'nextlayerid': 12,
            'nextobjectid': len(objects) + len(cells) + 1,
            'tilesets': [{'firstgid': 1, 'source': 'semantics.tsx'},
                         {'firstgid': OBJECT_FIRST_GID, 'source': 'objects.tsx'}],
            'properties': properties({
                'renderer': '../../../render_example.py + kit_renderer.py + coast_renderer.py',
                'art_baseline': 'Prototype55: authored shared-edge rivers, cold terrain, independent pack ice, botanical resources, riding horses and painted waterline wildlife and real-jungle vegetation',
                'ground_is_sample_specific': True,
                'ice_semantics': 'Independent ice_cells overlay; underlying terrain remains water (material code 2)',
                'semantic_axes': 'terrain,forest,relief,resource,improvement,ice,river_edges',
                'river_semantics': 'Layer 11 contains authored shared edges only; layer 6 retains source traces or explicit authored route centerlines. River paint is baked in layer 1.',
            }) + [{'name': 'layout', 'type': 'file', 'value': '../scene.json'},
                  {'name': 'river_edge_records', 'type': 'file', 'value': 'river_edges.json'}],
            'layers': [
                {'id': 1, 'name': 'Rendered ground, vegetation interior, river, vineyard and water-resource passes (sample-specific)',
                 'type': 'imagelayer', 'image': 'ground_and_forest_interior.png',
                 'x': 0, 'y': 0, 'opacity': 1, 'visible': True},
                object_layer(2, 'Depth-sorted vegetation, ice edges, actors and sites', objects, True),
                tile_layer(3, 'Terrain semantic IDs (edit source JSON to rerender)', width, height,
                           [TERRAIN_GIDS[v] for row in scene['terrain_rows'] for v in row]),
                tile_layer(4, 'Forest semantic IDs', width, height,
                           [FOREST_GIDS[v] for row in scene['forest_rows'] for v in row]),
                object_layer(5, 'Logical cell identities', cells),
            ]}
    river_objects = []
    for path in river_paths:
        points = path.get('world_nodes') or [[q[0] * T, q[1] * T] for q in path['fractional_grid_nodes']]
        x, y = points[0]
        river_objects.append({'id': data['nextobjectid'] + len(river_objects), 'name': path.get('path_id', 'authored_river'),
                              'x': x, 'y': y, 'width': 0, 'height': 0, 'rotation': 0, 'visible': True,
                              'polyline': [{'x': a - x, 'y': b - y} for a, b in points],
                              'properties': properties(river_path_properties(path, river_record))})
    data['layers'].append(object_layer(6, 'River source traces or explicit authored route centerlines (hidden; no inferred links)', river_objects))
    data['nextobjectid'] += len(river_objects)
    data['layers'].append(tile_layer(7, 'Relief semantic IDs (H/M independent of terrain and forest)', width, height,
                                    [9 if (row, col) in mountains else 8 if (row, col) in hills else 0
                                     for row in range(height) for col in range(width)]))
    metadata = [(8, 'Resource category identities; water resources use their recorded baked passes', kit.resource_metadata()),
                (9, 'Independent improvement identities; presses are upright objects', kit.improvement_metadata())]
    for layer_id, name, source_records in metadata:
        identity_objects = []
        for record in source_records:
            row, col = record['cell']
            identity_objects.append(cell_object(data['nextobjectid'] + len(identity_objects),
                                                record['source_category'] + f'_r{row}_c{col}', row, col,
                                                {k: v for k, v in record.items() if k != 'cell'}))
        data['layers'].append(object_layer(layer_id, name, identity_objects))
        data['nextobjectid'] += len(identity_objects)
    data['layers'].append(tile_layer(10, 'Independent ice semantic IDs (underlying terrain stays water)', width, height,
                                    [ICE_GID if (row, col) in frozen else 0
                                     for row in range(height) for col in range(width)]))
    edge_objects = []
    for edge in (river_record['topology'] or {}).get('edges', []):
        x, y = [int(v) * T for v in edge['grid_start']]
        xx, yy = [int(v) * T for v in edge['grid_end']]
        edge_objects.append({'id': data['nextobjectid'] + len(edge_objects), 'name': edge['id'],
                             'x': x, 'y': y, 'width': 0, 'height': 0, 'rotation': 0, 'visible': True,
                             'polyline': [{'x': 0, 'y': 0}, {'x': xx - x, 'y': yy - y}],
                             'properties': properties(river_edge_properties(edge, river_paths, river_record))})
    data['layers'].append(object_layer(11, 'Shared-edge river topology (authored only; no duplicate paint)', edge_objects))
    data['nextobjectid'] += len(edge_objects)
    tmj = out / 'sample.tmj'
    tmj.write_text(json.dumps(data, indent=2) + '\n')
    restored = reconstruct(tmj)
    difference = int(np.abs(np.asarray(restored, dtype=int) - np.asarray(whole, dtype=int)).max())
    assert difference == 0, difference
    qa = kit.qa()
    qa.update({'generic_layout_independent_of_benchmark': True,
               'upright_objects_exported_from_single_helper': True,
               'relief_semantics_independent_of_base_and_forest': True,
               'ice_semantics_independent_of_base_terrain': True,
               'ice_cells_keep_water_terrain': all(kit.ids[r, c] == CODES['water'] for r, c in frozen),
               'ice_cells': len(frozen), 'tundra_cells': int((kit.ids == 4).sum()),
               'snow_cells': int((kit.ids == 5).sum()), 'exported_masks': sorted(masks),
               'river_route_provenance': river_record['provenance'],
               'river_input_mode': river_record['input_mode'], 'river_shared_edge_records': len(edge_objects),
               'river_centerline_records': len(river_objects),
               'river_edge_records_match_runtime': river_record['topology'] == kit.river_edge_records,
               'river_paint_baked_only': True, 'status': 'Prototype55',
               'tiled_visible_layer_reconstruction_max_difference': difference,
               'tiled_native_application_opened': False,
               'tiled_validation': 'Local JSON/XML structural checks, relative references and pixel reconstruction only; no native Tiled run',
               'terrain_cells': width * height, 'visible_object_instances': len(objects),
               'unique_render_size_sprites': len(records), 'cell_identity_records': len(cells)})
    (out / 'validation.json').write_text(json.dumps(qa, indent=2) + '\n')
    print(json.dumps(qa, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--example', type=Path, default=ROOT / 'examples/jungle_mixed')
    args = parser.parse_args()
    build(args.example)
