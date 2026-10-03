import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {generateWorld} from '../generator.js';

test('opening map represents every supported terrain, forest and relief type',()=>{
 const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
 const value=id=>html.match(new RegExp(`id="${id}"[^>]*value="([^"]+)"`))[1];
 const settings=Object.fromEntries(['land','ruggedness','moisture','forest','resources'].map(k=>[k,+value(k)]));
 const world=generateWorld(value('seed'),settings);
 for(const [field,types] of Object.entries({terrain:['ocean','grassland','plains','desert'],vegetation:['broadleaf','pine','jungle'],relief:['hill','mountain']})){
  for(const type of types)assert.ok(world.cells.filter(c=>c[field]===type).length>=10,`${type} needs a visible area`);
 }
 assert.ok(world.rivers.length>0);
});
