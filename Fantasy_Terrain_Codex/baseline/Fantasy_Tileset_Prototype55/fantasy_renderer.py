from pathlib import Path
from PIL import Image
import json
R=Path(__file__).resolve().parent/'assets/fantasy';M=json.loads((R/'fantasy_manifest.json').read_text());SPRITES=[Image.open(R/q['file']).convert('RGBA') for q in M['sprites']];SHADOWS=[Image.open(R/f'stag_shadow_{i}.png').convert('RGBA') for i in range(2)]
def objects(kind,row,col,forward,variant=0,named=False):
 out=[]
 instances=M['deer_instances'] if kind=='deer' else [{'pose':2+variant%2,'root_uv':M['spice_root_uv']}]
 for inst in instances:
  i=inst['pose'];u,v=inst['root_uv'];i=(i+variant)%2 if kind=='deer' else i;px,py,cw,ch=forward(col+u,row+v);sc=cw/128;im=SPRITES[i];im=im.resize((max(1,round(im.width*sc)),max(1,round(im.height*sc))),Image.Resampling.LANCZOS);a=M['sprites'][i]['ground_anchor']
  if kind=='deer':
   shadow=SHADOWS[i];shadow=shadow.resize((max(1,round(shadow.width*sc)),max(1,round(shadow.height*sc))),Image.Resampling.LANCZOS);out.append((py-.1,shadow,round(px-shadow.width/2),round(py-shadow.height/2)) + ((f'stag_shadow_{i}',) if named else ()))
  out.append((py,im,round(px-a[0]*sc),round(py-a[1]*sc)) + ((Path(M['sprites'][i]['file']).stem,) if named else ()))
 return out
