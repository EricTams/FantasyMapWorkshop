"""Existing shell sprites rendered below a reusable water-surface highlight field."""
import numpy as np
from PIL import Image
import coast_renderer as C

def composite(image,objects,box,water_mask,surface_highlight,painted_waterline=False):
 x0,y0,w,h=box;yy,xx=np.mgrid[y0:y0+h,x0:x0+w];layer=Image.new('RGBA',(w,h));bed=np.zeros((h,w),float)
 # The group API alternates contact shadows and actors. Replace land-style shadows
 # with a submerged local contact field; retain exact actor pixels and coordinates.
 for _,sprite,left,top in objects[1::2]:
  layer.alpha_composite(sprite,(left-x0,top-y0));cx=left+sprite.width*.5;cy=top+sprite.height*.84
  q=((xx+.5-cx)/(sprite.width*.75))**2+((yy+.5-cy)/(sprite.width*.29))**2
  n=.82+.18*C._noise(xx+.5,yy+.5,11,4301)
  bed=np.maximum(bed,np.exp(-q*2.2)*n*(q<2.2))
 original=np.asarray(image.convert('RGB'),float);water=np.clip(water_mask,0,1)
 if painted_waterline:
  # New aquatic source art already separates submerged anatomy and surface breaks.
  # Preserve its authored waterline instead of tinting the exposed back/claws uniformly.
  p=np.asarray(layer,float);a=(p[:,:,3]/255)*water
  rgb=original*(1-a[:,:,None])+p[:,:,:3]*a[:,:,None]
  return Image.fromarray(np.uint8(np.round(rgb).clip(0,255))).convert('RGBA')
 # A cool, mostly dark contact/bed cue, with no dry sand or bright land-colored disk.
 bed*=water;rgb=original*(1-bed[:,:,None]*.09)+np.array([29,85,107])*bed[:,:,None]*.09
 p=np.asarray(layer,float);a=(p[:,:,3]/255)*water
 # Wavelength-dependent absorption and a water veil give color depth; do not
 # simply lower the whole resource opacity and make its pearl disappear.
 shell=p[:,:,:3]*np.array([.70,.88,.99]);shell=shell*.8+original*.2
 rgb=rgb*(1-a[:,:,None])+shell*a[:,:,None]
 # Painted water highlights cross over the shells in world-registered positions.
 over=np.clip(surface_highlight*.65,0,.65)*a
 surface=original*.52+np.array([120,179,208])*.48
 rgb=rgb*(1-over[:,:,None])+surface*over[:,:,None]
 return Image.fromarray(np.uint8(np.round(rgb).clip(0,255))).convert('RGBA')
