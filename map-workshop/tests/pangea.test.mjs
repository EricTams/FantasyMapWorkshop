import test from 'node:test';import assert from 'node:assert/strict';
import {generateWorld,hashSeed} from '../generator.js';import {worldNeighbors} from '../landforms.js';import {makeGeometry,displacement} from '../geometry.js';
function components(w){const unseen=new Set(w.cells.flatMap((c,i)=>c.land?[i]:[])),sizes=[];while(unseen.size){const q=[unseen.values().next().value];unseen.delete(q[0]);for(const i of q)for(const j of worldNeighbors(i,w.width))if(unseen.delete(j))q.push(j);sizes.push(q.length);}return sizes.sort((a,b)=>b-a);}
test('Pangea sweep preserves single continent, target coverage, polar oceans and deterministic settings',()=>{
 let crossings=0;
 for(const size of [16,28])for(const complexity of [0,60,100])for(let seed=0;seed<12;seed++){
  const w=generateWorld('shape-'+seed,{size,complexity,land:[30,58,72,78][seed%4]});
  assert.equal(w.settings.style,'pangea');assert.equal(w.wrapX,true);
  const sizes=components(w),land=sizes.reduce((a,b)=>a+b,0);assert.equal(land,Math.round(size*size*w.settings.land/100));assert.equal(sizes.length,1);
  for(const c of w.cells)if(c.y===0||c.y===size-1)assert.equal(c.land,false);
  if(w.cells.some(c=>c.x===0&&c.land&&w.cells[c.y*size+size-1].land))crossings++;
  for(const r of w.rivers)for(let i=1;i<r.nodes.length;i++){const a=r.nodes[i-1],b=r.nodes[i],dx=Math.abs(a[0]-b[0]);assert.equal(Math.min(dx,size-dx)+Math.abs(a[1]-b[1]),1);}
 }
 assert.ok(crossings>0);assert.deepEqual(generateWorld('repeat',{size:28}),generateWorld('repeat',{size:28}));
 assert.notDeepEqual(generateWorld('shape',{complexity:0}).cells.map(c=>c.land),generateWorld('shape',{complexity:100}).cells.map(c=>c.land));
});
test('wrapped coast and river geometry has no artificial edge at the seam',()=>{
 const w=generateWorld('seam',{size:28});for(const c of w.cells)c.land=c.y>=8&&c.y<=12;w.rivers=[{nodes:[[27,10],[0,10],[1,10]]}];const g=makeGeometry(w),W=28*128;
 assert.ok(g.coastDistance(0,10*96)>0);assert.equal(g.coastDistance(0,10*96),g.coastDistance(W,10*96));
 assert.equal(g.riverDistance(W-64,960).distance,0);assert.equal(g.riverDistance(64,960).distance,0);
 assert.deepEqual(displacement(hashSeed('seam'),0,500,W),displacement(hashSeed('seam'),W,500,W));
});
