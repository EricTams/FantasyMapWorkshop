import test from 'node:test';
import assert from 'node:assert/strict';
import {TERRAIN_FAMILIES,forestKind,terrainVariant} from '../terrain.js';
test('every forested hill is Alpine regardless of terrain; mountains stay rocky',()=>{
 for(const terrain of TERRAIN_FAMILIES){
  assert.equal(forestKind(terrain,'hill'),'alpine');
  assert.equal(forestKind(terrain,'mountain'),null);
  for(const relief of [null,'hill'])for(const wooded of [false,true]){
   const c={terrain,relief,vegetation:wooded?forestKind(terrain,relief):null};
   assert.equal(terrainVariant(c),relief?(wooded?'forest+hills':'hills'):(wooded?'forest':'flat'));
  }
 }
 assert.deepEqual(TERRAIN_FAMILIES.map(t=>forestKind(t,null)),['broadleaf','scrub','jungle','wetland']);
});
