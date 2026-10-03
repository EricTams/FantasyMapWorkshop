import test from 'node:test';
import assert from 'node:assert/strict';
import {groundCoverDensity} from '../ground-cover.js';
const world={width:16,height:16,cells:Array.from({length:256},(_,i)=>({vegetation:i%16<8?'broadleaf':null}))};
test('ground cover blends across woodland boundaries and stays sparse',()=>{
 for(let y=30;y<1500;y+=41){
  const left=groundCoverDensity(world,42,1024-.001,y,[]);
  const right=groundCoverDensity(world,42,1024+.001,y,[]);
  assert.ok(Math.abs(left-right)<.001);
  assert.ok(left>=0&&left<=.34);
 }
 assert.equal(groundCoverDensity(world,42,1600,800,[]),0);
});
test('resource influence is deterministic, local, and does not stack',()=>{
 const resource={x:1600,y:800};
 const one=groundCoverDensity(world,42,1600,800,[resource]);
 assert.ok(one>0&&one<=.45);
 assert.equal(one,groundCoverDensity(world,42,1600,800,[resource,resource]));
 assert.equal(groundCoverDensity(world,42,1900,800,[resource]),0);
});
