// Visual occupancy is separate from a tree's ground anchor and depth-sort position.
export function spriteFootprint(rgba,width,height,step=2){
 let mass=0,cx=0,cy=0;const points=[];
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const alpha=rgba[(y*width+x)*4+3];mass+=alpha;cx+=(x+.5)*alpha;cy+=(y+.5)*alpha;
 }
 const center=mass?[cx/mass,cy/mass]:[width/2,height/2];let radius=0;
 for(let y=0;y<height;y+=step)for(let x=0;x<width;x+=step){
  const bw=Math.min(step,width-x),bh=Math.min(step,height-y);let occupied=false;
  for(let dy=0;dy<bh;dy++)for(let dx=0;dx<bw;dx++)if(rgba[((y+dy)*width+x+dx)*4+3]>24)occupied=true;
  if(!occupied)continue;
  const px=x+bw/2,py=y+bh/2,pad=Math.hypot(bw,bh)/2;
  points.push([px,py,pad]);radius=Math.max(radius,Math.hypot(px-center[0],py-center[1])+pad);
 }
 return {center,radius,points};
}
export function canopyClearsRiver(footprint,left,top,scale,clearanceAt,bankGap=3){
 const cx=left+footprint.center[0]*scale,cy=top+footprint.center[1]*scale;
 // The shared warp can stretch distances. This conservative bound skips distant trees.
 if(clearanceAt(cx,cy)>footprint.radius*scale*2+bankGap)return true;
 for(const [x,y,pad] of footprint.points){
  if(clearanceAt(left+x*scale,top+y*scale)<bankGap+pad*scale*1.5)return false;
 }
 return true;
}
