"""Reusable world-coordinate painted river ribbons from visible source spans.

API: render_rivers((world_x, world_y, width, height), paths, materials, config=None)
Manifest ``river_digitization.paths`` dictionaries are accepted directly; their
``fractional_grid_nodes`` are multiplied by cell_size. Explicit ``world_nodes``
may be used for new maps. Every input span stays independent. Route labels never
create geometry, and observed endpoints use butt caps rather than fabricated
links through UI/forest occlusions. Sandbar branches use a thinner channel.

All masks and authored texture samples use world coordinates. Source-wide means
are fixed; no crop-dependent blur, normalization, rasterization or random state
is used. Independent chunks therefore match a whole render byte for byte.
The overlay changes no terrain IDs, coast topology or source annotations.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
import numpy as np
from PIL import Image
import coast_renderer as C


@dataclass(frozen=True)
class RiverConfig:
    cell_size: float = 128.0
    seed: int = 30
    main_width: float = 9.5  # full wet-channel width, in world px at a 128px cell
    branch_width: float = 5.7
    width_variation: float = 0.30
    bank_width: float = 3.4
    bank_opacity: float = 0.82
    antialias: float = 0.65
    smoothing_deviation: float = 3.0
    material_scale: float = 1.30
    material_overlap: float = 0.125


RIVER30_CONFIG = RiverConfig()


@dataclass
class RiverRender:
    overlay: Image.Image
    water_alpha: np.ndarray
    channel_mask: np.ndarray
    bank_alpha: np.ndarray
    distance: np.ndarray
    signed_channel_distance: np.ndarray
    nearest_path_index: np.ndarray
    path_ids: tuple[str, ...]

    @property
    def image(self):
        return self.overlay

    @property
    def owned_channel_mask(self):
        return self.channel_mask

    def root_exclusion_mask(self, clearance=0.0):
        """Exclude observed wet channels, optionally adding world-pixel clearance."""
        return self.signed_channel_distance <= float(clearance)


def _step(a, b, value):
    t = np.clip((value-a)/max(float(b-a), 1e-10), 0, 1)
    return t*t*(3-2*t)


def _noise(x, y, scale, seed):
    u,v=x/scale,y/scale
    ix,iy=np.floor(u).astype(np.int64),np.floor(v).astype(np.int64)
    fx,fy=u-ix,v-iy
    fx,fy=fx*fx*(3-2*fx),fy*fy*(3-2*fy)
    def at(a,b):
        n=(a*374761393+b*668265263+int(seed)*1442695)&0x7fffffff
        n=((n^(n>>13))*1274126177)&0x7fffffff
        return (n^(n>>16))/2147483647.0
    return ((at(ix,iy)*(1-fx)+at(ix+1,iy)*fx)*(1-fy)+
            (at(ix,iy+1)*(1-fx)+at(ix+1,iy+1)*fx)*fy)


def _grid(box):
    if len(box)!=4 or any(int(v)!=v for v in box):
        raise ValueError('box must be integer (world_x, world_y, width, height)')
    x0,y0,w,h=map(int,box)
    if w<=0 or h<=0:
        raise ValueError('box dimensions must be positive')
    y,x=np.mgrid[y0:y0+h,x0:x0+w]
    return x.astype(float)+.5,y.astype(float)+.5


def _paths(paths, config):
    """Validate without joining, resampling, reordering or altering source nodes."""
    if isinstance(paths, Mapping):
        paths=paths.get('paths', [])
    result=[]
    for i,path in enumerate(paths):
        if not isinstance(path,Mapping):
            raise ValueError('each path must contain fractional_grid_nodes or world_nodes')
        if 'world_nodes' in path:
            points=np.asarray(path['world_nodes'],dtype=float)
        else:
            points=np.asarray(path['fractional_grid_nodes'],dtype=float)*config.cell_size
        if points.ndim!=2 or points.shape[1]!=2 or len(points)<2 or not np.isfinite(points).all():
            raise ValueError(f'invalid river nodes for path {i}')
        # Duplicate nodes do not describe a segment, and removing exact repeats
        # does not move any observed point or join separately supplied paths.
        points=points[np.r_[True,np.any(np.diff(points,axis=0)!=0,axis=1)]]
        if len(points)<2:
            raise ValueError(f'path {i} has no nonzero segment')
        role=path.get('role','visible_main')
        default=config.branch_width if role=='visible_sandbar_branch' else config.main_width
        # Optional measured width overrides the default, with no arbitrary cap.
        width=float(path.get('width_world_px',default*config.cell_size/128.0))
        if not np.isfinite(width) or width<=0:
            raise ValueError('width_world_px must be positive and finite')
        result.append((str(path.get('path_id',f'path_{i}')),points,width,role))
    return result



def smooth_visible_path(points, max_deviation=3.0):
    """Round visible bends inside their source uncertainty, never extend a span.

    Local quadratic corner fillets replace sharp vertices; their control legs
    are at most 4*max_deviation, giving at most max_deviation displacement from
    the original two centerline segments. Source endpoints remain exact. Short
    adjacent legs are limited to 38% so separate fillets cannot overlap.
    """
    points=np.asarray(points,dtype=float)
    if max_deviation<=0 or len(points)<3:
        return points.copy()
    output=[points[0]]
    for a,b,c in zip(points[:-2],points[1:-1],points[2:]):
        ab,bc=b-a,c-b
        la,lb=np.linalg.norm(ab),np.linalg.norm(bc)
        cut=min(.38*la,.38*lb,4*max_deviation)
        if cut<1e-8:
            output.append(b);continue
        before=b-ab/la*cut;after=b+bc/lb*cut
        for t in (0.,1/3,2/3,1.):
            output.append((1-t)**2*before+2*(1-t)*t*b+t*t*after)
    output.append(points[-1])
    result=np.asarray(output)
    return result[np.r_[True,np.any(np.diff(result,axis=0)!=0,axis=1)]]

def _path_distance(points,x,y):
    d2=np.full(x.shape,np.inf);cx=x.copy();cy=y.copy()
    index=np.full(x.shape,-1,dtype=np.int32);parameter=np.zeros(x.shape)
    for k,(a,b) in enumerate(zip(points[:-1],points[1:])):
        delta=b-a;l2=float(np.dot(delta,delta))
        t=np.clip(((x-a[0])*delta[0]+(y-a[1])*delta[1])/l2,0,1)
        px,py=a[0]+delta[0]*t,a[1]+delta[1]*t
        candidate=(x-px)**2+(y-py)**2
        nearer=candidate<d2
        d2[nearer]=candidate[nearer];cx[nearer]=px[nearer];cy[nearer]=py[nearer]
        index[nearer]=k;parameter[nearer]=t[nearer]
    # Cap only the nearest endpoint; other bends in the same path remain valid.
    # A source-hidden continuation gets no invented round-ended extension.
    start=(points[1]-points[0]);start=start/np.linalg.norm(start)
    end=(points[-1]-points[-2]);end=end/np.linalg.norm(end)
    cap=np.full(x.shape,-np.inf)
    at_start=(index==0)&(parameter==0)
    at_end=(index==len(points)-2)&(parameter==1)
    cap[at_start]=(-(x-points[0,0])*start[0]-(y-points[0,1])*start[1])[at_start]
    cap[at_end]=((x-points[-1,0])*end[0]+(y-points[-1,1])*end[1])[at_end]
    return np.sqrt(d2),cx,cy,cap


def render_rivers(box, paths, materials, config=None) -> RiverRender:
    """Return an RGBA overlay and precise world-space channel/bank ownership.

    ``distance`` is the true Euclidean distance to the nearest rendered visible
    polyline (bounded corner interpolation), without an arbitrary narrow-band cap. ``signed_channel_distance``
    is negative inside a wet ribbon and positive outside; its endpoint clipping
    respects observed span termini. ``bank_alpha`` contains only exposed bank
    contribution, excluding the water. Missing spans are never inferred.
    """
    config=config or RIVER30_CONFIG
    if config.cell_size<=0 or config.main_width<=0 or config.branch_width<=0:
        raise ValueError('cell size and channel widths must be positive')
    if not 0<=config.width_variation<1 or config.bank_width<0 or not 0<=config.bank_opacity<=1:
        raise ValueError('invalid river width variation or bank settings')
    if config.smoothing_deviation<0:
        raise ValueError('smoothing_deviation must be nonnegative')
    if config.antialias<=0 or config.material_scale<=0:
        raise ValueError('antialias and material_scale must be positive')
    missing=[k for k in ('meadow','shore','deep_water','shallow_water') if k not in materials]
    if missing:
        raise ValueError('missing material arrays: '+', '.join(missing))
    x,y=_grid(box);unit=config.cell_size/128.0
    observed=_paths(paths,config)
    distance=np.full(x.shape,np.inf)
    signed=np.full(x.shape,np.inf);bank_signed=np.full(x.shape,np.inf)
    nearest=np.full(x.shape,-1,dtype=np.int32)
    for i,(_,points,base_width,_) in enumerate(observed):
        points=smooth_visible_path(points,config.smoothing_deviation*unit)
        d,cx,cy,cap=_path_distance(points,x,y)
        distance=np.minimum(distance,d)
        variation=.72*_noise(cx,cy,49*unit,config.seed+13)+.28*_noise(cx,cy,17*unit,config.seed+31)
        radius=.5*base_width*(1+config.width_variation*(2*variation-1))
        s=np.maximum(d-radius,cap)
        wet_bank=config.bank_width*unit*(.62+.76*_noise(cx,cy,13*unit,config.seed+59))
        bs=np.maximum(d-radius-wet_bank,cap)
        nearer=s<signed
        signed[nearer]=s[nearer];nearest[nearer]=i
        bank_signed=np.minimum(bank_signed,bs)
    aa=config.antialias*unit
    water=1-_step(-aa,aa,signed)
    bank=(1-_step(-aa,aa,bank_signed))*(1-water)*config.bank_opacity
    # Fine source-texture gaps vary damp bank opacity. This is not a pale stroke.
    bank*=.62+.38*_noise(x,y,4.8*unit,config.seed+101)
    owned=signed<=0

    def sample(name,factor=1.,offset=(0.,0.)):
        return C.sample_material(materials[name],x,y,config.material_scale*factor/unit,
                                 offset,config.material_overlap)
    deep=sample('deep_water',.93)
    shallow_source=C._calibrated_shallow(materials['shallow_water'])
    shallow=C.sample_material(shallow_source,x,y,config.material_scale*1.08/unit,
                              (37,101),config.material_overlap)
    meadow=sample('meadow',1.7)
    shore=sample('shore',1.8,(71,29))
    means={k:np.asarray(materials[k],dtype=float)[...,:3].mean((0,1))
           for k in ('deep_water','shallow_water','meadow')}
    # The same authored sea/water materials, quieted and slightly soil-tinted.
    # No white center stroke, turquoise rim, synthetic pebble or painted prop.
    means['shallow_water']=shallow_source.mean((0,1))
    water_mean=means['deep_water']*.43+means['shallow_water']*.47+means['meadow']*.10
    water_rgb=(water_mean+(deep-means['deep_water'])*.24+
               (shallow-means['shallow_water'])*.45)
    if 'forest_floor' in materials:
        bank_rgb=sample('forest_floor',1.8,(71,29))*.50+shore*.20+deep*.08
    else:
        bank_rgb=meadow*.50+shore*.16+deep*.12
    alpha=water+bank
    premultiplied=water_rgb*water[...,None]+bank_rgb*bank[...,None]
    rgb=np.divide(premultiplied,alpha[...,None],out=np.zeros_like(premultiplied),where=alpha[...,None]>0)
    rgba=np.dstack((np.clip(np.rint(rgb),0,255).astype(np.uint8),
                    np.clip(np.rint(alpha*255),0,255).astype(np.uint8)))
    return RiverRender(Image.fromarray(rgba,'RGBA'),water,owned,bank,distance,signed,
                       nearest,tuple(p[0] for p in observed))
