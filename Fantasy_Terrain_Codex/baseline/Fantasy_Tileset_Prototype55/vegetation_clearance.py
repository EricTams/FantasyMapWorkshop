"""Small deterministic openings for resources and hill cues. Artwork remains unchanged."""
import numpy as np
from scipy.ndimage import distance_transform_edt
import coast_renderer as C

def build(shape,forest_mask,features,hill_cells,tile=128):
 h,w=shape;y,x=np.mgrid[:h,:w];x=x+.5;y=y+.5;clear=np.zeros((h,w),bool);records=[]
 def opening(row,col,u,v,rx,ry,kind,seed):
  cx=(col+u)*tile;cy=(row+v)*tile;dx=(x-cx)/rx;dy=(y-cy)/ry
  # Shallow irregular shoulders, not a smooth blurred circular hole.
  warp=(C._noise(x,y,17,seed)-.5)*.28+(C._noise(x,y,8,seed+1)-.5)*.12
  mask=(dx*dx+dy*dy+warp<1)&(x>col*tile+4)&(x<(col+1)*tile-4)&(y>row*tile+4)&(y<(row+1)*tile-4)&forest_mask
  clear[:] |= mask;records.append({'cell':[row,col],'kind':kind,'center_world':[cx,cy],'radius_world':[rx,ry],'cleared_px':int(mask.sum())})
 for f in features:
  r,c=f['cell'];name=f['asset']
  if name=='grapes_resource.png':
   opening(r,c,.49,.62,58,42,'vineyard_resource_contact',4500+r*20+c)
  elif name=='vineyard_press.png':
   opening(r,c,.78,.90,24,15,'vineyard_press_contact',4540+r*20+c)
  elif name.startswith('botanical_'):
   from botanical_renderer import RESOURCES
   q=RESOURCES[name[10:-4]];u,v=q['root_uv'];rx,ry=q['clearance_radius'];opening(r,c,u,v-6/tile,rx,ry,'botanical_resource_contact',4900+r*20+c)
  elif name.startswith('mineral_'):
   from mineral_renderer import DEPOSITS
   q=DEPOSITS[name[8:-4]];u,v=q['root_uv'];rx,ry=q['clearance_radius'];opening(r,c,u,v-8/tile,rx,ry,'mineral_site_contact',4400+r*20+c)
  elif name.startswith('wildlife_'):
   from wildlife_renderer import M
   group=M['groups'][name[9:-4]]
   if group.get('water_resource'):continue
   for i,actor in enumerate(group['instances']):
    u,v=actor['root_uv'];rx,ry=actor['clearance_radius'];opening(r,c,u,v-3/tile,rx,ry,'wildlife_contact',4300+r*50+c*2+i)
  elif name=='deer_herd.png':
   opening(r,c,.27,.65-3/tile,29,18,'hoof_contact',4010+r*20+c)
   opening(r,c,.75,.84-3/tile,29,18,'hoof_contact',4050+r*20+c)
  elif name=='scarlet_pepper_bushes.png':
   opening(r,c,.32,.52-7/tile,33,22,'shrub_contact',4110+r*20+c)
   opening(r,c,.68,.84-7/tile,33,22,'shrub_contact',4150+r*20+c)
 for r,c in hill_cells:
  opening(r,c,.57,.57,55,19,'exposed_hill_slope',4200+r*20+c)
 # Positive distance is outside openings; cap/floor feathering is kept short.
 dist=distance_transform_edt(~clear)-distance_transform_edt(clear) if clear.any() else np.full((h,w),1e6)
 return clear,dist,[r for r in records if r['cleared_px']]
