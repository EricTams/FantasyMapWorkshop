"""Continuous painted-material ground field; no cell-dependent color normalization."""
import numpy as np
from scipy.ndimage import gaussian_filter
import coast_renderer as C

def prepare(source, sampler):
 a=np.asarray(source,float);mean=a.mean((0,1));y,x=np.mgrid[:a.shape[0],:a.shape[1]]
 # Detail must exclude baked broad illumination before4x minification.
 high=np.clip(a-gaussian_filter(a,(20,20,0),mode='wrap')+mean,0,255)
 fine=mean+(sampler(high,x,y,4)-mean)*.38
 fine += mean-fine.mean((0,1))
 broad=gaussian_filter(a,(32,32,0),mode='wrap')
 return {'fine':fine,'broad':broad,'mean':mean}

def sample(field,x,y,sampler):
 mean=field['mean']
 fine=C.sample_material(field['fine'],x,y,scale=1.3,overlap=.125)
 # Authored broad color sampled over many cells, on two non-grid-aligned axes.
 u=.8571673*x+.5150381*y+183;v=-.5150381*x+.8571673*y-74
 p=.3907311*x-.9205049*y+317;q=.9205049*x+.3907311*y+61
 broad1=sampler(field['broad'],u,v,.45)-mean;broad2=sampler(field['broad'],p,q,.21)-mean
 return np.clip(fine+.65*broad1+.35*broad2,0,255)
