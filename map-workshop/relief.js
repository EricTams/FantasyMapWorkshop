import {randomAt,noise} from './generator.js';
import {displacement,segmentDistance} from './geometry.js';
const strength=c=>c?.land?(c.relief==='mountain'?1:c.relief==='hill'?.48:0):0;

// Shared ridge graph: adjacent relief cells meet at the same displaced saddle.
export function makeRelief(world,seed){
 const nodes=new Map(),segments=[],rocks=[];
 for(const c of world.cells)if(strength(c)){
  const id=c.y*world.width+c.x;
  nodes.set(id,{x:(c.x+.5)*128+(randomAt(seed,id,0,160)-.5)*38,y:(c.y+.55)*96+(randomAt(seed,id,0,161)-.5)*25,height:strength(c),cell:c,id});
 }
 // A spanning forest avoids rectangular rings in dense relief regions.
 const candidates=[],parent=new Map([...nodes.keys()].map(id=>[id,id]));
 const root=id=>{while(parent.get(id)!==id)id=parent.get(id);return id;};
 for(const n of nodes.values())for(const [dx,dy] of [[1,0],[0,1],[1,1],[-1,1]]){
  const x=n.cell.x+dx,y=n.cell.y+dy;if(x<0||x>=world.width||y>=world.height)continue;
  const other=nodes.get(y*world.width+x);if(!other)continue;
  if(dx&&dy&&!nodes.has(n.cell.y*world.width+x)&&!nodes.has(y*world.width+n.cell.x))continue;
  candidates.push({n,other,cost:Math.hypot(dx,dy)+randomAt(seed,n.id,other.id,169)*1.1});
 }
 candidates.sort((a,b)=>a.cost-b.cost);
 const links=[];
 for(const edge of candidates){const a=root(edge.n.id),b=root(edge.other.id);if(a===b)continue;parent.set(a,b);links.push(edge);}
 for(const n of nodes.values()){
  const connected=links.some(e=>e.n===n||e.other===n);
  for(const {other} of links.filter(e=>e.n===n)){
   const mx=(n.x+other.x)/2+(randomAt(seed,n.id,other.id,162)-.5)*20,my=(n.y+other.y)/2+(randomAt(seed,n.id,other.id,163)-.5)*16;
   const saddle=Math.min(n.height,other.height)*.80;
   segments.push({ax:n.x,ay:n.y,bx:mx,by:my,a:n.height,b:saddle},{ax:mx,ay:my,bx:other.x,by:other.y,a:saddle,b:other.height});
  }
  if(!connected){const angle=noise(seed,n.cell.x/4,n.cell.y/4,164)*Math.PI;
   const dx=Math.cos(angle)*36,dy=Math.sin(angle)*24;
   segments.push({ax:n.x-dx,ay:n.y-dy,bx:n.x,by:n.y,a:n.height*.5,b:n.height},{ax:n.x,ay:n.y,bx:n.x+dx,by:n.y+dy,a:n.height,b:n.height*.5});
  }
  rocks.push({x:n.x,y:n.y,peak:n.cell.relief==='mountain',width:n.cell.relief==='mountain'?86+randomAt(seed,n.id,0,170)*27:68+randomAt(seed,n.id,0,170)*18,variant:Math.floor(randomAt(seed,n.id,0,165)*2)});
 }
 for(const [i,s] of segments.entries()){
  const length=Math.hypot(s.bx-s.ax,s.by-s.ay),count=Math.max(1,Math.round(length/34));
  for(let j=0;j<count;j++){const t=(j+.5)/count;
   rocks.push({x:s.ax+(s.bx-s.ax)*t+(randomAt(seed,i,j,171)-.5)*22,y:s.ay+(s.by-s.ay)*t+(randomAt(seed,i,j,172)-.5)*17,peak:false,width:62+randomAt(seed,i,j,166)*24,variant:Math.floor(randomAt(seed,i,j,167)*2)});
  }
 }
 const buckets=world.cells.map(c=>segments.filter(s=>Math.max(s.ax,s.bx)>=c.x*128-100&&Math.min(s.ax,s.bx)<=(c.x+1)*128+100&&Math.max(s.ay,s.by)>=c.y*96-80&&Math.min(s.ay,s.by)<=(c.y+1)*96+80));
 function height(x,y){
  const col=Math.floor(x/128),row=Math.floor(y/96);if(col<0||row<0||col>=world.width||row>=world.height)return 0;
  let value=0;
  for(const s of buckets[row*world.width+col]){
   const d=segmentDistance(x,y,s),h=s.a+(s.b-s.a)*d.t,radius=46+h*22,t=Math.max(0,1-d.distance/radius);
   value=Math.max(value,h*t*t*(3-2*t));
  }return value;
 }
 return {height,rocks,segments,links:links.map(e=>[e.n.id,e.other.id])};
}

// Invert the same display→logical warp used for materials and rivers.
export function reliefPosition(seed,x,y){
 let px=x,py=y;for(let i=0;i<6;i++){const d=displacement(seed,px,py);px=x-d[0];py=y-d[1];}return [px,py];
}
export function alpineDensity(seed,x,y,height){
 const grove=.55+.75*noise(seed,x/79,y/58,168);
 return .45*grove*(1-Math.min(.8,height)*.85);
}
