from pathlib import Path
import json,math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
from deterministic_hash import hash32
R=Path(__file__).resolve().parent/'assets/relief'
class ReliefLayer:
 def __init__(self,hill_cells,mountain_cells,shape,tile=128,terrain_ids=None):
  self.hill_mask=np.zeros(shape,bool);self.mountain_mask=np.zeros(shape,bool)
  for r,c in hill_cells:self.hill_mask[r,c]=True
  for r,c in mountain_cells:self.mountain_mask[r,c]=True
  self.mask=self.hill_mask|self.mountain_mask;self.tile=tile;self.terrain_ids=terrain_ids;self.meta=json.loads((R/'relief_manifest.json').read_text())['sprites'];self.sprites=[Image.open(R/m['file']).convert('RGBA') for m in self.meta];self.anchors=[];h,w=shape;candidates=[];owned=np.repeat(np.repeat(self.hill_mask,tile,0),tile,1);inner=distance_transform_edt(owned)
  for gy in range(math.ceil(h*tile/32)):
   for gx in range(math.ceil(w*tile/32)):
    x=gx*32+(hash32(gx,gy,331)%3200)/100;y=gy*32+(hash32(gx,gy,332)%3200)/100
    if x<w*tile and y<h*tile and self.hill_mask[int(y//tile),int(x//tile)] and inner[int(y),int(x)]>=20:candidates.append((hash32(gx,gy,333),y,x,hash32(gx,gy,334)%2))
  for _,y,x,i in sorted(candidates):
   if sum(int(by//tile)==int(y//tile) and int(bx//tile)==int(x//tile) for by,bx,_ in self.anchors)<2 and all(((x-bx)/82)**2+((y-by)/46)**2>=1 for by,bx,_ in self.anchors):self.anchors.append((y,x,i))
  for r,c in hill_cells:
   cx=(c+.5)*tile;cy=(r+.58)*tile
   if not any(((x-cx)/72)**2+((y-cy)/35)**2<.65 for y,x,_ in self.anchors):self.anchors.append((cy,cx,hash32(c,r,335)%2))
  for r,c in mountain_cells:self.anchors.append(((r+.77)*tile,(c+.5)*tile+(hash32(c,r,336)%1000)/100-5,2+(hash32(c,r,337)+c)%2))
  self.anchors.sort();manifest=json.loads((R/'relief_manifest.json').read_text());self.variants={k:[Image.open(R/m['file']).convert('RGBA') for m in v] for k,v in manifest.get('climate_variants',{}).items()}
 def objects(self,forward,mountains=False,named=False):
  out=[]
  for y,x,i in self.anchors:
   if (i>=2)!=mountains:continue
   px,py,cw,ch=forward(x/self.tile,y/self.tile);sc=cw/self.tile;climate={0:'sand',4:'tundra',5:'snow'}.get(int(self.terrain_ids[int(y//self.tile),int(x//self.tile)])) if self.terrain_ids is not None else None;im=self.variants.get(climate,self.sprites)[i];im=im.resize((max(1,round(im.width*sc)),max(1,round(im.height*sc))),Image.Resampling.LANCZOS);a=self.meta[i]['ground_anchor'];out.append((py,im,round(px-a[0]*sc),round(py-a[1]*sc)) + ((Path(self.meta[i]['file']).stem+('_'+climate if climate in self.variants else ''),) if named else ()))
  return out
 def draw(self,image,forward,box=None):
  out=image.convert('RGBA');x0,y0=(0,0) if box is None else box[:2]
  for _,im,x,y in self.objects(forward,False):out.alpha_composite(im,(x-x0,y-y0))
  return out
