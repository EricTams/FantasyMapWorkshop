from pathlib import Path
from PIL import Image
import json
R=Path(__file__).resolve().parent/'assets/pepper';M=json.loads((R/'pepper_manifest.json').read_text());S=[Image.open(R/v['file']).convert('RGBA') for v in M['sprites']]
def objects(row,col,forward,variant=0,named=False):
 out=[]
 for q in M['instances']:
  i=(q['pose']+variant)%2;u,v=q['root_uv'];px,py,cw,ch=forward(col+u,row+v);sc=cw/128;im=S[i].resize((max(1,round(S[i].width*sc)),max(1,round(S[i].height*sc))),Image.Resampling.LANCZOS);a=M['sprites'][i]['ground_anchor'];out.append((py,im,round(px-a[0]*sc),round(py-a[1]*sc)) + ((Path(M['sprites'][i]['file']).stem,) if named else ()))
 return out
