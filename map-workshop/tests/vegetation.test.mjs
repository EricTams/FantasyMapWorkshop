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
