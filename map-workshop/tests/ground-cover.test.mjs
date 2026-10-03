import test from 'node:test';
import assert from 'node:assert/strict';
import {groundCoverDensity,isForested} from '../ground-cover.js';
const world={width:16,height:16,cells:Array.from({length:256},(_,i)=>({vegetation:i%16<8?'broadleaf':null}))};
test('ground cover belongs exclusively to forested tiles, including boundaries',()=>{
 for(let y=30;y<1500;y+=41){
  assert.ok(groundCoverDensity(world,42,1024-.001,y)>0);
  assert.equal(groundCoverDensity(world,42,1024,y),0);
  assert.equal(groundCoverDensity(world,42,1600,y),0);
 }
 for(const [x,y] of [[-1,50],[2048,50],[50,-1],[50,1536]])assert.equal(isForested(world,x,y),false);
});
test('forest ground coverage remains deterministic and sparse',()=>{
 for(let x=10;x<1024;x+=17){
  const d=groundCoverDensity(world,42,x,800);
  assert.ok(d>0&&d<=.28);
  assert.equal(d,groundCoverDensity(world,42,x,800));
 }
});
