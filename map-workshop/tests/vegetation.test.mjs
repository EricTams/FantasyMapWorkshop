import test from 'node:test';
import assert from 'node:assert/strict';
import {spriteFootprint,canopyClearsRiver} from '../vegetation.js';
function tree(){const rgba=new Uint8ClampedArray(20*50*4);for(let y=2;y<27;y++)for(let x=3;x<17;x++)rgba[(y*20+x)*4+3]=255;for(let y=27;y<50;y++)for(let x=9;x<11;x++)rgba[(y*20+x)*4+3]=255;return spriteFootprint(rgba,20,50);}
test('visual mass is above the root; foreground crown cannot cover horizontal river',()=>{
 const f=tree();assert.ok(f.center[1]<25);
 // Root at y=130 clears the old 15px rule, but the crown occupies y=82..107.
 const horizontal=(x,y)=>Math.abs(y-100)-4;
 assert.equal(canopyClearsRiver(f,40,80,1,horizontal),false);
 // A tree north of the river can retain its natural anchor without a symmetric clearing.
 assert.equal(canopyClearsRiver(f,40,40,1,horizontal),true);
});
test('canopy respects vertical rivers and transparent sprite margins',()=>{
 const f=tree(),vertical=(x,y)=>Math.abs(x-50)-4;
 assert.equal(canopyClearsRiver(f,40,80,1,vertical),false);
 assert.equal(canopyClearsRiver(f,65,80,1,vertical),true);
 const blank=spriteFootprint(new Uint8ClampedArray(20*50*4),20,50);
 assert.equal(canopyClearsRiver(blank,40,80,1,vertical),true);
});

import {resourceTreeDensity,canopyClearsObjects} from '../vegetation.js';
import {noise} from '../generator.js';
test('resource thinning is deterministic, gradual, crosses tile borders and recovers',()=>{
 const resources=[{x:64,y:48}],keep=(x,y)=>resourceTreeDensity(123,x,y,resources,noise);
 assert.equal(keep(64,48),.22);assert.equal(keep(400,48),1);
 assert.ok(keep(128,48)<1);assert.ok(Math.abs(keep(127.99,48)-keep(128.01,48))<.001);
 for(let x=0;x<250;x+=3){assert.equal(keep(x,48),keep(x,48));assert.ok(keep(x,48)>=.22&&keep(x,48)<=1);}
 assert.equal(resourceTreeDensity(123,64,48,[...resources,...resources],noise),.22);
 assert.equal(resourceTreeDensity(123,64,48,[],noise),1);
});
test('canopy footprints protect a resource even when its roots are outside the clearing',()=>{
 const overlaps=(l,t,r,b)=>l<55&&r>45&&t<100&&b>90;
 assert.equal(canopyClearsObjects(tree(),40,80,1,overlaps),false);
 assert.equal(canopyClearsObjects(tree(),75,80,1,overlaps),true);
});
