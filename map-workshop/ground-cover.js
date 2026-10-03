import {noise,randomAt} from './generator.js';
// Coordinates here are already mapped through the shared displacement field.
export function isForested(world,x,y){
 const col=Math.floor(x/128),row=Math.floor(y/96);
 return col>=0&&row>=0&&col<world.width&&row<world.height&&!!world.cells[row*world.width+col]?.vegetation;
}
export function groundCoverDensity(world,seed,x,y){
 if(!isForested(world,x,y))return 0;
 const clusters=Math.max(0,Math.min(1,(noise(seed,x/64,y/48,130)-.25)*2));
 return .28*(.25+.75*clusters);
}

export function drawGroundCover(ctx,world,seed,fields,atlas){
 const layer=document.createElement('canvas');layer.width=ctx.canvas.width;layer.height=ctx.canvas.height;
 const lc=layer.getContext('2d',{willReadFrequently:true}),sw=atlas.width/2,sh=atlas.height/2;
 for(let y=12;y<layer.height;y+=17)for(let x=12;x<layer.width;x+=22){
  const px=x+(randomAt(seed,x,y,131)-.5)*19,py=y+(randomAt(seed,x,y,132)-.5)*15;
  const f=fields.sample(px,py),qx=px+f[0],qy=py+f[1];
  if(f[2]<8||f[3]<f[4]+4)continue;
  if(randomAt(seed,x,y,133)>groundCoverDensity(world,seed,qx,qy))continue;
  const variant=Math.floor(randomAt(seed,x,y,134)*4),w=23+randomAt(seed,x,y,135)*9,h=w*.65;
  lc.globalAlpha=.9;
  lc.drawImage(atlas,(variant%2)*sw,Math.floor(variant/2)*sh,sw,sh,px-w/2,py-h/2,w,h);
 }
 // Clip the whole patch, not only its center, against the shared displaced fields.
 const pixels=lc.getImageData(0,0,layer.width,layer.height),a=pixels.data;
 for(let y=0;y<layer.height;y++)for(let x=0;x<layer.width;x++){
  const i=(y*layer.width+x)*4+3;if(!a[i])continue;
  const f=fields.sample(x,y);
  if(!isForested(world,x+f[0],y+f[1])){a[i]=0;continue;}
  const edge=Math.max(0,Math.min(1,(f[2]-7)/5,(f[3]-f[4]-3)/4));
  a[i]*=edge;
 }
 lc.putImageData(pixels,0,0);ctx.drawImage(layer,0,0);
}
