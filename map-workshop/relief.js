import {randomAt,noise} from './generator.js';
import {displacement,segmentDistance} from './geometry.js?v=24';
const strength=c=>c?.land?(c.relief==='mountain'?1:c.relief==='hill'?.48:0):0;

// Shared ridge graph: adjacent relief cells meet at the same displaced saddle.
export function makeRelief(world,seed){
 const nodes=new Map(),segments=[],rocks=[];
 for(const c of world.cells)if(strength(c)){
  const id=c.y*world.width+c.x;
  nodes.set(id,{x:(c.x+.5)*128+(randomAt(seed,id,0,160)-.5)*38,y:(c.y+.55)*96+(randomAt(seed,id,0,161)-.5)*25,height:strength(c),cell:c,id});
 }
 // Smooth two-dimensional support, including the spaces between ridge branches.
 const at=(x,y)=>y>=0&&y<world.height&&(world.wrapX||x>=0&&x<world.width)?strength(world.cells[y*world.width+((x%world.width)+world.width)%world.width]):0;
 const blend=(x,y,read)=>{
  const gx=x/128-.5,gy=y/96-.5,ix=Math.floor(gx),iy=Math.floor(gy);
  let u=gx-ix,v=gy-iy;u=u*u*(3-2*u);v=v*v*(3-2*v);
  return (read(ix,iy)*(1-u)+read(ix+1,iy)*u)*(1-v)+(read(ix,iy+1)*(1-u)+read(ix+1,iy+1)*u)*v;
 };
 const density=(x,y)=>{let n=0;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++)if(at(x+dx,y+dy))n++;return Math.max(0,Math.min(1,(n-3)/4));};
 const breadth=(x,y)=>blend(x,y,density);
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
  if(n.cell.relief==='mountain'||randomAt(seed,n.id,0,173)>breadth(n.x,n.y))rocks.push({x:n.x,y:n.y,peak:n.cell.relief==='mountain',width:n.cell.relief==='mountain'?128+randomAt(seed,n.id,0,170)*30:68+randomAt(seed,n.id,0,170)*18,variant:Math.floor(randomAt(seed,n.id,0,165)*2)});
 }
 for(const [i,s] of segments.entries()){
  const length=Math.hypot(s.bx-s.ax,s.by-s.ay),count=Math.max(1,Math.round(length/34));
  for(let j=0;j<count;j++){const t=(j+.5)/count;
   if(randomAt(seed,i,j,174)<breadth(s.ax+(s.bx-s.ax)*t,s.ay+(s.by-s.ay)*t))continue;
   rocks.push({x:s.ax+(s.bx-s.ax)*t+(randomAt(seed,i,j,171)-.5)*22,y:s.ay+(s.by-s.ay)*t+(randomAt(seed,i,j,172)-.5)*17,peak:false,width:62+randomAt(seed,i,j,166)*24,variant:Math.floor(randomAt(seed,i,j,167)*2)});
  }
 }
 // Broad blocks get area-distributed knolls, not a trace of the ridge graph.
 for(let y=24;y<world.height*96;y+=39)for(let x=24;x<world.width*128;x+=49){
  const px=x+(randomAt(seed,x,y,175)-.5)*30,py=y+(randomAt(seed,x,y,176)-.5)*24;
  if(!at(Math.floor(px/128),Math.floor(py/96)))continue;
  if(randomAt(seed,x,y,177)>breadth(px,py)*.88)continue;
  rocks.push({x:px,y:py,peak:false,width:92+randomAt(seed,x,y,178)*32,variant:Math.floor(randomAt(seed,x,y,179)*2)});
 }
 // Mountain neighbors share broad rocky saddles, including non-spine edges.
 const mountainNodes=[...nodes.values()].filter(n=>n.cell.relief==='mountain');
 for(const n of mountainNodes)for(const [dx,dy] of [[1,0],[0,1]]){
  const other=nodes.get((n.cell.y+dy)*world.width+n.cell.x+dx);
  if(!other||other.cell.relief!=='mountain'||other.cell.x!==n.cell.x+dx)continue;
  rocks.push({x:(n.x+other.x)/2,y:(n.y+other.y)/2,rocky:true,saddle:true,width:132+randomAt(seed,n.id,other.id,181)*18,heightScale:.55,variant:Math.floor(randomAt(seed,n.id,other.id,182)*2)});
 }
 // Interior knolls become smaller crags; grassy shoulders remain at the perimeter.
 for(const r of rocks){
  if(r.peak||r.rocky)continue;
  const col=Math.floor(r.x/128),row=Math.floor(r.y/96),n=nodes.get(row*world.width+col);
  if(n?.cell.relief==='mountain'&&mountainNodes.some(m=>m!==n&&Math.abs(m.cell.x-col)+Math.abs(m.cell.y-row)===1)){
   r.rocky=true;r.width*=.92;r.heightScale=.74;
  }
 }
 if(world.wrapX){const original=[...segments];for(const dx of [-world.width*128,world.width*128])for(const s of original)segments.push({...s,ax:s.ax+dx,bx:s.bx+dx});}
 const buckets=world.cells.map(c=>segments.filter(s=>Math.max(s.ax,s.bx)>=c.x*128-100&&Math.min(s.ax,s.bx)<=(c.x+1)*128+100&&Math.max(s.ay,s.by)>=c.y*96-80&&Math.min(s.ay,s.by)<=(c.y+1)*96+80));
 function height(x,y){
  if(world.wrapX)x=((x%(world.width*128))+world.width*128)%(world.width*128);
  const col=Math.floor(x/128),row=Math.floor(y/96);if(col<0||row<0||col>=world.width||row>=world.height)return 0;
  let value=0;
  for(const s of buckets[row*world.width+col]){
   const d=segmentDistance(x,y,s),h=s.a+(s.b-s.a)*d.t,radius=46+h*22,t=Math.max(0,1-d.distance/radius);
   value=Math.max(value,h*t*t*(3-2*t));
  }
  const mass=blend(x,y,at),b=breadth(x,y);
  const rolling=.73+.23*noise(seed,x/83,y/62,180);
  return Math.max(value*(1-b*.78),mass*rolling)+value*b*.12;
 }
 // Keep the summit silhouette exposed above the surrounding foothills.
 const peaks=rocks.filter(r=>r.peak);
 const visibleRocks=rocks.filter(r=>r.peak||r.rocky||!peaks.some(p=>Math.hypot((r.x-p.x)/57,(r.y-p.y)/43)<1));
 return {height,breadth,rocks:visibleRocks,segments,links:links.map(e=>[e.n.id,e.other.id])};
}

// Invert the same display→logical warp used for materials and rivers.
export function reliefPosition(seed,x,y,period=0){
 let px=x,py=y;for(let i=0;i<6;i++){const d=displacement(seed,px,py,period);px=x-d[0];py=y-d[1];}return [px,py];
}
export function alpineDensity(seed,x,y,height){
 const grove=.55+.75*noise(seed,x/79,y/58,168);
 return .45*grove*(1-Math.min(.8,height)*.85);
}

// Only mountain terrain may receive visible rock above its anchor's logical row.
export function mountainFitsNorth(world,seed,footprint,left,top,scale,anchorRow){
 const period=world.wrapX?world.width*128:0;
 for(const [x,y,pad] of footprint.points){
  for(const side of [-1,1]){
   const px=left+(x+side*pad)*scale,py=top+(y-pad)*scale-2;
   const [dx,dy]=displacement(seed,px,py,period),col=world.wrapX?((Math.floor((px+dx)/128)%world.width)+world.width)%world.width:Math.floor((px+dx)/128),row=Math.floor((py+dy)/96);
   if(row>=anchorRow)continue;
   if(col<0||col>=world.width||row<0||world.cells[row*world.width+col]?.relief!=='mountain')return false;
  }
 }return true;
}
