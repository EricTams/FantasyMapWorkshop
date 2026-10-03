import {wrap,constrainView,nearestWrappedX,tourStops} from './camera.js?v=21b';
import {generateWorld,hashSeed,describeCell} from './generator.js?v=21';
import {loadAssets,renderWorld} from './renderer.js?v=22';
const $=id=>document.getElementById(id),canvas=$('map'),ctx=canvas.getContext('2d'),viewport=$('viewport');
let world,art,view={scale:1,x:0,y:0},fitScale=1,drag=null,busy=false,request=0,ready=false;
const controls=['land','ruggedness','moisture','forest','resources'];
for(const key of controls)$(key).addEventListener('input',()=>{$(`${key}-value`).textContent=$(key).value+'%';schedule();});
let timer;function schedule(){clearTimeout(timer);timer=setTimeout(()=>generate(),200);}
function settings(){return {...Object.fromEntries(controls.map(k=>[k,+$(k).value])),size:+$('size').value};}
$('size').onchange=()=>generate();
$('controls').addEventListener('submit',e=>{e.preventDefault();clearTimeout(timer);generate();});
$('reroll').addEventListener('click',()=>{const a=new Uint32Array(1);crypto.getRandomValues(a);$('seed').value=a[0].toString(36);generate();});
async function generate(){
 if(!ready)return;stopTour();const id=++request;if(busy){schedule();return;}busy=true;$('loading').hidden=false;$('loading').textContent='Shaping your world…';$('generate').disabled=true;
 try{
  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  const seed=$('seed').value.trim()||'elderwood';$('seed').value=seed;
  const next=generateWorld(seed,settings()),nextArt=renderWorld(next,hashSeed(seed));world=next;art=nextArt;
  const titles=['Reach','Isles','Wilds','Marches','Expanse','Coast'];const label=/^[a-zA-Z][a-zA-Z -]{1,24}$/.test(seed)?seed[0].toUpperCase()+seed.slice(1):['Silverpine','Ashenvale','Everspring','Thornwild','Amberfall','Mistwood'][hashSeed(seed)%6];
  $('world-name').textContent=`The ${label} ${titles[hashSeed(seed)%titles.length]}`;
  const land=world.cells.filter(c=>c.land).length,res=world.cells.filter(c=>c.resource).length;
  $('stats').textContent=`${land} land tiles · ${world.rivers.length} rivers · ${res} resources`;
  $('map-size').textContent=`${world.width} × ${world.height} tiles`;
  $('tour').disabled=false;
  $('png').disabled=$('json').disabled=false;$('tile-info').textContent='Point to a tile to inspect it.';
  fit();
 }catch(e){console.error(e);$('loading').textContent='The map could not be generated. Try Generate world again.';return;}
 finally{busy=false;$('generate').disabled=false;}
 if(id===request)$('loading').hidden=true;else schedule();
}
function resize(){const dpr=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(viewport.clientWidth*dpr);canvas.height=Math.round(viewport.clientHeight*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);if(art)fit();}
function fit(){stopTour();if(!art)return;fitScale=Math.min(viewport.clientWidth/art.width,viewport.clientHeight/art.height);view.scale=fitScale;view.x=(viewport.clientWidth-art.width*view.scale)/2;view.y=(viewport.clientHeight-art.height*view.scale)/2;draw();}
function draw(){const w=viewport.clientWidth,h=viewport.clientHeight;ctx.fillStyle='#183441';ctx.fillRect(0,0,w,h);if(!art)return;
 constrainView(view,art.width,art.height,w,h);
 const span=art.width*view.scale;
 for(let offset=view.x;offset<w;offset+=(span<=w?w:span)){ctx.save();ctx.translate(offset,view.y);ctx.scale(view.scale,view.scale);ctx.drawImage(art,0,0);
 if($('grid').checked){ctx.lineWidth=1/view.scale;ctx.strokeStyle='#f4e2ad66';ctx.setLineDash([4/view.scale,5/view.scale]);ctx.beginPath();for(let x=0;x<=art.width;x+=128){ctx.moveTo(x,0);ctx.lineTo(x,art.height);}for(let y=0;y<=art.height;y+=96){ctx.moveTo(0,y);ctx.lineTo(art.width,y);}ctx.stroke();}ctx.restore();}
 $('zoom-value').textContent=Math.round(view.scale/fitScale*100)+'%';}
