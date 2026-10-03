from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parent/'assets/vineyard';PLOTS=[Image.open(R/f'grapes_plot_{i}.png').convert('RGBA') for i in range(2)];PRESSES=[Image.open(R/f'vineyard_press_{i}.png').convert('RGBA') for i in range(2)]
def objects(kind,row,col,forward,variant=0,named=False):
 index=variant%2;im=(PLOTS if kind=='grapes' else PRESSES)[index]
 if kind=='grapes':
  # Center the full plot in the projected gameplay cell; do not ground-squash its upright vines.
  px,py,cw,ch=forward(col+.484,row+.50);sc=cw/128;im=im.resize((max(1,round(im.width*sc)),max(1,round(im.height*sc))),Image.Resampling.LANCZOS);_,depth,_,_=forward(col+.484,row+.89);return [(depth,im,round(px-im.width/2),round(py-im.height/2),f'grapes_plot_{index}')] if named else [(depth,im,round(px-im.width/2),round(py-im.height/2))]
 px,py,cw,ch=forward(col+.78125,row+.93);sc=cw/128;im=im.resize((max(1,round(im.width*sc)),max(1,round(im.height*sc))),Image.Resampling.LANCZOS);return [(py,im,round(px-im.width*.5),round(py-im.height*.94),f'vineyard_press_{index}')] if named else [(py,im,round(px-im.width*.5),round(py-im.height*.94))]
