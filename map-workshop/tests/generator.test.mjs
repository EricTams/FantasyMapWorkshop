import test from 'node:test';
import assert from 'node:assert/strict';
import {generateWorld,neighbors} from '../generator.js';
test('same seed and settings reproduce the entire world',()=>{assert.deepEqual(generateWorld('elderwood'),generateWorld('elderwood'));assert.notDeepEqual(generateWorld('elderwood'),generateWorld('other'));});
test('seed sweep: connected land, ocean border, valid resources and shared-edge river drainage',()=>{
 for(let seed=0;seed<80;seed++){
  const w=generateWorld(String(seed),{style:"island",land:30+seed%49,moisture:seed%101,ruggedness:seed%101,forest:seed%101,resources:seed%101});
  const land=w.cells.map((c,i)=>c.land?i:-1).filter(i=>i>=0),visited=new Set([land[0]]),queue=[land[0]];
  for(const i of queue)for(const j of neighbors(i))if(w.cells[j].land&&!visited.has(j)){visited.add(j);queue.push(j);}
  assert.equal(visited.size,land.length);assert.equal(land.length,Math.min(196,Math.round(256*w.settings.land/100)));
  for(const c of w.cells){if(c.x===0||c.y===0||c.x===15||c.y===15)assert.equal(c.land,false);if(!c.land){assert.equal(c.vegetation,null);assert.equal(c.relief,null);assert.ok(c.resource===null||c.resource==='fish');}if(c.relief==='mountain')assert.equal(c.vegetation,null);}
  const graph=new Map();for(const r of w.rivers){assert.ok(r.nodes.length>=4);for(let i=1;i<r.nodes.length;i++){const a=r.nodes[i-1],b=r.nodes[i];assert.equal(Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1]),1);assert.ok(b.every(v=>v>=0&&v<=16));const key=a.join(',');if(graph.has(key))assert.equal(graph.get(key),b.join(','));graph.set(key,b.join(','));}}
  for(const source of graph.keys()){const seen=new Set();let at=source;while(graph.has(at)){assert.ok(!seen.has(at));seen.add(at);at=graph.get(at);}}
 }
});
test('zero settings remove forests, relief and resources; controls influence output',()=>{
 const low=generateWorld('sliders',{forest:0,ruggedness:0,resources:0,moisture:0,land:30}),high=generateWorld('sliders',{forest:100,ruggedness:100,resources:100,moisture:100,land:78});
 assert.equal(low.cells.filter(c=>c.vegetation||c.relief||c.resource).length,0);
 for(const key of ['land','vegetation','relief','resource'])assert.ok(high.cells.filter(c=>c[key]).length>low.cells.filter(c=>c[key]).length);
 assert.ok(high.cells.filter(c=>c.terrain==='grassland').length>low.cells.filter(c=>c.terrain==='grassland').length);
});
