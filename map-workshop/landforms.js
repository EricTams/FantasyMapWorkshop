// Large-scale silhouettes precede terrain detail. All x distances live on a cylinder.
const wrap=(x,n)=>((x%n)+n)%n;
export function worldNeighbors(i,n){const x=i%n,y=Math.floor(i/n);return [y*n+wrap(x-1,n),y*n+wrap(x+1,n),...(y>0?[i-n]:[]),...(y<n-1?[i+n]:[])];}
export function buildPangea(cells,n,seed,settings,randomAt,noise){
 const complexity=settings.complexity/100;
 const rnd=(i,s=200)=>randomAt(seed,i,0,s);
 const center=rnd(0)*n,spine=[],tilt=(rnd(0,211)-.5)*.9;
 for(let i=0;i<5;i++)spine.push({x:center+(i-2)*n*.10,y:n*(.48+(rnd(i,201)-.5)*.36),rx:n*(.13+rnd(i,202)*.045),ry:n*(.24+rnd(i,203)*.07)});
 // Branches create broad peninsulas, rather than merely roughening the coast.
 for(let i=0;i<3;i++){const root=spine[1+i],side=i%2?1:-1;spine.push({x:root.x+(rnd(i,204)-.5)*n*.18,y:root.y+side*n*.19,rx:n*.12,ry:n*.17});}
 for(const l of spine){const x=l.x-center,y=l.y-n*.5;l.x=center+x*Math.cos(tilt)-y*Math.sin(tilt);l.y=n*.5+x*Math.sin(tilt)+y*Math.cos(tilt);}
 const bays=Array.from({length:4},(_,i)=>({x:center+(i-1.5)*n*.13,y:i%2?n*.78:n*.22,rx:n*(.045+.065*complexity),ry:n*(.17+.22*complexity)}));
 const dx=(x,c)=>wrap(x-c+n/2,n)-n/2;
 for(const c of cells){
  let score=-10;for(const l of spine)score=Math.max(score,1-Math.hypot(dx(c.x+.5,l.x)/l.rx,(c.y+.5-l.y)/l.ry));
  for(const b of bays)score-=(.15+complexity*2.0)*Math.exp(-2*((dx(c.x+.5,b.x)/b.rx)**2+((c.y+.5-b.y)/b.ry)**2));
  // Periodic detail, with frequency independent of map size.
  const nx=wrap(c.x-center+n/2,n),blend=nx/n;
  score+=(.07+.20*complexity)*((noise(seed,nx/2.8,c.y/2.8,210)*(1-blend)+noise(seed,(nx-n)/2.8,c.y/2.8,210)*blend)-.5);
  c.elevation=score;c.land=false;
 }
 const target=Math.min(n*(n-2),Math.round(n*n*settings.land/100)),mainTarget=target;
 const interior=i=>cells[i].y>0&&cells[i].y<n-1;
 const start=cells.reduce((best,c,i)=>interior(i)&&c.elevation>cells[best].elevation?i:best,Math.floor(n/2)*n);
 const frontier=new Set([start]);
 for(let k=0;k<mainTarget;k++){
  let best=-1;for(const i of frontier)if(best<0||cells[i].elevation>cells[best].elevation)best=i;
  if(best<0)break;frontier.delete(best);cells[best].land=true;
  for(const j of worldNeighbors(best,n))if(interior(j)&&!cells[j].land)frontier.add(j);
 }
 // Put the display seam through the quietest ocean corridor when possible.
 // Connectivity is cylindrical even when extreme land coverage leaves no ocean cut.
 let cut=0,best=Infinity;
 for(let x=0;x<n;x++){let score=0;for(let y=0;y<n;y++){
  const a=cells[y*n+x].land,b=cells[y*n+wrap(x-1,n)].land;
  score+=(a&&b?100:0)+(a?1:0)+(b?1:0);
 }if(score<best){best=score;cut=x;}}
 const original=[...cells];
 for(let y=0;y<n;y++)for(let x=0;x<n;x++)cells[y*n+x]={...original[y*n+wrap(x+cut,n)],x,y};
 // Elevation remains useful for relief; coastline scores need not dictate mountain height.
 for(const c of cells)c.elevation=Math.max(-1,Math.min(1,c.elevation+.24));
}
