// Native anchors and pair layouts from the preserved fantasy/pepper manifests.
// Each member participates independently in the shared ground-depth sort.
export function resourceMembers(kind,col,row){
 // New mineral deposits are loose groups with independent depth and clearance.
 if(['mithril','gems','voidstone'].includes(kind)){
  return [[.36,.44,62],[.74,.61,37],[.30,.83,29]].map(([u,v,width])=>({path:`minerals/reconstructed/${kind==='gems'?'rubies':kind}.png`,x:(col+u)*128,y:(row+v)*96,width,anchor:.80,protectedFraction:.92}));
 }
 const families={
  white_stags:{folder:'fantasy',stem:'white_stag',width:48,anchor:.97,protectedFraction:.84,roots:[[.27,.65],[.75,.84]]},
  scarlet_pepper:{folder:'pepper',stem:'scarlet_pepper',width:70,anchor:.95,protectedFraction:.85,roots:[[.32,.52],[.68,.84]]}
 };
 const family=families[kind];if(!family)return [];
 return family.roots.map(([u,v],pose)=>({path:`${family.folder}/${family.stem}_${pose}.png`,x:(col+u)*128,y:(row+v)*96,width:family.width*.9,anchor:family.anchor,protectedFraction:family.protectedFraction}));
}
