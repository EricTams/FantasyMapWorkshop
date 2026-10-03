from pathlib import Path
from PIL import Image
import json
R=Path(__file__).resolve().parent/'assets/wildlife';M=json.load(open(R/'wildlife_manifest.json'));SPRITES=[Image.open(R/v['file']).convert('RGBA') for v in M['sprites']];SHADOWS=[Image.open(R/v['shadow_file']).convert('RGBA') for v in M['sprites']]
def objects(kind,row,col,forward,variant=0,named=False):
 out=[]
 for item in M['groups'][kind]['instances']:
  idx=item['sprite'];u,v=item['root_uv'];px,py,cw,ch=forward(col+u,row+v);sc=cw/128;im=SPRITES[idx];meta=M['sprites'][idx];im=im.resize((max(1,round(im.width*sc)),max(1,round(im.height*sc))),Image.Resampling.LANCZOS);shadow=SHADOWS[idx].resize((max(1,round(SHADOWS[idx].width*sc)),max(1,round(SHADOWS[idx].height*sc))),Image.Resampling.LANCZOS);anchor=meta['root_anchor'];out.append((py-.1,shadow,round(px-anchor[0]*sc),round(py-4*sc)));out.append((py,im,round(px-anchor[0]*sc),round(py-anchor[1]*sc)))
 return [(d,im,l,t,M['sprites'][M['groups'][kind]['instances'][i//2]['sprite']]['name']+('_shadow' if i%2==0 else '')) for i,(d,im,l,t) in enumerate(out)] if named else out
