from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;OUT=R/'examples/mixed_junctions';(OUT/'previews').mkdir(exist_ok=True)
from kit_renderer import KitScene,get_font
s=json.loads((OUT/'scene.json').read_text());trace=json.loads((OUT/'shoreline.json').read_text());features=json.loads((OUT/'features.json').read_text())
k=KitScene(s,trace,features);im=k.render();font=get_font('DejaVuSans.ttf',17);bold=get_font('DejaVuSans-Bold.ttf',23)
for grid in [False,True]:
 pic=k.grid(im) if grid else im;out=Image.new('RGB',(im.width,im.height+150),(20,37,31));out.paste(pic,(0,77));d=ImageDraw.Draw(out);d.text((18,14),'Jungle in the mixed fantasy landscape',font=bold,fill=(241,238,220));d.text((18,47),'Woodland, clearing, river and coast junctions; resources and hills share feature cells',font=font,fill=(199,210,193))
 if grid:
  for row,col,lab in [(2,1,'STAGS + WOOD'),(2,2,'PEPPERS + J'),(0,2,'HILL + J')]:
   x,y,_,_=k.forward(col+.04,row+.88);d.text((x,y+77),lab,font=get_font('DejaVuSans.ttf',11),fill=(255,244,233),stroke_width=1,stroke_fill=(30,35,23))
 d.text((18,im.height+94),'Original authored scenario. Current jungle art uses continuous interiors and rooted edge sprites.',font=font,fill=(193,207,190));d.text((18,im.height+119),'Resource contact openings and exposed hill slopes are built from shared vegetation masks.',font=font,fill=(193,207,190));out.save(OUT/'previews'/('current_mixed_junctions_grid.png' if grid else 'current_mixed_junctions.png'))
print('Mixed preview saved',flush=True)
for name,data in [('scene',s),('shoreline',trace),('features',features)]: (OUT/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
qa=k.qa();qa['original_fantasy_scenario']=True;qa['shared_feature_resource_cells']=[[2,1],[2,2]];qa['shared_hill_jungle_cells']=[[0,2]];(OUT/'validation.json').write_text(json.dumps(qa,indent=2)+'\n');print(qa,flush=True)

from render_example import build
build(OUT)
