"""Read-only asset, Tiled structure/reference, independent-axis and pixel verification."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from render_example import (CODES, FOREST_GIDS, ICE_GID, OBJECT_FIRST_GID, SEMANTICS,
                            TERRAIN_GIDS, KitScene, T, ice_cells, mask_fields,
                            reconstruct, render_kind)
from river_edges import compile_edges

ROOT = Path(__file__).resolve().parent


def property_values(record):
    values = record.get('properties', [])
    assert len({p['name'] for p in values}) == len(values), 'Duplicate property names'
    for prop in values:
        assert isinstance(prop['name'], str)
        expected = {'bool': bool, 'int': int, 'float': (int, float), 'string': str, 'file': str}[prop['type']]
        assert isinstance(prop['value'], expected), prop
        if prop['type'] in ('int', 'float'):
            assert not isinstance(prop['value'], bool), prop
    return {p['name']: p['value'] for p in values}


def reference(base, value):
    assert isinstance(value, str) and not Path(value).is_absolute(), value
    target = (base / value).resolve()
    assert target.is_relative_to(ROOT) and target.is_file(), value
    return target


def tiled_structure(tmj, data):
    """Validate the supported export shape; this is not a native Tiled application test."""
    assert data['type'] == 'map' and data['orientation'] == 'orthogonal'
    assert data['renderorder'] == 'right-down' and data['infinite'] is False
    assert data['tilewidth'] == data['tileheight'] == T
    assert all(type(data[key]) is int and data[key] > 0 for key in ('width', 'height', 'nextlayerid', 'nextobjectid'))
    assert data['tilesets'] == [{'firstgid': 1, 'source': 'semantics.tsx'},
                                {'firstgid': OBJECT_FIRST_GID, 'source': 'objects.tsx'}]
    refs, tiles = [], {}
    for link in data['tilesets']:
        path = reference(tmj.parent, link['source'])
        refs.append(path)
        ts = ET.parse(path).getroot()
        assert ts.tag == 'tileset' and ts.attrib['objectalignment'] == 'topleft'
        assert int(ts.attrib['columns']) == 0
        assert int(ts.attrib['tilewidth']) == int(ts.attrib['tileheight']) == T
        children = ts.findall('tile')
        assert int(ts.attrib['tilecount']) == len(children)
        assert [int(t.attrib['id']) for t in children] == list(range(len(children)))
        if link['firstgid'] == 1:
            assert len(children) == len(SEMANTICS)
        for tile in children:
            gid = link['firstgid'] + int(tile.attrib['id'])
            assert gid not in tiles, f'Overlapping tileset GID: {gid}'
            assert len(tile.findall('image')) == 1
            image = tile.find('image')
            target = reference(path.parent, image.attrib['source'])
            refs.append(target)
            with Image.open(target) as im:
                size = im.size
                im.verify()
            assert size == (int(image.attrib['width']), int(image.attrib['height']))
            props = tile.findall('./properties/property')
            assert len({p.attrib['name'] for p in props}) == len(props)
            props = {p.attrib['name']: p.attrib for p in props}
            tiles[gid] = {'name': tile.attrib['type'], 'image': target, 'size': size, 'properties': props}
    for gid, (name, code, axis, _) in enumerate(SEMANTICS, 1):
        tile = tiles[gid]
        assert tile['name'] == name and tile['size'] == (T, T)
        assert tile['properties']['material_code'] == {'name': 'material_code', 'type': 'int', 'value': str(code)}
        assert tile['properties']['semantic_axis']['value'] == axis
        assert tile['properties']['semantic_only']['value'] == 'true'
    assert tiles[ICE_GID]['properties']['independent_of_terrain']['value'] == 'true'
    assert tiles[ICE_GID]['properties']['underlying_terrain_code']['value'] == str(CODES['water'])
    layers = {layer['id']: layer for layer in data['layers']}
    assert len(layers) == len(data['layers']) and [layer['id'] for layer in data['layers']] == list(range(1, 12))
    assert data['nextlayerid'] > max(layers)
    all_ids = []
    for layer in data['layers']:
        assert layer['x'] == layer['y'] == 0 and layer['opacity'] == 1
        assert layer['visible'] is (layer['id'] in (1, 2))
        if layer['type'] == 'imagelayer':
            assert layer['id'] == 1
            target = reference(tmj.parent, layer['image'])
            refs.append(target)
            with Image.open(target) as im:
                assert im.size == (data['width'] * T, data['height'] * T)
                im.verify()
        elif layer['type'] == 'tilelayer':
            assert layer['id'] in (3, 4, 7, 10)
            assert layer['width'] == data['width'] and layer['height'] == data['height']
            assert len(layer['data']) == data['width'] * data['height']
            assert all(type(gid) is int and (gid == 0 or gid in tiles) for gid in layer['data'])
        elif layer['type'] == 'objectgroup':
            assert layer['id'] in (2, 5, 6, 8, 9, 11) and layer['draworder'] == 'index'
            for obj in layer['objects']:
                assert type(obj['id']) is int and obj['id'] > 0
                all_ids.append(obj['id'])
                assert isinstance(obj['name'], str) and obj['rotation'] == 0 and obj['visible'] is True
                assert all(isinstance(obj[k], (int, float)) and not isinstance(obj[k], bool)
                           for k in ('x', 'y', 'width', 'height'))
                assert obj['width'] >= 0 and obj['height'] >= 0
                assert all(np.isfinite(obj[k]) for k in ('x', 'y', 'width', 'height'))
                if layer['id'] in (6, 11):
                    assert len(obj['polyline']) >= 2
                    assert all(set(point) == {'x', 'y'} and all(isinstance(value, (int, float)) and not isinstance(value, bool) and np.isfinite(value) for value in point.values()) for point in obj['polyline'])
                property_values(obj)
                if 'gid' in obj:
                    assert layer['id'] == 2 and type(obj['gid']) is int and obj['gid'] >= OBJECT_FIRST_GID
                    assert obj['gid'] in tiles
                    assert tiles[obj['gid']]['name'] == obj['name']
                    assert tiles[obj['gid']]['size'] == (obj['width'], obj['height'])
                else:
                    assert layer['id'] != 2
        else:
            raise AssertionError(f"Unexpected layer type: {layer['type']}")
    assert len(set(all_ids)) == len(all_ids) and data['nextobjectid'] > max(all_ids, default=0)
    property_values(data)
    for prop in data.get('properties', []):
        if prop['type'] == 'file':
            refs.append(reference(tmj.parent, prop['value']))
    return layers, tiles, refs


def verify_rivers(scene, shape, layers, record):
    """Independently recover each exported edge and its ownership from Tiled properties."""
    spec, evidence = scene.get('river_edges'), scene.get('river_digitization', {})
    assert record['status'] == 'Prototype55' and record['render_pass'] == 'baked_ground'
    assert record['authored_spec'] == (spec or None)
    assert record['source_digitization'] == (evidence or None)
    if spec:
        assert not evidence.get('paths'), 'Observed traces must not be silently snapped or merged'
        paths, topology = compile_edges(spec, shape, T)
        provenance = spec.get('provenance', 'Explicit authored shared-edge routes')
        assert record['input_mode'] == 'authored_shared_edges'
        assert record['routes'] == spec.get('routes', [])
        assert len({route['id'] for route in record['routes']}) == len(record['routes'])
    else:
        paths, topology = evidence.get('paths', []), None
        provenance = evidence.get('provenance', 'source-visible evidence; missing spans are not connected') if paths else 'none'
        assert record['input_mode'] == ('source_trace' if paths else 'none')
        assert record['routes'] == []
    assert record['provenance'] == provenance and record['topology'] == topology
    assert not layers[6]['visible'] and not layers[11]['visible']
    assert len(layers[6]['objects']) == len(paths)
    for obj, path in zip(layers[6]['objects'], paths):
        # Source nodes retain exact supplied coordinates; authored nodes come only from compile_edges.
        points = path.get('world_nodes') or [[q[0] * T, q[1] * T] for q in path['fractional_grid_nodes']]
        x, y = points[0]
        assert (obj['x'], obj['y']) == (x, y)
        assert obj['polyline'] == [{'x': a - x, 'y': b - y} for a, b in points]
        assert obj['name'] == path.get('path_id', 'authored_river') and 'gid' not in obj
        props = property_values(obj)
        expected = {'role': path.get('role', 'visible_main'), 'evidence_provenance': provenance,
                    'input_mode': record['input_mode'], 'render_pass': 'baked_ground', 'semantic_only': True}
        if topology is not None:
            assert json.loads(props.pop('semantic_edge_ids_json')) == path['semantic_edge_ids']
            assert json.loads(props.pop('route_metadata_json')) == next(route for route in record['routes'] if route['id'] == path['route_id'])
            expected['route_id'] = path['route_id']
        else:
            assert json.loads(props.pop('source_path_json')) == path
        assert props == expected
    edges = (topology or {}).get('edges', [])
    assert len(layers[11]['objects']) == len(edges)
    assert len({obj['name'] for obj in layers[11]['objects']}) == len(edges)
    cell_sides = {}
    for obj, edge in zip(layers[11]['objects'], edges):
        props = property_values(obj)
        assert obj['name'] == props['edge_id'] == edge['id'] and 'gid' not in obj
        recovered = {'id': props['edge_id'],
                     'grid_start': [props['grid_start_x'], props['grid_start_y']],
                     'grid_end': [props['grid_end_x'], props['grid_end_y']],
                     'adjacent_cells': json.loads(props['adjacent_cells_json'])}
        assert recovered == edge
        assert all(type(v) is int for v in recovered['grid_start'] + recovered['grid_end'])
        a, b = recovered['grid_start'], recovered['grid_end']
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
        assert (obj['x'], obj['y'], obj['width'], obj['height']) == (a[0] * T, a[1] * T, 0, 0)
        assert obj['polyline'] == [{'x': 0, 'y': 0}, {'x': (b[0] - a[0]) * T, 'y': (b[1] - a[1]) * T}]
        assert props['input_mode'] == 'authored_shared_edges' and props['semantic_only'] is True
        assert props['render_pass'] == 'baked_ground' and props['evidence_provenance'] == provenance
        members = []
        for path, route in zip(paths, record['routes']):
            indices = [i for i, value in enumerate(path['semantic_edge_ids']) if value == edge['id']]
            if indices:
                members.append({'route_id': route['id'], 'segment_indices': indices,
                                'route_metadata': {key: value for key, value in route.items() if key != 'nodes'}})
        assert json.loads(props['route_memberships_json']) == members and members
        for i, owner in enumerate(recovered['adjacent_cells']):
            row, col = owner['cell']
            assert 0 <= row < shape[0] and 0 <= col < shape[1] and owner['side'] in 'NESW'
            assert [props[f'owner_{i}_row'], props[f'owner_{i}_column']] == [row, col]
            assert props[f'owner_{i}_side'] == owner['side']
            cell_sides.setdefault((row, col), set()).add(owner['side'])
    for obj in layers[5]['objects']:
        props = property_values(obj)
        for side in 'NESW':
            assert props[f'river_{side}'] is (side in cell_sides.get((props['row'], props['column']), set()))
    if topology is not None:
        assert topology['edge_count'] == len(edges)
        assert topology['all_segments_unit_grid_edges'] is True
    return topology, paths


def main(example=None):
    sums = ROOT / 'SHA256SUMS.txt'
    if sums.exists():
        for line in sums.read_text().splitlines():
            digest, rel = line.split('  ', 1)
            target = reference(ROOT, rel)
            assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, rel
    inventory = json.loads((ROOT / 'dependency_inventory.json').read_text())
    checked = 0
    for record in inventory['assets']:
        path = reference(ROOT, record['file'])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], f"Asset changed; update reviewed inventory: {record['file']}"
        with Image.open(path) as image:
            image.verify()
        checked += 1
    example = (example or ROOT / 'examples/jungle_mixed').resolve()
    tmj = example / 'generated/sample.tmj'
    data = json.loads(tmj.read_text())
    layers, tiles, refs = tiled_structure(tmj, data)
    scene = json.loads((example / 'scene.json').read_text())
    features = json.loads((example / 'features.json').read_text())
    height, width = data['height'], data['width']
    assert len(scene['terrain_rows']) == len(scene['forest_rows']) == height
    assert all(len(row) == width for row in scene['terrain_rows'] + scene['forest_rows'])
    assert scene['geometry']['row_boundary_y'] == [row * T for row in range(height + 1)]
    assert scene['geometry']['column_boundary_x_by_row'] == [[col * T for col in range(width + 1)] for _ in range(height + 1)]
    assert scene['crop_bounds_px'] == [0, 0, width * T, height * T]
    frozen = ice_cells(scene)
    assert layers[3]['data'] == [TERRAIN_GIDS[v] for row in scene['terrain_rows'] for v in row]
    assert layers[4]['data'] == [FOREST_GIDS[v] for row in scene['forest_rows'] for v in row]
    hills, mountains = {tuple(c) for c in scene.get('hill_cells', [])}, {tuple(c) for c in scene.get('mountain_cells', [])}
    assert layers[7]['data'] == [9 if (row, col) in mountains else 8 if (row, col) in hills else 0
                                 for row in range(height) for col in range(width)]
    assert layers[10]['data'] == [ICE_GID if (row, col) in frozen else 0
                                  for row in range(height) for col in range(width)]
    cells = layers[5]['objects']
    assert len(cells) == width * height and len({obj['name'] for obj in cells}) == len(cells)
    for i, obj in enumerate(cells):
        row, col = divmod(i, width)
        props = property_values(obj)
        assert obj['name'] == f'r{row}_c{col}' and [props['row'], props['column']] == [row, col]
        assert (obj['x'], obj['y'], obj['width'], obj['height']) == (col * T, row * T, T, T)
        assert props['terrain_kind'] == scene['terrain_rows'][row][col]
        assert props['material_id'] == CODES[props['terrain_kind']]
        assert props['forest_kind'] == scene['forest_rows'][row][col]
        assert props['forest'] is (props['forest_kind'] in ('D', 'P', 'J'))
        assert props['relief_kind'] == ('M' if (row, col) in mountains else 'H' if (row, col) in hills else '.')
        assert props['ice'] is ((row, col) in frozen)
        if props['ice']:
            assert props['material_id'] == CODES['water'] and layers[3]['data'][i] == TERRAIN_GIDS['water']
    river_record = json.loads((tmj.parent / 'river_edges.json').read_text())
    topology, river_paths = verify_rivers(scene, (height, width), layers, river_record)
    feature_data = features['rendered_features']
    expected_resources = [f for f in feature_data if f.get('kind') == 'resource' or f['asset'].startswith('wildlife_')]
    resources = layers[8]['objects']
    assert len(resources) == len(expected_resources)
    manifest = json.loads((ROOT / 'assets/wildlife/wildlife_manifest.json').read_text())
    registry = json.loads((ROOT / 'resource_semantics.json').read_text())
    visible = layers[2]['objects']
    water_count, painted_count, partial_count = 0, 0, 0
    for obj, feat in zip(resources, expected_resources):
        props = property_values(obj)
        row, col = feat['cell']
        assert [props['row'], props['column']] == [row, col]
        assert (obj['x'], obj['y'], obj['width'], obj['height']) == (col * T, row * T, T, T)
        assert props['asset_identifier'] == feat['asset']
        assert props['semantic_resource_code'] == registry['categories'].get(props['source_category'], 0)
        if feat['asset'].startswith('wildlife_'):
            group = manifest['groups'][feat['asset'][9:-4]]
            assert props['source_category'] == group['source_category']
            if group.get('water_resource'):
                water_count += 1
                painted = bool(group.get('painted_waterline'))
                painted_count += int(painted)
                assert props['render_pass'] == ('baked_painted_waterline51' if painted else 'baked_water_treatment43')
                partial = group['source_category'] in ('clam', 'clams', 'crab', 'crabs')
                partial_count += int(partial)
                if partial:
                    assert props['implementation_status'].startswith('partial;')
                    assert 'provisional' in props['implementation_status']
                else:
                    assert props['implementation_status'].startswith('prototype;')
                    assert 'partial' not in props['implementation_status'] and 'provisional' not in props['implementation_status']
                if group['source_category'] == 'whale':
                    assert painted and not partial
                names = {manifest['sprites'][q['sprite']]['name'] for q in group['instances']}
                assert not any(v['name'] in names or v['name'].removesuffix('_shadow') in names for v in visible)
    improvements = layers[9]['objects']
    expected_improvements = [f for f in feature_data if f.get('kind') == 'improvement']
    assert len(improvements) == len(expected_improvements)
    improvement_registry = json.loads((ROOT / 'improvement_semantics.json').read_text())
    for obj, feat in zip(improvements, expected_improvements):
        props = property_values(obj)
        assert [props['row'], props['column']] == feat['cell']
        assert props['asset_identifier'] == feat['asset'] and props['independent_of_resource_id'] is True
        assert props['semantic_improvement_code'] == improvement_registry['categories'].get(props['source_category'], 0)
    grape_records = [o for o in resources if property_values(o)['asset_identifier'] == 'grapes_resource.png']
    if grape_records:
        assert all(property_values(o)['render_pass'] == 'baked_vineyard_field46' for o in grape_records)
        assert not any(o['name'].startswith('grapes_plot_') for o in visible)
    expected_presses = sum(f['asset'] == 'vineyard_press.png' for f in expected_improvements)
    assert sum(o['name'].startswith('vineyard_press_') for o in visible) == expected_presses
    # Compare exported names, order, anchors, pixels and independent identity records
    # directly with the same runtime helpers used to draw them.
    kit = KitScene(scene, example / 'shoreline.json', features)
    assert kit.river_edge_records == topology
    if kit.river is not None:
        assert list(kit.river.path_ids) == [path.get('path_id', 'authored_river') for path in river_paths]
    else:
        assert not river_paths
    assert not any(obj['name'].startswith('river') for obj in visible), 'River paint must remain baked in the ground layer'
    instances = kit.object_instances()
    assert len(instances) == len(visible)
    wildlife_names = {q['name'] for q in manifest['sprites']}
    exported_sprites = {}
    for obj, (depth, sprite, left, top, name) in zip(visible, instances):
        assert (obj['name'], obj['x'], obj['y'], obj['width'], obj['height']) == (name, left, top, sprite.width, sprite.height)
        assert property_values(obj)['depth_y'] == float(depth)
        tile = tiles[obj['gid']]
        assert tile['properties']['asset_name']['value'] == name
        assert tile['properties']['derived_at_render_size']['value'] == 'true'
        assert tile['properties']['render_kind']['value'] == render_kind(name, wildlife_names)
        if obj['gid'] not in exported_sprites:
            with Image.open(tile['image']) as im:
                exported_sprites[obj['gid']] = np.asarray(im.convert('RGBA')).copy()
        assert np.array_equal(exported_sprites[obj['gid']], np.asarray(sprite.convert('RGBA'))), name
        assert not name.startswith('mushroom'), 'J must use reviewed jungle artwork, never mushroom fallback'
    assert {obj['gid'] for obj in visible} == {gid for gid in tiles if gid >= OBJECT_FIRST_GID}
    for exported, runtime in ((resources, kit.resource_metadata()), (improvements, kit.improvement_metadata())):
        assert len(exported) == len(runtime)
        for obj, record in zip(exported, runtime):
            props = property_values(obj)
            assert props == dict({k: v for k, v in record.items() if k != 'cell'}, row=record['cell'][0], column=record['cell'][1])
    botanical_manifest = json.loads((ROOT / 'assets/botanicals/botanical_manifest.json').read_text())
    botanical_variants = {q['category']: len(q['variants']) for q in botanical_manifest['resources']}
    expected_botanicals = Counter()
    for feat in feature_data:
        if feat['asset'].startswith('botanical_'):
            kind = feat['asset'][10:-4]
            expected_botanicals[f'botanical_{kind}_{sum(feat["cell"]) % botanical_variants[kind]}'] += 1
    assert Counter(obj['name'] for obj in visible if obj['name'].startswith('botanical_')) == expected_botanicals
    ice_instances = kit.ice.objects(kit.forward, T, named=True) if kit.ice is not None else []
    assert Counter(obj['name'] for obj in visible if obj['name'].startswith('ice_edge_')) == Counter(q[4] for q in ice_instances)
    assert all(q[4] in ('ice_edge_0', 'ice_edge_1', 'ice_edge_2') for q in ice_instances)
    masks = mask_fields(kit)
    assert {p.stem for p in (tmj.parent / 'masks').glob('*.png')} == set(masks)
    for name, mask in masks.items():
        with Image.open(tmj.parent / 'masks' / f'{name}.png') as im:
            assert im.size == (width * T, height * T)
            actual = np.asarray(im).copy()
        expected = np.round(np.clip(mask, 0, 1) * 65535).astype('uint16')
        assert np.array_equal(actual, expected), name
    with Image.open(tmj.parent / 'preview.png') as im:
        full = np.asarray(im.convert('RGB'), dtype=int)
    assert np.array_equal(full, np.asarray(kit.render().convert('RGB'), dtype=int)), 'Preview differs from runtime render'
    rebuilt = np.asarray(reconstruct(tmj), dtype=int)
    assert full.shape == rebuilt.shape
    diff = int(np.abs(full - rebuilt).max())
    assert diff == 0
    print(json.dumps({'canonical_assets_checked': checked, 'tiled_references_checked': len(refs),
                      'discrete_semantic_cells_checked': len(cells), 'semantic_gid_count': len(SEMANTICS),
                      'first_visible_sprite_gid': OBJECT_FIRST_GID, 'export_maximum_channel_difference': diff,
                      'resource_identity_records': len(resources), 'improvement_identity_records': len(improvements),
                      'grape_field_records': len(grape_records), 'upright_press_objects': expected_presses,
                      'botanical_actor_objects': sum(expected_botanicals.values()),
                      'water_resource_pass_records': water_count, 'painted_waterline_records': painted_count,
                      'partial_water_records': partial_count, 'ice_cells': len(frozen),
                      'ice_edge_objects': len(ice_instances), 'mask_files_checked': len(masks),
                      'tundra_cells': sum(v == 'tundra' for row in scene['terrain_rows'] for v in row),
                      'snow_cells': sum(v == 'snow' for row in scene['terrain_rows'] for v in row),
                      'river_input_mode': river_record['input_mode'],
                      'river_shared_edge_records': len(layers[11]['objects']),
                      'river_centerline_records': len(river_paths),
                      'river_junction_nodes': len((topology or {}).get('junction_nodes', [])),
                      'river_edge_records_match_runtime': True, 'river_paint_baked_only': True,
                      'tiled_structural_validation': 'Supported JSON/XML export shape and all relative file references',
                      'native_tiled_validation': False,
                      'status': 'Prototype55 structural, independent semantic-axis and exact reconstruction checks passed; visual quality requires separate review'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--example', type=Path)
    args = parser.parse_args()
    main(args.example.resolve() if args.example else None)
