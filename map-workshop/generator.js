import {forestKind} from './terrain.js';
// New reconstruction, October 2026. No historical World20 layout is inferred here.
export const SIZE = 16;
export const DEFAULTS = Object.freeze({land:58,ruggedness:45,moisture:55,forest:48,resources:35});
export function hashSeed(text){let h=2166136261;for(const c of String(text)){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return h>>>0;}
export function randomAt(seed,x,y,stream=0){let h=(seed^Math.imul(x+121,374761393)^Math.imul(y+73,668265263)^Math.imul(stream+1,1442695041))>>>0;h=Math.imul(h^(h>>>13),1274126177);return ((h^(h>>>16))>>>0)/4294967296;}
const mix=(a,b,t)=>a+(b-a)*t;
export function noise(seed,x,y,stream=0){const ix=Math.floor(x),iy=Math.floor(y);let u=x-ix,v=y-iy;u=u*u*(3-2*u);v=v*v*(3-2*v);return mix(mix(randomAt(seed,ix,iy,stream),randomAt(seed,ix+1,iy,stream),u),mix(randomAt(seed,ix,iy+1,stream),randomAt(seed,ix+1,iy+1,stream),u),v);}
export function neighbors(i,n=SIZE){const x=i%n,y=Math.floor(i/n),r=[];if(x>0)r.push(i-1);if(x<n-1)r.push(i+1);if(y>0)r.push(i-n);if(y<n-1)r.push(i+n);return r;}
export function generateWorld(seedText='elderwood',input={}){
 const settings={};for(const [k,v] of Object.entries(DEFAULTS)){const a=Number(input[k]??v);settings[k]=Math.max(k==='land'?30:0,Math.min(k==='land'?78:100,Number.isFinite(a)?a:v));}
 const seed=hashSeed(seedText),n=SIZE,cells=[];
 for(let y=0;y<n;y++)for(let x=0;x<n;x++){
  const dx=(x-7.5)/7,dy=(y-7.5)/7;
  const e=1-Math.sqrt(dx*dx*.85+dy*dy)+.65*(noise(seed,x/3.8,y/3.8)-.5)+.22*(noise(seed,x/1.8,y/1.8,2)-.5);
  cells.push({x,y,elevation:e,land:false,terrain:'ocean',vegetation:null,relief:null,resource:null});
 }
 // Grow one land component toward the requested coverage; keep an ocean border.
 const target=Math.min((n-2)**2,Math.round(n*n*settings.land/100));
 const interior=i=>cells[i].x>0&&cells[i].y>0&&cells[i].x<n-1&&cells[i].y<n-1;
 let start=cells.reduce((best,c,i)=>interior(i)&&c.elevation>cells[best].elevation?i:best,8*n+8);
 const frontier=new Set([start]);
 for(let k=0;k<target;k++){
  let best=-1;for(const i of frontier)if(best<0||cells[i].elevation>cells[best].elevation)best=i;
  if(best<0)break;frontier.delete(best);cells[best].land=true;
  for(const i of neighbors(best))if(interior(i)&&!cells[i].land)frontier.add(i);
 }
 for(const c of cells){if(!c.land)continue;
  const wet=noise(seed,c.x/4,c.y/4,11)*.62+settings.moisture/100*.65;
  const h=noise(seed,c.x/2.6,c.y/2.6,17)*.7+c.elevation*.3;
  c.terrain=wet<.36?'desert':wet<.57?'plains':wet>.74?'swamp':'grassland';
  c.relief=settings.ruggedness===0?null:h>1.02-settings.ruggedness/100*.60?'mountain':h>1.08-settings.ruggedness/100*.85?'hill':null;
  const cover=noise(seed,c.x/2.5,c.y/2.5,21)*.8+randomAt(seed,c.x,c.y,23)*.2;
  if(c.relief!=='mountain'&&cover<settings.forest/100*(.6+wet*.45))c.vegetation=forestKind(c.terrain,c.relief);
  if(randomAt(seed,c.x,c.y,31)<settings.resources/100*.34){
   const choices=c.relief?['mithril','gems','voidstone']:c.vegetation?['white_stags','scarlet_pepper']:c.terrain==='desert'?['gems','voidstone']:['wheat','aurochs'];
   c.resource=choices[Math.floor(randomAt(seed,c.x,c.y,32)*choices.length)];
  }
 }
 for(const c of cells)if(!c.land&&neighbors(c.y*n+c.x).some(i=>cells[i].land)&&randomAt(seed,c.x,c.y,35)<settings.resources/100*.22)c.resource='fish';
 const rivers=makeRivers(cells,seed,settings);
 return {version:2,generator:'atlas-island-v2',seed:String(seedText),settings,width:n,height:n,projection:{tileWidth:128,tileHeight:96},cells,rivers,provenance:'New procedural geography using preserved Prototype55 assets. Not a reconstruction of World20.'};
}
function makeRivers(cells,seed,s){
 const n=SIZE,w=n+1,total=w*w,heights=[],coast=[],touchLand=[];
 for(let y=0;y<=n;y++)for(let x=0;x<=n;x++){
  const near=[];for(const dy of [-1,0])for(const dx of [-1,0])if(x+dx>=0&&x+dx<n&&y+dy>=0&&y+dy<n)near.push(cells[(y+dy)*n+x+dx]);
  heights.push(near.reduce((a,c)=>a+c.elevation,0)/near.length);
  touchLand.push(near.some(c=>c.land));coast.push(near.filter(c=>c.land).length===1&&near.filter(c=>!c.land).length>=2);
 }
 // A coast-rooted drainage tree. Strictly decreasing distance prevents cycles.
 const dist=Array(total).fill(Infinity),parent=Array(total).fill(-1),done=new Set();
 coast.forEach((v,i)=>{if(v)dist[i]=0;});
 for(let k=0;k<total;k++){
  let u=-1;for(let i=0;i<total;i++)if(!done.has(i)&&(u<0||dist[i]<dist[u]))u=i;
  if(u<0||!Number.isFinite(dist[u]))break;done.add(u);
  for(const v of neighbors(u,w)){if(!touchLand[v]||done.has(v))continue;
   const cost=1+Math.max(0,heights[u]-heights[v])*18+randomAt(seed,u,v,40)*.35;
   if(dist[u]+cost<dist[v]){dist[v]=dist[u]+cost;parent[v]=u;}
  }
 }
 const candidates=Array.from({length:total},(_,i)=>i).filter(i=>dist[i]>3&&Number.isFinite(dist[i])).sort((a,b)=>(heights[b]+randomAt(seed,b,0,41)*.4)-(heights[a]+randomAt(seed,a,0,41)*.4));
 const used=new Set(),rivers=[];const wanted=1+Math.floor(s.moisture/28);
 for(const source of candidates){if(rivers.length>=wanted)break;
  if(rivers.some(r=>Math.hypot(r.nodes[0][0]-source%w,r.nodes[0][1]-Math.floor(source/w))<4))continue;
  let at=source;const nodes=[],ids=[];
  while(at>=0){nodes.push([at%w,Math.floor(at/w)]);ids.push(at);if(used.has(at)||coast[at])break;at=parent[at];}
  if(nodes.length<4)continue;
  ids.forEach(i=>used.add(i));rivers.push({id:`river-${rivers.length+1}`,nodes,outlet:coast[ids.at(-1)]?'coast':'tributary'});
 }
 return rivers;
}
export function describeCell(c){return [c.terrain,c.vegetation&&`${c.vegetation} forest`,c.relief,c.resource?.replaceAll('_',' ')].filter(Boolean).join(' · ');}
