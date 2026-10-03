import test from 'node:test';import assert from 'node:assert/strict';
import {makeRelief,reliefPosition,alpineDensity} from '../relief.js';import {displacement} from '../geometry.js';
const world={width:16,height:16,cells:Array.from({length:256},(_,i)=>({x:i%16,y:Math.floor(i/16),land:true,relief:Math.floor(i/16)===8&&i%16>=4&&i%16<=10?(i%16>7?'mountain':'hill'):null}))};
test('ridge connections are continuous through saddles and vanish away from relief',()=>{
 const a=makeRelief(world,42),b=makeRelief(world,42);assert.deepEqual(a.rocks,b.rocks);
 for(const s of a.segments)for(let t=0;t<=1;t+=.1)assert.ok(a.height(s.ax+(s.bx-s.ax)*t,s.ay+(s.by-s.ay)*t)>.3);
 assert.equal(a.height(100,100),0);
 for(let x=400;x<1500;x+=17)assert.ok(Math.abs(a.height(x,800)-a.height(x+.001,800))<.001);
});
test('ridge anchors invert the shared displacement and Alpine density thins at crests',()=>{
 for(let x=400;x<1500;x+=37){const [px,py]=reliefPosition(42,x,800),[dx,dy]=displacement(42,px,py);assert.ok(Math.hypot(px+dx-x,py+dy-800)<.2);assert.ok(alpineDensity(42,x,800,.7)<alpineDensity(42,x,800,.1));}
});
test('3x3 blocks retain raised interiors between ridges, with no internal pits',()=>{
 const block={...world,cells:world.cells.map(c=>({...c,relief:c.x>=6&&c.x<=8&&c.y>=6&&c.y<=8?'hill':null}))};
 const r=makeRelief(block,42);
 for(let y=6.5*96;y<=8.5*96;y+=8)for(let x=6.5*128;x<=8.5*128;x+=8)assert.ok(r.height(x,y)>.34,`pit at ${x},${y}`);
 assert.equal(r.height(100,100),0);
 assert.ok(r.breadth(7.5*128,7.5*96)>.9);
 const interior=r.rocks.filter(p=>p.x>7*128&&p.x<8*128&&p.y>7*96&&p.y<8*96);
 assert.ok(interior.length>=3);
});
test('3x3 mountains have rocky saddles across all twelve shared edges',()=>{
 const block={...world,cells:world.cells.map(c=>({...c,relief:c.x>=6&&c.x<=8&&c.y>=6&&c.y<=8?'mountain':null}))};
 const r=makeRelief(block,42);
 assert.equal(r.rocks.filter(p=>p.saddle).length,12);
 assert.equal(r.rocks.filter(p=>p.peak).length,9);
 assert.ok(r.rocks.filter(p=>p.rocky&&!p.saddle).length>0);
 assert.ok(r.rocks.every(p=>p.peak||p.rocky));
});
test('mountain crown can cross north boundary only into mountain terrain',async()=>{
 const {mountainFitsNorth}=await import('../relief.js');
 const block={...world,cells:world.cells.map(c=>({...c,relief:null}))};
 const footprint={points:[[10,0,1],[10,20,1]]};
 assert.equal(mountainFitsNorth(block,42,footprint,950,630,1,7),false);
 for(let x=6;x<=8;x++)block.cells[6*16+x].relief='mountain';
 assert.equal(mountainFitsNorth(block,42,footprint,950,630,1,7),true);
 block.cells[6*16+7].relief='hill';
 assert.equal(mountainFitsNorth(block,42,footprint,950,630,1,7),false);
});
