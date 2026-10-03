"""A global row lattice over the union of wine cells; no per-cell phase reset."""
from pathlib import Path
from PIL import Image
from scipy.ndimage import distance_transform_edt,map_coordinates
import numpy as np,math
import coast_renderer as C
R=Path(__file__).resolve().parent/'assets/vineyard/rows';ROWS=[Image.open(R/f'vine_row_{i}_aligned_native.png').convert('RGBA') for i in range(3)]
def step(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
class VineyardField:
 def __init__(self,cells,presses,shape,land_mask,channel_mask=None,tile=128):
  H,W=shape;h,w=H*tile,W*tile;mask=np.zeros((H,W),bool)
  for r,c in cells:mask[r,c]=True
  mask=np.repeat(np.repeat(mask,tile,0),tile,1)&land_mask
  if channel_mask is not None:mask &= ~channel_mask
  yy,xx=np.mgrid[:h,:w];theta=math.radians(31);co=math.cos(theta);si=math.sin(theta);corners=[(0,0),(w,0),(0,h),(w,h)];u=[co*x-si*y for x,y in corners];v=[si*x+co*y for x,y in corners];umin=math.floor(min(u))-120;umax=math.ceil(max(u))+120;vmin=math.floor(min(v))-80;vmax=math.ceil(max(v))+80;plane=Image.new('RGBA',(umax-umin,vmax-vmin));placements=[]
  pitch=33;overlap=13;period=sum(im.width-overlap for im in ROWS)
  for row in range(math.floor(vmin/pitch)-2,math.ceil(vmax/pitch)+2):
   baseline=row*pitch+10;base=(row*29)%79-100;n=math.floor((umin-base)/period)-1;u0=base+n*period;j=n*3
   while u0<umax+100:
    index=(row+j)%3;im=ROWS[index];py=baseline-im.height+3;plane.alpha_composite(im,(round(u0-umin),round(py-vmin)));placements.append((row,index,u0,py));u0+=im.width-overlap;j+=1
  field=plane.transform((w,h),Image.Transform.AFFINE,(co,-si,-umin,si,co,-vmin),Image.Resampling.BICUBIC)
  a=np.asarray(field,float);dist=distance_transform_edt(np.pad(mask,1))[1:-1,1:-1];noise=(C._noise(xx+.5,yy+.5,13,4601)-.5)*3;support=step(.5,5,dist+noise)*mask
  # Press bays interrupt only the local footprint; row phase continues around them.
  for r,c in presses:
   q=((xx+.5-(c+.78125)*tile)/25)**2+((yy+.5-(r+.87)*tile)/18)**2
   bay=(1-step(.70,1.15,q))*((xx//tile)==c)*((yy//tile)==r);support*=1-bay
  a[:,:,3]*=support;self.rgba=np.uint8(np.round(a).clip(0,255));self.mask=mask;self.cells=cells;self.presses=presses;self.config={'row_pitch_px':pitch,'endpoint_overlap_px':overlap,'angle_degrees':31,'phase':'Global world coordinates, independent of cell and rendering chunk','boundary':'One cell-union mask, no internal edge inset','projection':'Low vine-row surface follows ground projection; press remains upright','outer_edge_limit':'Some row endpoints may be clipped by the external ownership boundary'}
 def composite(self,rgb,wx,wy):
  a=self.rgba[:,:,3].astype(float)/255;alpha=map_coordinates(a,[wy-.5,wx-.5],order=1,mode='nearest',prefilter=False);premult=np.stack([map_coordinates(self.rgba[:,:,k]*a,[wy-.5,wx-.5],order=1,mode='nearest',prefilter=False) for k in range(3)],axis=2);return rgb*(1-alpha[:,:,None])+premult
