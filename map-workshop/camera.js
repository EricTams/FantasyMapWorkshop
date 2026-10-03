export const wrap=(value,period)=>((value%period)+period)%period;
export function constrainView(view,mapWidth,mapHeight,width,height){
 const span=mapWidth*view.scale,h=mapHeight*view.scale;
 view.x=span<=width?(width-span)/2:wrap(view.x,span)-span;
 view.y=h<=height?(height-h)/2:Math.max(height-h,Math.min(0,view.y));
 return view;
}
export function nearestWrappedX(current,target,span){return current+wrap(target-current+span/2,span)-span/2;}
export function tourStops(world){
 const stops=[];
 const add=(label,predicate)=>{const cells=world.cells.filter(predicate);if(!cells.length)return;
  // Prefer a visible interior example, away from the polar edges.
  const c=cells.reduce((best,c)=>Math.abs(c.y-world.height/2)<Math.abs(best.y-world.height/2)?c:best);
  stops.push({label,x:(c.x+.5)*128,y:(c.y+.5)*96});};
 for(const [kind,label] of Object.entries({mithril:'Mithril',gems:'Ruby crystals',voidstone:'Voidstone',white_stags:'White stags',scarlet_pepper:'Scarlet pepper',wheat:'Wheat',aurochs:'Aurochs',fish:'Coastal fish'}))add(label,c=>c.resource===kind);
 for(const [kind,label] of Object.entries({grassland:'Grasslands',plains:'Sage scrub plains',desert:'Desert wetlands',swamp:'Swamp forest'}))add(label,c=>c.land&&c.terrain===kind&&c.vegetation&&c.relief===null);
 add('Alpine hills',c=>c.vegetation==='alpine');add('Mountain range',c=>c.relief==='mountain');
 return stops;
}
