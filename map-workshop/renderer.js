import {noise,randomAt} from './generator.js';
import {resourceMembers} from './resources.js';
import {displacement,ownership,makeGeometry} from './geometry.js';
import {spriteFootprint,canopyClearsRiver,resourceTreeDensity,canopyClearsObjects} from './vegetation.js';
const BASE=new URL('./assets/',import.meta.url);
const names=['materials/deep_water.png','materials/shallow_water.png','materials/meadow.png','materials/shore.png',...Array.from({length:4},(_,i)=>`sprites/broadleaf_edge_${i}.png`),...Array.from({length:4},(_,i)=>`pine/sprites/pine_edge_${i}.png`),...Array.from({length:4},(_,i)=>`jungle/jungle_edge_${i}.png`),...['hill','mountain'].flatMap(kind=>[0,1].map(i=>`relief/${kind}_rock_${i}.png`)),...['mithril','gems','voidstone'].map(s=>`minerals/${s}.png`),'fantasy/white_stag_0.png','fantasy/white_stag_1.png','pepper/scarlet_pepper_0.png','pepper/scarlet_pepper_1.png','resources/wheat_field.png','wildlife/aurochs_0.png','wildlife/aurochs_1.png','resources/fish_school.png'];
export const images={};
const texture={};
const footprints={};
export async function loadAssets(){await Promise.all(names.map(async name=>{const img=new Image();img.src=new URL(name,BASE).href;await img.decode();images[name]=img;if(!name.startsWith('materials/')){const c=document.createElement('canvas');c.width=img.width;c.height=img.height;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(img,0,0);footprints[name]=spriteFootprint(ctx.getImageData(0,0,img.width,img.height).data,img.width,img.height);}}));for(const name of ['deep_water','shallow_water','meadow','shore'])texture[name]=prepareTexture(images[`materials/${name}.png`]);}
function prepareTexture(image){
 const c=document.createElement('canvas');c.width=c.height=256;const cx=c.getContext('2d',{willReadFrequently:true});cx.drawImage(image,0,0,256,256);const src=cx.getImageData(0,0,256,256).data,out=new Uint8ClampedArray(224*224*3);
 // Fold the final 32 pixels over the start in both axes; globally phased 224px repeat.
 for(let y=0;y<224;y++)for(let x=0;x<224;x++){
  const fx=x<32?(x+.5)/32:1,fy=y<32?(y+.5)/32:1;
  for(let k=0;k<3;k++){const a=src[(y*256+x)*4+k],b=src[(y*256+(x<32?x+224:x))*4+k],d=src[((y<32?y+224:y)*256+x)*4+k],e=src[((y<32?y+224:y)*256+(x<32?x+224:x))*4+k];out[(y*224+x)*3+k]=(a*fx+b*(1-fx))*fy+(d*fx+e*(1-fx))*(1-fy);}
 }out.mean=[0,0,0];for(let i=0;i<out.length;i++)out.mean[i%3]+=out[i]/(224*224);return out;
}
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const colors={desert:[204,184,141],plains:[181,168,103],grassland:[143,156,78],ocean:[143,156,78]};
function biomeMaterial(world,x,y,band){
 const color=[0,0,0];let desert=0;
 for(const part of ownership(x,y,band)){
  const cell=world.cells[clamp(part.row,0,15)*16+clamp(part.col,0,15)];
  const c=colors[cell.terrain];for(let k=0;k<3;k++)color[k]+=c[k]*part.weight;
  if(cell.terrain==='desert')desert+=part.weight;
 }
 return {color,desert};
}
// Sample world fields on a four-pixel lattice, then interpolate, never per tile.
function prepareFields(world,seed){
 const step=4,w=513,h=385,channels=8,a=new Float32Array(w*h*channels),geometry=makeGeometry(world);
 for(let iy=0;iy<h;iy++)for(let ix=0;ix<w;ix++){
  const x=ix*step,y=iy*step,[dx,dy]=displacement(seed,x,y),qx=x+dx,qy=y+dy;
  const r=geometry.riverDistance(qx,qy),o=(iy*w+ix)*channels;
  a[o]=dx;a[o+1]=dy;
  // Coast uses the same inverse-mapped point as biomes, materials and rivers.
  // The six-pixel corner filter softens the logical silhouette before displacement.
  const cx=qx,cy=qy;
  a[o+2]=(geometry.coastDistance(cx-6,cy-6)+geometry.coastDistance(cx+6,cy-6)+geometry.coastDistance(cx-6,cy+6)+geometry.coastDistance(cx+6,cy+6))/4;
  a[o+3]=r.distance;
  a[o+4]=(3.3+noise(seed,qx/48,qy/36,111)*2.1)*clamp(r.progress/42,.12,1);
  a[o+5]=noise(seed,qx/19,qy/14,112);
  a[o+6]=4+noise(seed,qx/35,qy/26,113)*2;
  a[o+7]=r.progress;
 }
 const out=new Float32Array(channels);
 return {geometry,sample(x,y){
  const xx=clamp(x/step,0,w-1.001),yy=clamp(y/step,0,h-1.001),ix=Math.floor(xx),iy=Math.floor(yy),fx=xx-ix,fy=yy-iy,o=(iy*w+ix)*channels;
  for(let k=0;k<channels;k++)out[k]=(a[o+k]*(1-fx)+a[o+channels+k]*fx)*(1-fy)+(a[o+w*channels+k]*(1-fx)+a[o+(w+1)*channels+k]*fx)*fy;
  return out;
 }};
}
const resourcePath={mithril:'minerals/mithril.png',gems:'minerals/gems.png',voidstone:'minerals/voidstone.png',wheat:'resources/wheat_field.png',fish:'resources/fish_school.png'};
export function renderWorld(world,seed){
 const canvas=document.createElement('canvas');canvas.width=2048;canvas.height=1536;const ctx=canvas.getContext('2d');const data=ctx.createImageData(2048,1536);const p=data.data;
 const water=texture.deep_water,shallow=texture.shallow_water,ground=texture.meadow,sand=texture.shore;
 const fields=prepareFields(world,seed);
 for(let y=0;y<1536;y++){
  for(let x=0;x<2048;x++){
   const f=fields.sample(x,y),qx=x+f[0],qy=y+f[1],coast=f[2];
   const land=clamp((coast+1.1)/2.2),shelf=clamp((coast+25)/25),beach=clamp((7-coast)/7)*land;
   const bx=clamp(qx,0,2047.999),by=clamp(qy,0,1535.999);
   // Ownership, material detail, and channel distance all use the same displaced point.
   const tx=((Math.floor(qx*.8)%224)+224)%224,ty=((Math.floor(qy*1.067)%224)+224)%224,ti=(ty*224+tx)*3;
   const wi=((y%224)*224+x%224)*3,o=(y*2048+x)*4;
   const {color,desert}=biomeMaterial(world,bx,by,f[6]);
   const channel=clamp((f[4]-f[3]+1.4)/2.8);
   const bank=clamp((f[4]+2.5+f[5]*2-f[3])/3.5);
   const riverLand=clamp((coast+6)/10);
   for(let k=0;k<3;k++){
    let g=color[k]+(ground[ti+k]-ground.mean[k])*.45*(1-desert)+(sand[ti+k]-sand.mean[k])*.42*desert;
    g=g*(1-beach)+([198,186,137][k]+(sand[ti+k]-sand.mean[k])*.4)*beach;
    const deep=[19,74,114][k]+(water[wi+k]-water.mean[k])*.40;
    const light=[42,107,131][k]+(shallow[wi+k]-shallow.mean[k])*.45;
    const sea=deep*(1-shelf*.78)+light*shelf*.78;
    let base=sea*(1-land)+g*land;
    const bankColor=[102,114,74][k]+(ground[ti+k]-ground.mean[k])*.25;
    base=base*(1-bank*.55*riverLand)+bankColor*bank*.55*riverLand;
    // Sampled water detail and irregular banks replace three uniform stroked lines.
    const riverColor=[54,111,125][k]+(shallow[ti+k]-shallow.mean[k])*.55+(f[5]-.5)*9;
    p[o+k]=base*(1-channel*riverLand)+riverColor*channel*riverLand;
   }p[o+3]=255;
  }
 }ctx.putImageData(data,0,0);
 const objects=[],resources=[];
 const add=(path,x,y,width,anchor=.87,protectedFraction=1)=>{const img=images[path];if(!img)return;const h=img.height*width/img.width;objects.push({img,x:x-width/2,y:y-h*anchor,w:width,h,depth:y,protectedFraction});};
 for(const c of world.cells){const x=(c.x+.5)*128,y=(c.y+.57)*96;
  if(c.relief==='mountain')add(`relief/mountain_rock_${Math.floor(randomAt(seed,c.x,c.y,80)*2)}.png`,x+(c.resource?-18:0),y+(c.resource?-10:5),c.resource?86:110);
  const before=objects.length;
  const members=resourceMembers(c.resource,c.x,c.y);
  if(members.length){for(const m of members)add(m.path,m.x,m.y,m.width,m.anchor,m.protectedFraction);}
  else if(c.resource==='aurochs'){add('wildlife/aurochs_0.png',x-25,y,48);add('wildlife/aurochs_1.png',x+27,y+19,44);}
  else if(c.resource)add(resourcePath[c.resource],x,y+14,c.resource==='fish'?88:102,.78);
  if(c.resource&&c.land){resources.push({x,y,objects:objects.slice(before)});}
 }

 // Protect identifying parts only against trees drawn in front of each member.
 // Rear foliage can overlap freely; lower legs and bush bases allow small overlaps.
 const mask=document.createElement('canvas');mask.width=2048;mask.height=1536;
 const mc=mask.getContext('2d',{willReadFrequently:true});
 const resourceDepth=new Float32Array(2048*1536);resourceDepth.fill(Infinity);
 for(const r of resources)for(const o of r.objects){
  const sprite=document.createElement('canvas');sprite.width=Math.ceil(o.w);sprite.height=Math.ceil(o.h*o.protectedFraction);
  const sc=sprite.getContext('2d',{willReadFrequently:true});sc.drawImage(o.img,0,0,o.w,o.h);
  const pixels=sc.getImageData(0,0,sprite.width,sprite.height).data;
  for(let sy=0;sy<sprite.height;sy++)for(let sx=0;sx<sprite.width;sx++){
   const x=Math.floor(o.x)+sx,y=Math.floor(o.y)+sy;
   if(x<0||y<0||x>=2048||y>=1536||pixels[(sy*sprite.width+sx)*4+3]<=24)continue;
   const index=y*2048+x;resourceDepth[index]=Math.min(resourceDepth[index],o.depth);
  }
  mc.save();mc.beginPath();mc.rect(o.x,o.y,o.w,o.h*o.protectedFraction);mc.clip();mc.drawImage(o.img,o.x,o.y,o.w,o.h);mc.restore();
 }
 const alpha=mc.getImageData(0,0,2048,1536).data,stride=2049,integral=new Uint32Array(stride*1537);
 for(let y=0;y<1536;y++){let sum=0;for(let x=0;x<2048;x++){sum+=alpha[(y*2048+x)*4+3]>24?1:0;integral[(y+1)*stride+x+1]=sum+integral[y*stride+x+1];}}
 const occupied=(left,top,right,bottom,treeDepth)=>{
  const x0=clamp(Math.floor(left),0,2048),y0=clamp(Math.floor(top),0,1536),x1=clamp(Math.ceil(right),0,2048),y1=clamp(Math.ceil(bottom),0,1536);
  if(integral[y1*stride+x1]-integral[y0*stride+x1]-integral[y1*stride+x0]+integral[y0*stride+x0]===0)return false;
  for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++)if(resourceDepth[y*2048+x]<=treeDepth)return true;
  return false;
 };
 // Relief and resource footprints stay distinct from vegetation and base biome.
 for(const c of world.cells){if(c.relief==='hill'){
  for(let j=0;j<3;j++){const x=c.x*128+30+j*34,y=c.y*96+44+(j%2)*25;const img=images[`relief/hill_rock_${j%2}.png`];ctx.drawImage(img,x-39,y-26,78,78*img.height/img.width);}
 }}

 // A global planting lattice connects forest neighbors without tiled canopy stamps.
 for(let y=12;y<1530;y+=14)for(let x=10;x<2040;x+=17){
  const px=x+(randomAt(seed,x,y,70)-.5)*13,py=y+(randomAt(seed,x,y,71)-.5)*11;
  const f=fields.sample(px,py);
  const col=Math.floor((px+f[0])/128),row=Math.floor((py+f[1])/96),c=world.cells[row*16+col];if(!c?.vegetation)continue;
  if(f[2]<8)continue;
  if(randomAt(seed,x,y,122)>resourceTreeDensity(seed,px,py,resources,noise))continue;
  const i=Math.floor(randomAt(seed,x,y,72)*4),kind=c.vegetation;
  const path=kind==='pine'?`pine/sprites/pine_edge_${i}.png`:kind==='jungle'?`jungle/jungle_edge_${i}.png`:`sprites/broadleaf_edge_${i}.png`;
  const width=(kind==='pine'?29:39)*(0.85+randomAt(seed,x,y,73)*.28);
  const scale=width/images[path].width,height=images[path].height*scale;
  if(!canopyClearsObjects(footprints[path],px-width/2,py-height*.93,scale,(l,t,r,b)=>occupied(l,t,r,b,py)))continue;
  // Test the alpha-weighted visual center and occupied canopy, not just the root.
  // In particular, a foreground tree's crown reaches north across a horizontal river.
  if(!canopyClearsRiver(footprints[path],px-width/2,py-height*.93,scale,(sx,sy)=>{
   const sample=fields.sample(sx,sy);return sample[3]-sample[4];
  }))continue;
  add(path,px,py,width,.93);
 }
 objects.sort((a,b)=>a.depth-b.depth);for(const o of objects)ctx.drawImage(o.img,o.x,o.y,o.w,o.h);
 return canvas;
}
