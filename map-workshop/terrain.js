export const TERRAIN_FAMILIES=['grassland','plains','swamp','desert'];
export function forestKind(terrain,relief){
 if(relief==='mountain')return null;
 if(relief==='hill')return 'alpine';
 return {grassland:'broadleaf',plains:'scrub',swamp:'jungle',desert:'wetland'}[terrain]??null;
}
export function terrainVariant(cell){
 return cell.relief==='mountain'?'mountain':cell.relief==='hill'?(cell.vegetation?'forest+hills':'hills'):cell.vegetation?'forest':'flat';
}
