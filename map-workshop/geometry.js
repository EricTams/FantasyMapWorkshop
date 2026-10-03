// Shared inverse mapping: every rendered layer asks which logical point owns a pixel.
// This moves boundaries and material coordinates together without changing game data.
import {noise} from './generator.js';
export const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
export function displacement(seed,x,y){
 const wy=y/0.75;
 return [
  (noise(seed,x/73,wy/73,101)-.5)*23+(noise(seed,x/21,wy/21,103)-.5)*5,
  ((noise(seed,x/73,wy/73,102)-.5)*23+(noise(seed,x/21,wy/21,104)-.5)*5)*.75
 ];
}
export function ownership(x,y,band=5){
 const axis=(v,size)=>{const i=Math.floor(v/size),f=v-i*size;
  if(f<band)return [[i, .5+f/(2*band)],[i-1,.5-f/(2*band)]];
  if(f>size-band)return [[i,.5+(size-f)/(2*band)],[i+1,.5-(size-f)/(2*band)]];
  return [[i,1]];
 };
 return axis(y,96).flatMap(([row,wy])=>axis(x,128).map(([col,wx])=>({col,row,weight:wx*wy})));
}
export function segmentDistance(x,y,s){
 const vx=s.bx-s.ax,vy=s.by-s.ay;
 const t=clamp(((x-s.ax)*vx+(y-s.ay)*vy)/(vx*vx+vy*vy));
 return {distance:Math.hypot(x-s.ax-t*vx,y-s.ay-t*vy),t};
}
export function makeGeometry(world){
 const coast=[],rivers=[];
 const land=(x,y)=>x>=0&&y>=0&&x<world.width&&y<world.height&&world.cells[y*world.width+x].land;
 for(const c of world.cells){if(!c.land)continue;
  const x=c.x*128,y=c.y*96;
  if(!land(c.x-1,c.y))coast.push({ax:x,ay:y,bx:x,by:y+96});
  if(!land(c.x+1,c.y))coast.push({ax:x+128,ay:y,bx:x+128,by:y+96});
  if(!land(c.x,c.y-1))coast.push({ax:x,ay:y,bx:x+128,by:y});
  if(!land(c.x,c.y+1))coast.push({ax:x,ay:y+96,bx:x+128,by:y+96});
 }
 for(const route of world.rivers){let length=0;for(let i=1;i<route.nodes.length;i++){
  const [a,b]=[route.nodes[i-1],route.nodes[i]],s={ax:a[0]*128,ay:a[1]*96,bx:b[0]*128,by:b[1]*96,start:length};
  s.length=Math.hypot(s.bx-s.ax,s.by-s.ay);length+=s.length;rivers.push(s);
 }}
 const buckets=segments=>Array.from({length:world.width*world.height},(_,i)=>{const x=i%world.width,y=Math.floor(i/world.width);return segments.filter(s=>Math.max(s.ax,s.bx)>=(x-1)*128&&Math.min(s.ax,s.bx)<=(x+2)*128&&Math.max(s.ay,s.by)>=(y-1)*96&&Math.min(s.ay,s.by)<=(y+2)*96);});
 const cb=buckets(coast),rb=buckets(rivers);
 const bucket=(x,y)=>clamp(Math.floor(y/96),0,world.height-1)*world.width+clamp(Math.floor(x/128),0,world.width-1);
 return {
  coastDistance(x,y){let d=192;for(const s of cb[bucket(x,y)])d=Math.min(d,segmentDistance(x,y,s).distance);return d*(land(Math.floor(x/128),Math.floor(y/96))?1:-1);},
  riverDistance(x,y){let best=192,progress=100;for(const s of rb[bucket(x,y)]){const v=segmentDistance(x,y,s);if(v.distance<best){best=v.distance;progress=s.start+v.t*s.length;}}return {distance:best,progress};}
 };
}
