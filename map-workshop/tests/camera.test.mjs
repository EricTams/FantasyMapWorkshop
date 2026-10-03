import test from 'node:test';
import assert from 'node:assert/strict';
import {constrainView,nearestWrappedX,tourStops,wrap} from '../camera.js';
import {generateWorld,neighbors} from '../generator.js';
import {makeGeometry} from '../geometry.js';
test('camera wraps horizontally and clamps or centers vertically at every scale',()=>{
 for(const scale of [.1,.4,1,1.5])for(const x of [-1e6,-3584,0,3584,1e6])for(const y of [-1e6,0,1e6]){
  const v=constrainView({x,y,scale},3584,2688,900,650),span=3584*scale,h=2688*scale;
  if(span<=900)assert.equal(v.x,(900-span)/2);else {assert.ok(v.x>=-span&&v.x<0);assert.ok(Math.abs(wrap(v.x-x,span))<1e-6||Math.abs(wrap(v.x-x,span)-span)<1e-6);}
  if(h<=650)assert.equal(v.y,(650-h)/2);else assert.ok(v.y>=650-h&&v.y<=0);
 }
 assert.equal(nearestWrappedX(-3500,-100,3584),-3684);
});
test('large world has connected land and valid geometry beyond former 16-tile boundary',()=>{
 const w=generateWorld('wildwood-1701',{style:"island",size:28,land:72,ruggedness:62,moisture:43,forest:60,resources:35});
 assert.equal(w.cells.length,784);
 const land=w.cells.map((c,i)=>c.land?i:-1).filter(i=>i>=0),seen=new Set([land[0]]),queue=[land[0]];
 for(const i of queue)for(const j of neighbors(i,w.width))if(w.cells[j].land&&!seen.has(j)){seen.add(j);queue.push(j);}assert.equal(seen.size,land.length);
 const c=w.cells.find(c=>c.land&&c.x>20&&c.y>16),g=makeGeometry(w);assert.ok(c);assert.ok(g.coastDistance((c.x+.5)*128,(c.y+.5)*96)>0);
 for(const r of w.rivers)for(const [x,y] of r.nodes)assert.ok(x>=0&&x<=28&&y>=0&&y<=28);
 const stops=tourStops(w);assert.equal(stops.length,14);assert.equal(new Set(stops.map(s=>s.label)).size,14);
 for(const s of stops)assert.ok(s.x>0&&s.x<3584&&s.y>0&&s.y<2688);
 const empty={width:28,height:28,cells:[]};assert.deepEqual(tourStops(empty),[]);
});
