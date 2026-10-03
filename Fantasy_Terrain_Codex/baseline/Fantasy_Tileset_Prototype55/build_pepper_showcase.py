from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));from kit_renderer import KitScene,get_font
OUT=R/'examples/scarlet_pepper_valley';(OUT/'previews').mkdir(parents=True,exist_ok=True)
from pepper_renderer import objects as pepper_objects
s=json.loads((OUT/'scene.json').read_text());trace=json.loads((OUT/'shoreline.json').read_text());features=json.loads((OUT/'features.json').read_text())
k=KitScene(s,trace,features,R/'assets/resources');im=k.render();font=get_font('DejaVuSans.ttf',17);bold=get_font('DejaVuSans-Bold.ttf',23)
for grid in [False,True]:
 pic=k.grid(im) if grid else im;out=Image.new('RGB',(im.width,im.height+130),(20,37,31));out.paste(pic,(0,75));d=ImageDraw.Draw(out);d.text((18,14),'Scarlet pepper bushes on the fantasy map',font=bold,fill=(241,238,220));d.text((18,46),'Spices: low green shrubs with obvious red pepper fruit',font=font,fill=(199,210,193))
 if grid:
  for row,col in [[3,2],[4,1]]:
   x,y,cw,ch=k.forward(col+.05,row+.10);d.text((x,y+75),'PEPPERS',font=font,fill=(252,233,212),stroke_width=1,stroke_fill=(32,40,27))
 d.text((18,im.height+91),'Original authored scenario; no spice locations are asserted in the Civ4 reference layouts.',font=font,fill=(193,207,190));out.save(OUT/'previews'/('pass36_scarlet_pepper_map_grid.png' if grid else 'pass36_scarlet_pepper_map.png'))
# Native128px pepper resource composition, with original generated sprite pixels.
tile=Image.new('RGBA',(128,128));f=lambda u,v:(u*128,v*128,128,128)
for _,p,x,y in sorted(pepper_objects(0,0,f),key=lambda q:q[0]):tile.alpha_composite(p,(x,y))
tile.save(R/'assets/pepper/scarlet_pepper_bushes.png')
(OUT).mkdir(exist_ok=True)
for name,data in [('scene',s),('shoreline',trace),('features',features)]: (OUT/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
qa=k.qa();qa['all_base_terrain_assigned']=bool(not(k.ids==255).any());qa['original_fantasy_layout']=True;qa['pepper_cells']=[[3,2],[4,1]];qa['original_spice_mapping']='Scarlet pepper bushes: low shrubs with obvious red fruit';(OUT/'validation.json').write_text(json.dumps(qa,indent=2)+'\n');print(qa,flush=True)

from render_example import build
build(OUT)
