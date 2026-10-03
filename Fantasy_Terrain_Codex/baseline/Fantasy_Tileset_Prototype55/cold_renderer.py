"""Original cold material fields and neighbor-connected floating pack ice."""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter,distance_transform_edt
import coast_renderer as C
import ground_field as GF
R=Path(__file__).resolve().parent/'assets/cold';M=json.load(open(R/'cold_manifest.json'))
def cold_ground(rgb,ids,land_alpha,x,y,sampler,T=128):
 out=rgb.copy();weights={}
 for code,name in [(4,'frost_heath'),(5,'snowfields')]:
  if not np.any(ids==code):continue
  raw=np.repeat(np.repeat(ids==code,T,0),T,1).astype(float)
  w=C._step(.3,.7,gaussian_filter(raw,5))*land_alpha
  material=np.asarray(Image.open(R/M['materials'][name]['file']).convert('RGB'),float);field=GF.prepare(material,sampler);texture=GF.sample(field,x+.5,y+.5,sampler)
  out=out*(1-w[:,:,None])+texture*w[:,:,None];weights[name]=w
 return out,weights
class IceField:
 def __init__(self,cells,ids,land_alpha,shape,T=128):
  H,W=shape;self.cells=[list(q) for q in cells];self.valid=np.zeros((H*T,W*T),bool)
  for r,c in self.cells:
   if ids[r,c]!=2:raise ValueError('Pack ice must retain an underlying water terrain ID')
   self.valid[r*T:(r+1)*T,c*T:(c+1)*T]=True
  self.water_clearance=distance_transform_edt(land_alpha<.5)
  self.valid &= land_alpha<.5;self.distance=distance_transform_edt(self.valid)-distance_transform_edt(~self.valid);y,x=np.mgrid[:H*T,:W*T];warp=(C._noise(x+.5,y+.5,25,5201)-.5)*9
  self.alpha=C._step(2,15,self.distance+warp)*(1-land_alpha)
  mat=np.asarray(Image.open(R/M['materials']['pack_ice']['file']).convert('RGB'),float)
  self.texture=C.sample_material(mat,x+.5,y+.5,scale=3.4,overlap=.125)
  self.sprites=[Image.open(R/q['file']).convert('RGBA') for q in M['edge_sprites']];self.anchors=[]
  for gy in range(math.ceil(H*T/25)):
   for gx in range(math.ceil(W*T/25)):
    bx=gx*25+7+(gx*7+gy*11)%12;by=gy*25+6+(gx*13+gy*3)%13
    if bx>=W*T or by>=H*T:continue
    if self.valid[by,bx] and self.water_clearance[by,bx]>=25 and 5<=self.distance[by,bx]<=20:
     if all((bx-ax)**2+(by-ay)**2>31**2 for ay,ax,_ in self.anchors):self.anchors.append((by,bx,(gx+2*gy)%3))
 def ground(self,rgb):return rgb*(1-self.alpha[:,:,None])+self.texture*self.alpha[:,:,None]
 def objects(self,forward,T=128,named=False):
  out=[]
  for y,x,idx in self.anchors:
   px,py,cw,ch=forward(x/T,y/T);im=self.sprites[idx];im=im.resize((max(1,round(im.width*cw/T)),max(1,round(im.height*ch/T))),Image.Resampling.LANCZOS);out.append((py,im,round(px-im.width/2),round(py-im.height/2)) + ((f'ice_edge_{idx}',) if named else ()))
  return out
