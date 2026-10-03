import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {TERRAIN_FAMILIES,terrainVariant,forestKind} from '../terrain.js';
import {generateWorld} from '../generator.js';

test('opening map represents every supported terrain, forest and relief type',()=>{
 const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
 const value=id=>html.match(new RegExp(`id="${id}"[^>]*value="([^"]+)"`))[1];
 const settings=Object.fromEntries(['land','ruggedness','moisture','forest','resources'].map(k=>[k,+value(k)]));
 const world=generateWorld(value('seed'),settings);
 for(const [field,types] of Object.entries({terrain:['ocean','grassland','plains','desert','swamp'],vegetation:['broadleaf','scrub','jungle','wetland','alpine'],relief:['hill','mountain']})){
  for(const type of types)assert.ok(world.cells.filter(c=>c[field]===type).length>=1,`${type} needs a visible area`);
 }
 for(const terrain of TERRAIN_FAMILIES)for(const variant of ['flat','forest','hills','forest+hills'])assert.ok(world.cells.some(c=>c.terrain===terrain&&terrainVariant(c)===variant),`${terrain}: ${variant}`);
 for(const c of world.cells)if(c.vegetation)assert.equal(c.vegetation,forestKind(c.terrain,c.relief));
 assert.ok(world.rivers.length>0);
});
