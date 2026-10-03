import test from 'node:test';
import assert from 'node:assert/strict';
import {displacement,ownership,makeGeometry} from '../geometry.js';
import {generateWorld,hashSeed} from '../generator.js';
test('shared displacement is deterministic, continuous and confined to tile edges',()=>{
 const seed=hashSeed('elderwood');
 for(let y=0;y<1536;y+=23)for(let x=0;x<2048;x+=29){
  const d=displacement(seed,x,y),next=displacement(seed,x+.1,y+.1);
  assert.deepEqual(d,displacement(seed,x,y));assert.ok(Math.abs(d[0])<=14&&Math.abs(d[1])<=10.5);
  assert.ok(Math.hypot(next[0]-d[0],next[1]-d[1])<.2);
 }
 for(let y=0;y<16;y++)for(let x=0;x<16;x++){
  const px=(x+.5)*128,py=(y+.5)*96,d=displacement(seed,px,py);
  assert.deepEqual(ownership(px+d[0],py+d[1],6),[{col:x,row:y,weight:1}]);
 }
});
test('biome weights sum to one, including junctions, and share boundaries continuously',()=>{
 for(let y=88;y<104;y+=.5)for(let x=120;x<136;x+=.5){const weights=ownership(x,y,5);assert.ok(Math.abs(weights.reduce((s,v)=>s+v.weight,0)-1)<1e-12);assert.ok(weights.every(v=>v.weight>=0));}
 const left=ownership(128-1e-6,60),right=ownership(128+1e-6,60);const weight=(a,c)=>a.filter(v=>v.col===c).reduce((s,v)=>s+v.weight,0);
 assert.ok(Math.abs(weight(left,0)-weight(right,0))<1e-6);
});
test('coast follows the rectangular tile footprint; river joins share one distance field',()=>{
 const w=generateWorld('geometry');for(const c of w.cells)c.land=c.x===4&&c.y===4;
 w.rivers=[{nodes:[[4,3],[4,4],[5,4]]},{nodes:[[4,5],[4,4]]}];const g=makeGeometry(w);
 assert.equal(g.coastDistance(4*128+64,4*96+48),48);
 assert.equal(g.coastDistance(4*128-8,4*96+48),-8);
 assert.equal(g.coastDistance(4*128+8,4*96+48),8);
 for(const [x,y] of [[512,384],[512,350],[550,384],[512,440]])assert.equal(g.riverDistance(x,y).distance,0);
});
