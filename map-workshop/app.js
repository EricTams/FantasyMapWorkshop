import {generateWorld,hashSeed,describeCell} from './generator.js';
import {loadAssets,renderWorld} from './renderer.js?v=19';
const $=id=>document.getElementById(id),canvas=$('map'),ctx=canvas.getContext('2d'),viewport=$('viewport');
let world,art,view={scale:1,x:0,y:0},fitScale=1,drag=null,busy=false,request=0,ready=false;
const controls=['land','ruggedness','moisture','forest','resources'];
for(const key of controls)$(key).addEventListener('input',()=>{$(`${key}-value`).textContent=$(key).value+'%';schedule();});
let timer;function schedule(){clearTimeout(timer);timer=setTimeout(()=>generate(),200);}
function settings(){return Object.fromEntries(controls.map(k=>[k,+$(k).value]));}
$('controls').addEventListener('submit',e=>{e.preventDefault();clearTimeout(timer);generate();});
$('reroll').addEventListener('click',()=>{const a=new Uint32Array(1);crypto.getRandomValues(a);$('seed').value=a[0].toString(36);generate();});
async function generate(){
 if(!ready)return;const id=++request;if(busy){schedule();return;}busy=true;$('loading').hidden=false;$('loading').textContent='Shaping your world…';$('generate').disabled=true;
 try{
  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  const seed=$('seed').value.trim()||'elderwood';$('seed').value=seed;
  const next=generateWorld(seed,settings()),nextArt=renderWorld(next,hashSeed(seed));world=next;art=nextArt;
  const titles=['Reach','Isles','Wilds','Marches','Expanse','Coast'];const label=/^[a-zA-Z][a-zA-Z -]{1,24}$/.test(seed)?seed[0].toUpperCase()+seed.slice(1):['Silverpine','Ashenvale','Everspring','Thornwild','Amberfall','Mistwood'][hashSeed(seed)%6];
  $('world-name').textContent=`The ${label} ${titles[hashSeed(seed)%titles.length]}`;
  const land=world.cells.filter(c=>c.land).length,res=world.cells.filter(c=>c.resource).length;
  $('stats').textContent=`${land} land tiles · ${world.rivers.length} rivers · ${res} resources`;
  $('png').disabled=$('json').disabled=false;$('tile-info').textContent='Point to a tile to inspect it.';
  fit();
 }catch(e){console.error(e);$('loading').textContent='The map could not be generated. Try Generate world again.';return;}
 finally{busy=false;$('generate').disabled=false;}
 if(id===request)$('loading').hidden=true;else schedule();
}
function resize(){const dpr=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(viewport.clientWidth*dpr);canvas.height=Math.round(viewport.clientHeight*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);if(art)fit();}
function fit(){fitScale=Math.min(viewport.clientWidth/2048,viewport.clientHeight/1536);view.scale=fitScale;view.x=(viewport.clientWidth-2048*view.scale)/2;view.y=(viewport.clientHeight-1536*view.scale)/2;draw();}
function draw(){const w=viewport.clientWidth,h=viewport.clientHeight;ctx.fillStyle='#183441';ctx.fillRect(0,0,w,h);if(!art)return;ctx.save();ctx.translate(view.x,view.y);ctx.scale(view.scale,view.scale);ctx.drawImage(art,0,0);if($('grid').checked){ctx.lineWidth=1/view.scale;ctx.strokeStyle='#f4e2ad66';ctx.setLineDash([4/view.scale,5/view.scale]);ctx.beginPath();for(let x=0;x<=2048;x+=128){ctx.moveTo(x,0);ctx.lineTo(x,1536);}for(let y=0;y<=1536;y+=96){ctx.moveTo(0,y);ctx.lineTo(2048,y);}ctx.stroke();}ctx.restore();$('zoom-value').textContent=Math.round(view.scale/fitScale*100)+'%';}
function zoom(factor,x=viewport.clientWidth/2,y=viewport.clientHeight/2){const next=Math.max(fitScale*.75,Math.min(fitScale*5,view.scale*factor)),ratio=next/view.scale;view.x=x-(x-view.x)*ratio;view.y=y-(y-view.y)*ratio;view.scale=next;draw();}
$('zoom-in').onclick=()=>zoom(1.25);$('zoom-out').onclick=()=>zoom(.8);$('fit').onclick=fit;$('grid').onchange=draw;
viewport.addEventListener('wheel',e=>{e.preventDefault();const r=viewport.getBoundingClientRect();zoom(Math.exp(-e.deltaY*.001),e.clientX-r.left,e.clientY-r.top);},{passive:false});
viewport.addEventListener('pointerdown',e=>{if(e.target!==canvas)return;drag={x:e.clientX,y:e.clientY};viewport.setPointerCapture(e.pointerId);});
viewport.addEventListener('pointermove',e=>{if(drag){view.x+=e.clientX-drag.x;view.y+=e.clientY-drag.y;drag={x:e.clientX,y:e.clientY};draw();}if(!world)return;const r=viewport.getBoundingClientRect(),x=Math.floor((e.clientX-r.left-view.x)/view.scale/128),y=Math.floor((e.clientY-r.top-view.y)/view.scale/96);$('tile-info').textContent=x>=0&&x<16&&y>=0&&y<16?`${String.fromCharCode(65+x)}${y+1} · ${describeCell(world.cells[y*16+x])}`:'Point to a tile to inspect it.';});
viewport.addEventListener('pointerup',()=>drag=null);viewport.addEventListener('pointercancel',()=>drag=null);
viewport.addEventListener('keydown',e=>{if(e.target!==viewport)return;const moves={ArrowLeft:[40,0],ArrowRight:[-40,0],ArrowUp:[0,40],ArrowDown:[0,-40]};if(moves[e.key]){e.preventDefault();view.x+=moves[e.key][0];view.y+=moves[e.key][1];draw();}else if(e.key==='+'||e.key==='=')zoom(1.25);else if(e.key==='-')zoom(.8);else if(e.key==='0')fit();});
function download(blob,ext){const a=document.createElement('a'),url=URL.createObjectURL(blob);a.href=url;a.download=`atlas-${world.seed.replace(/[^a-z0-9_-]/gi,'_')}.${ext}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('png').onclick=()=>art.toBlob(blob=>blob&&download(blob,'png'),'image/png');$('json').onclick=()=>download(new Blob([JSON.stringify(world,null,2)],{type:'application/json'}),'json');
new ResizeObserver(resize).observe(viewport);
try{await loadAssets();ready=true;await generate();}catch(e){console.error(e);$('loading').textContent='Terrain art could not load. Reload this page to try again.';}
