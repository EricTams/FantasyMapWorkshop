import {noise,randomAt} from './generator.js';
const BASE=new URL('./assets/',import.meta.url);
const names=['materials/deep_water.png','materials/shallow_water.png','materials/meadow.png','materials/shore.png',...Array.from({length:4},(_,i)=>`sprites/broadleaf_edge_${i}.png`),...Array.from({length:4},(_,i)=>`pine/sprites/pine_edge_${i}.png`),...Array.from({length:4},(_,i)=>`jungle/jungle_edge_${i}.png`),...['hill','mountain'].flatMap(kind=>[0,1].map(i=>`relief/${kind}_rock_${i}.png`)),...['mithril','gems','voidstone'].map(s=>`minerals/${s}.png`),'fantasy/white_stags_tile.png','pepper/scarlet_pepper_bushes.png','resources/wheat_field.png','wildlife/aurochs_0.png','wildlife/aurochs_1.png','resources/fish_school.png'];
export const images={};
const texture={};
export async function loadAssets(){await Promise.all(names.map(async name=>{const img=new Image();img.src=new URL(name,BASE).href;await img.decode();images[name]=img;}));for(const name of ['deep_water','shallow_water','meadow','shore'])texture[name]=prepareTexture(images[`materials/${name}.png`]);}
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
function biomeColor(world,x,y){
 const ix=Math.floor(x),iy=Math.floor(y),fx=x-ix,fy=y-iy;
 const nx=fx<.06?ix-1:fx>.94?ix+1:ix,ny=fy<.06?iy-1:fy>.94?iy+1:iy;
 const wx=fx<.06?(.06-fx)/.12:fx>.94?(fx-.94)/.12:0,wy=fy<.06?(.06-fy)/.12:fy>.94?(fy-.94)/.12:0;
 const at=(a,b)=>colors[world.cells[clamp(b,0,15)*16+clamp(a,0,15)].terrain];
 const a=at(ix,iy),b=at(nx,iy),c=at(ix,ny),d=at(nx,ny);
 return a.map((v,k)=>(v*(1-wx)+b[k]*wx)*(1-wy)+(c[k]*(1-wx)+d[k]*wx)*wy);
}
function field(world,x,y,fn){const ix=Math.floor(x),iy=Math.floor(y),fx=x-ix,fy=y-iy;const at=(a,b)=>a<0||b<0||a>=16||b>=16?0:fn(world.cells[b*16+a]);return (at(ix,iy)*(1-fx)+at(ix+1,iy)*fx)*(1-fy)+(at(ix,iy+1)*(1-fx)+at(ix+1,iy+1)*fx)*fy;}
const resourcePath={mithril:'minerals/mithril.png',gems:'minerals/gems.png',voidstone:'minerals/voidstone.png',white_stags:'fantasy/white_stags_tile.png',scarlet_pepper:'pepper/scarlet_pepper_bushes.png',wheat:'resources/wheat_field.png',fish:'resources/fish_school.png'};
export function renderWorld(world,seed){
 const canvas=document.createElement('canvas');canvas.width=2048;canvas.height=1536;const ctx=canvas.getContext('2d');const data=ctx.createImageData(2048,1536);const p=data.data;
 const water=texture.deep_water,shallow=texture.shallow_water,ground=texture.meadow,sand=texture.shore;
 // A small continuous mask is enlarged through interpolation for organic coasts.
 const coast=new Float32Array(129*129);
 for(let y=0;y<=128;y++)for(let x=0;x<=128;x++)coast[y*129+x]=field(world,x/8-.5,y/8-.5,c=>c.land?1:0)+(noise(seed,x/5,y/5,60)-.5)*.15;
 for(let y=0;y<1536;y++){
  const gy=y/96,yy=y/12,iy=Math.floor(yy),fy=yy-iy;
  for(let x=0;x<2048;x++){
   const gx=x/128,xx=x/16,ix=Math.floor(xx),fx=xx-ix;
   const v=(coast[iy*129+ix]*(1-fx)+coast[iy*129+ix+1]*fx)*(1-fy)+(coast[(iy+1)*129+ix]*(1-fx)+coast[(iy+1)*129+ix+1]*fx)*fy;
   const land=clamp((v-.47)*28),shelf=clamp((v-.12)*3.2),beach=clamp((.60-v)*9)*land;
   // Narrow irregular ownership bands leave each tile's center pure.
   const warp=3*Math.sin(x*.05+y*.018)+2*Math.sin(y*.07+x*.024);
   const bx=clamp((x+warp)/128,0,15.999),by=clamp((y+warp*.75)/96,0,15.999);
   const c=world.cells[Math.floor(by)*16+Math.floor(bx)];
   const tx=Math.floor(x*.8)%224,ty=Math.floor(y*1.067)%224,ti=(ty*224+tx)*3;
   const wi=((y%224)*224+x%224)*3;const o=(y*2048+x)*4;
   const color=biomeColor(world,bx,by);
   for(let k=0;k<3;k++){
    let g=color[k]+(ground[ti+k]-ground.mean[k])*.45;
    if(c.terrain==='desert')g=color[k]+(sand[ti+k]-sand.mean[k])*.42;
    g=g*(1-beach)+([198,186,137][k]+(sand[ti+k]-sand.mean[k])*.4)*beach;
    const deep=[19,74,114][k]+(water[wi+k]-water.mean[k])*.40;
    const light=[42,107,131][k]+(shallow[wi+k]-shallow.mean[k])*.45;
    const sea=deep*(1-shelf*.78)+light*shelf*.78;
    p[o+k]=sea*(1-land)+g*land;
   }p[o+3]=255;
  }
 }ctx.putImageData(data,0,0);
 const objects=[];
 const add=(path,x,y,width,anchor=.87)=>{const img=images[path];if(!img)return;const h=img.height*width/img.width;objects.push({img,x:x-width/2,y:y-h*anchor,w:width,h,depth:y});};
 // Relief and resource footprints stay distinct from vegetation and base biome.
 for(const c of world.cells){if(c.relief==='hill'){
  for(let j=0;j<3;j++){const x=c.x*128+30+j*34,y=c.y*96+44+(j%2)*25;const img=images[`relief/hill_rock_${j%2}.png`];ctx.drawImage(img,x-39,y-26,78,78*img.height/img.width);}
 }}
 drawRivers(ctx,world,seed);
 // A global planting lattice connects forest neighbors without tiled canopy stamps.
 for(let y=12;y<1530;y+=14)for(let x=10;x<2040;x+=17){
  const px=x+(randomAt(seed,x,y,70)-.5)*13,py=y+(randomAt(seed,x,y,71)-.5)*11;
  const col=Math.floor((px+7*Math.sin(py*.07)+3*Math.sin(px*.12))/128),row=Math.floor((py+5*Math.sin(px*.07))/96),c=world.cells[row*16+col];if(!c?.vegetation)continue;
  if(field(world,px/128-.5,py/96-.5,t=>t.land?1:0)<.65)continue;
  const dx=px-(col+.5)*128,dy=py-(row+.5)*96;
  if(c.resource&&(dx*dx/2600+dy*dy/1200)<1)continue;
  if(nearRiver(world,px,py,12))continue;
  const i=Math.floor(randomAt(seed,x,y,72)*4),kind=c.vegetation;
  const path=kind==='pine'?`pine/sprites/pine_edge_${i}.png`:kind==='jungle'?`jungle/jungle_edge_${i}.png`:`sprites/broadleaf_edge_${i}.png`;
  add(path,px,py,(kind==='pine'?29:39)*(0.85+randomAt(seed,x,y,73)*.28),.93);
 }
 for(const c of world.cells){const x=(c.x+.5)*128,y=(c.y+.57)*96;
  if(c.relief==='mountain')add(`relief/mountain_rock_${Math.floor(randomAt(seed,c.x,c.y,80)*2)}.png`,x+(c.resource?-18:0),y+(c.resource?-10:5),c.resource?86:110);
  if(c.resource==='aurochs'){add('wildlife/aurochs_0.png',x-25,y,48);add('wildlife/aurochs_1.png',x+27,y+19,44);}
  else if(c.resource)add(resourcePath[c.resource],x,y+14,c.resource==='fish'?88:102,.78);
 }
 objects.sort((a,b)=>a.depth-b.depth);for(const o of objects)ctx.drawImage(o.img,o.x,o.y,o.w,o.h);
 return canvas;
}
function nearRiver(world,x,y,r){for(const river of world.rivers)for(let i=1;i<river.nodes.length;i++){
 const [ax,ay]=river.nodes[i-1].map((v,k)=>v*(k?96:128)),[bx,by]=river.nodes[i].map((v,k)=>v*(k?96:128));
 const t=clamp(((x-ax)*(bx-ax)+(y-ay)*(by-ay))/((bx-ax)**2+(by-ay)**2));if(Math.hypot(x-ax-t*(bx-ax),y-ay-t*(by-ay))<r)return true;
 }return false;}
function drawRivers(ctx,world,seed){
 ctx.lineCap='round';ctx.lineJoin='round';
 for(const river of world.rivers){const points=[];
  river.nodes.forEach(([x,y],i)=>{if(!i){points.push([x*128,y*96]);return;}const [ax,ay]=river.nodes[i-1];for(let j=1;j<=8;j++){const t=j/8,wiggle=Math.sin(t*Math.PI)*3*(noise(seed,x+t,y+t,91)-.3);points.push([(ax+(x-ax)*t)*128+(x===ax?wiggle:0),(ay+(y-ay)*t)*96+(y===ay?wiggle:0)]);}});
  const path=()=>{ctx.beginPath();ctx.moveTo(...points[0]);for(let i=1;i<points.length-1;i++){const p=points[i],next=points[i+1];ctx.quadraticCurveTo(...p,(p[0]+next[0])/2,(p[1]+next[1])/2);}ctx.lineTo(...points.at(-1));};
  path();ctx.strokeStyle='#7b8966';ctx.lineWidth=12;ctx.stroke();ctx.strokeStyle='#467e89';ctx.lineWidth=8;ctx.stroke();ctx.strokeStyle='#6b9c9a99';ctx.lineWidth=3;ctx.stroke();
 }
}
