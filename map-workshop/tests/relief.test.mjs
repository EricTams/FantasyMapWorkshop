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