function zoom(factor,x=viewport.clientWidth/2,y=viewport.clientHeight/2){stopTour();if(!art)return;const next=Math.max(fitScale*.75,Math.min(Math.max(1.5,fitScale*5),view.scale*factor)),ratio=next/view.scale;view.x=x-(x-view.x)*ratio;view.y=y-(y-view.y)*ratio;view.scale=next;draw();}
let tourFrame=0,tourRunning=false;
function stopTour(){tourRunning=false;cancelAnimationFrame(tourFrame);$('tour').textContent='World tour';$('tour').setAttribute('aria-pressed','false');$('tour-status').hidden=true;}
function startTour(){if(!world||busy)return;const stops=tourStops(world);if(!stops.length)return;
 tourRunning=true;$('tour').textContent='Stop tour';$('tour').setAttribute('aria-pressed','true');$('tour-status').hidden=false;
 // Tour at a readable scale: approximately seven tiles across, capped at native size.
 const scale=Math.max(fitScale,Math.min(1,viewport.clientWidth/(7*128)));
 const ratio=scale/view.scale;view.x=viewport.clientWidth/2-(viewport.clientWidth/2-view.x)*ratio;view.y=viewport.clientHeight/2-(viewport.clientHeight/2-view.y)*ratio;view.scale=scale;draw();
 let index=0,start=null,from,to;
 const visit=()=>{const stop=stops[index];from={x:view.x,y:view.y};to={x:nearestWrappedX(view.x,viewport.clientWidth/2-stop.x*scale,art.width*scale),y:viewport.clientHeight/2-stop.y*scale};
  const bounded=constrainView({...to,scale},art.width,art.height,viewport.clientWidth,viewport.clientHeight);to.y=bounded.y;
  $('tour-status').textContent=`${index+1} / ${stops.length} · ${stop.label} — drag or zoom to explore`;};
 visit();
 const frame=time=>{if(!tourRunning)return;if(start===null)start=time;const elapsed=time-start,t=Math.min(1,elapsed/2200),ease=t*t*(3-2*t);
  view.x=from.x+(to.x-from.x)*ease;view.y=from.y+(to.y-from.y)*ease;draw();
  if(elapsed>=5200){index=(index+1)%stops.length;start=time;visit();}tourFrame=requestAnimationFrame(frame);};
 tourFrame=requestAnimationFrame(frame);
}
$('tour').onclick=()=>tourRunning?stopTour():startTour();
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopTour();});
$('zoom-in').onclick=()=>zoom(1.25);$('zoom-out').onclick=()=>zoom(.8);$('fit').onclick=fit;$('grid').onchange=draw;
viewport.addEventListener('wheel',e=>{e.preventDefault();const r=viewport.getBoundingClientRect();zoom(Math.exp(-e.deltaY*.001),e.clientX-r.left,e.clientY-r.top);},{passive:false});
viewport.addEventListener('pointerdown',e=>{if(e.target!==canvas)return;stopTour();drag={x:e.clientX,y:e.clientY};viewport.setPointerCapture(e.pointerId);});
viewport.addEventListener('pointermove',e=>{if(drag){view.x+=e.clientX-drag.x;view.y+=e.clientY-drag.y;drag={x:e.clientX,y:e.clientY};draw();}if(!world)return;const r=viewport.getBoundingClientRect(),x=Math.floor(wrap((e.clientX-r.left-view.x)/view.scale,art.width)/128),y=Math.floor((e.clientY-r.top-view.y)/view.scale/96);$('tile-info').textContent=y>=0&&y<world.height?`${x+1}, ${y+1} · ${describeCell(world.cells[y*world.width+x])}`:'Point to a tile to inspect it.';});
viewport.addEventListener('pointerup',()=>drag=null);viewport.addEventListener('pointercancel',()=>drag=null);
viewport.addEventListener('keydown',e=>{if(e.target!==viewport)return;const moves={ArrowLeft:[40,0],ArrowRight:[-40,0],ArrowUp:[0,40],ArrowDown:[0,-40]};if(e.key==='Escape'){stopTour();return;}if(moves[e.key]){stopTour();e.preventDefault();view.x+=moves[e.key][0];view.y+=moves[e.key][1];draw();}else if(e.key==='+'||e.key==='=')zoom(1.25);else if(e.key==='-')zoom(.8);else if(e.key==='0')fit();});
function download(blob,ext){const a=document.createElement('a'),url=URL.createObjectURL(blob);a.href=url;a.download=`atlas-${world.seed.replace(/[^a-z0-9_-]/gi,'_')}.${ext}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('png').onclick=()=>art.toBlob(blob=>blob&&download(blob,'png'),'image/png');$('json').onclick=()=>download(new Blob([JSON.stringify(world,null,2)],{type:'application/json'}),'json');
new ResizeObserver(resize).observe(viewport);
try{await loadAssets();ready=true;await generate();}catch(e){console.error(e);$('loading').textContent='Terrain art could not load. Reload this page to try again.';}
