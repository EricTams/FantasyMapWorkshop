"""Reusable material/neighbor-mask/upright-sprite renderer. No scene illustration is sliced into tiles."""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import map_coordinates,gaussian_filter,distance_transform_edt
import coast_renderer as C
ROOT=Path(__file__).resolve().parent;T=128
FONT='DejaVuSans.ttf';BOLD='DejaVuSans-Bold.ttf'
def get_font(name,size):
 try:return ImageFont.truetype(name,size)
 except OSError:return ImageFont.load_default(size=size)
def step(a,b,x):
 z=np.clip((x-a)/(b-a),0,1);return z*z*(3-2*z)
MIP_CACHE={}
def sample(a,x,y,scale=1,offset=(0,0)):
 # Proper trilinear mipmapping prevents foliage/grass aliasing when materials are minified.
 lod=max(0,math.log2(max(scale,1)));low=int(math.floor(lod));high=int(math.ceil(lod));blend=lod-low
 def at(level):
  factor=2**level;key=(id(a),level)
  if key not in MIP_CACHE or MIP_CACHE[key][0] is not a:
   MIP_CACHE[key]=(a,np.asarray(Image.fromarray(np.uint8(np.round(a).clip(0,255))).resize((max(1,a.shape[1]//factor),max(1,a.shape[0]//factor)),Image.Resampling.LANCZOS),float) if level else a)
  m=MIP_CACHE[key][1]
  return np.stack([map_coordinates(m[:,:,k],[np.mod((y*scale+offset[1])/factor,m.shape[0]),np.mod((x*scale+offset[0])/factor,m.shape[1])],order=1,mode='grid-wrap',prefilter=False) for k in range(3)],axis=2)
 v=at(low)
 return v if high==low else v*(1-blend)+at(high)*blend
def hash32(x,y,z=0):
 v=(int(x)*374761393+int(y)*668265263+z*1442695041+641029)&0xffffffff;v=((v^(v>>13))*1274126177)&0xffffffff;return (v^(v>>16))&0xffffffff
class KitScene:
 def __init__(self,scene,trace,coverage,old_asset_root=None):
  self.s=scene;self.coverage=coverage;self.old_asset_root=Path(old_asset_root) if old_asset_root is not None else ROOT/'assets/resources'
  self.ids=np.array([[{'sand':0,'grass':1,'water':2,'plains':3,'tundra':4,'snow':5,'unknown':255}[v] for v in row] for row in scene['terrain_rows']],np.uint8);self.fD=np.array([[v=='D' for v in row] for row in scene['forest_rows']]);self.fP=np.array([[v=='P' for v in row] for row in scene['forest_rows']]);self.fJ=np.array([[v=='J' for v in row] for row in scene['forest_rows']]);self.f=self.fD|self.fP|self.fJ;self.H,self.W=self.ids.shape;self.PW=self.W*T;self.PH=self.H*T
  from relief_renderer import ReliefLayer
  self.hill_cells=scene.get('hill_cells',[]);self.mountain_cells=scene.get('mountain_cells',[]);self.hills=ReliefLayer(self.hill_cells,self.mountain_cells,(self.H,self.W),terrain_ids=self.ids) if self.hill_cells or self.mountain_cells else None;self.hraw=np.zeros((self.PH,self.PW),bool) if self.hills is None else np.repeat(np.repeat(self.hills.mask,T,0),T,1)
  self.mats=C.load_materials(ROOT/'assets/materials')
  import ground_field as GF
  self.ground_field=GF.prepare(self.mats['meadow'],sample)
  # Correct excessive source grain without inventing painted content: broad source field + quiet high-frequency authored detail.
  a=self.mats['meadow'];y,x=np.mgrid[:512,:512];broad=gaussian_filter(a,sigma=(10,10,0),mode='wrap');fine=sample(a,x,y,4)
  self.mats['meadow']=np.clip(broad+(fine-a.mean((0,1)))*.38,0,255)
  self.river=None;self.river_edge_records=None
  river_paths=scene.get('river_digitization',{}).get('paths',[])
  if scene.get('river_edges'):
   if river_paths:raise ValueError('Choose authored shared-edge topology or source digitization, not both')
   from river_edges import compile_edges
   river_paths,self.river_edge_records=compile_edges(scene['river_edges'],(self.H,self.W),T)
  if river_paths:
   import river_renderer as RR
   self.river=RR.render_rivers((0,0,self.PW,self.PH),river_paths,self.mats,RR.RiverConfig(main_width=9.0,bank_width=2.2,smoothing_deviation=2.4) if self.river_edge_records else None)
  self.poly,self.evidence=C.load_trace(trace);self.fraw=np.repeat(np.repeat(self.f,T,0),T,1)
  fields=C.polygon_fields(self.poly,(0,0,self.PW,self.PH),self.evidence);self.fvalid=self.fraw&fields.land_mask
  if self.river_edge_records and self.river is not None:
   # Coast outlet keeps water contact without painting banks through the open sea.
   retain=step(-3,2,fields.signed_distance);ro=np.array(self.river.overlay);ro[:,:,3]=np.round(ro[:,:,3]*retain).astype('uint8');self.river.overlay=Image.fromarray(ro);self.river.water_alpha*=retain;self.river.bank_alpha*=retain;self.river.channel_mask &= retain>.1
  if self.river is not None:self.fvalid &= ~self.river.channel_mask
  self.fdist=distance_transform_edt(self.fvalid)-distance_transform_edt(~self.fvalid)
  from vegetation_clearance import build as build_clearance
  self.clearance_mask,self.clearance_distance,self.clearance_records=build_clearance((self.PH,self.PW),self.fvalid,self.coverage['rendered_features'],self.hill_cells,T)
  self.fvalid &= self.clearance_distance>=5
  # A forest region owns its roots, while an irregular narrow perimeter carries the canopy silhouette.
  # All core pixels >=32 world px inside woodland retain the prior exact material masks.
  ey,ex=np.mgrid[:self.PH,:self.PW]
  edge_warp=(C._noise(ex+.5,ey+.5,29,2801)-.5)*10+(C._noise(ex+.5,ey+.5,13,2802)-.5)*3
  self.floor_mask=step(0,13,self.fdist+edge_warp)
  self.interior_mask=step(9,24,self.fdist+edge_warp)
  core=self.fdist>=32
  self.floor_mask[core]=1;self.interior_mask[core]=1
  keep=step(-1,4,self.clearance_distance);self.floor_mask*=keep;self.interior_mask*=keep
  self.coast=C.render_coast((0,0,self.PW,self.PH),self.poly,self.mats,edge_evidence=self.evidence,forest_proximity=C.WorldMask(gaussian_filter(self.fvalid.astype(float),12)),config=C.COAST27_CONFIG)
  water_rgb=np.asarray(self.coast.image,float);water_fine=water_rgb-gaussian_filter(water_rgb,sigma=(1.5,1.5,0),mode='nearest');self.water_surface_highlight=np.clip((water_fine.mean(2)-1.0)/21.0,0,1)
  if self.hills is not None:self.hills.anchors=[(hy,hx,hi) for hy,hx,hi in self.hills.anchors if self.coast.land_mask[int(hy),int(hx)] and (self.river is None or not self.river.channel_mask[int(hy),int(hx)])]
  y,x=np.mgrid[:self.PH,:self.PW];self.worldbase=np.asarray(self.coast.image,float);idpix=self.ids[y//T,x//T]
  # Keep coast/river materials fixed; replace only their dry-ground contribution.
  old_meadow=C.sample_material(self.mats['meadow'],x+.5,y+.5,scale=1.3,overlap=.125)
  meadow=GF.sample(self.ground_field,x+.5,y+.5,sample)
  dry=self.coast.land_alpha*(1-self.coast.sand_alpha)*(1-self.coast.bank_alpha)
  self.worldbase+=(meadow-old_meadow)*dry[:,:,None]
  for code,target in [(3,[181,165,104]),(0,[204,184,141])]:
   w=step(.3,.7,gaussian_filter((idpix==code).astype(float),5))*self.coast.land_alpha*(1-self.coast.sand_alpha)*(1-self.coast.bank_alpha)
   tinted=np.array(target)+(meadow-self.ground_field['mean'])*.74
   self.worldbase+=(tinted-meadow)*w[:,:,None]
  from cold_renderer import cold_ground,IceField
  self.worldbase,self.cold_weights=cold_ground(self.worldbase,self.ids,self.coast.land_alpha,x,y,sample,T)
  self.ice=IceField(scene.get('ice_cells',[]),self.ids,self.coast.land_alpha,(self.H,self.W),T) if scene.get('ice_cells') else None
  if self.ice is not None:self.worldbase=self.ice.ground(self.worldbase)
  unknown=idpix==255;hatch=((x+y)%18<2);neutral=np.zeros_like(self.worldbase)+[79,87,83];neutral[hatch]=[94,101,97]
  self.worldbase[unknown&~self.fraw&~self.hraw]=neutral[unknown&~self.fraw&~self.hraw]
  floor=sample(self.mats['forest_floor'],x,y,2.6)
  # Unknown base IDs remain unknown. Their generic wooded substrate uses the same
  # organic perimeter blend, rather than painting a full rectangular cell beneath it.
  generic_floor=floor*self.floor_mask[:,:,None]+self.worldbase*(1-self.floor_mask[:,:,None])
  self.worldbase[unknown&self.fraw]=generic_floor[unknown&self.fraw]
  self.worldbase=np.clip(self.worldbase,0,255)
  self.pine_material=None;self.pine_trees=[];self.pine_meta=[]
  if self.fP.any():
   pm=json.loads((ROOT/'assets/pine/pine_manifest.json').read_text());self.pine_material=np.asarray(Image.open(ROOT/'assets/pine'/pm['interior_material']).convert('RGB'),float);self.pine_trees=[Image.open(ROOT/'assets/pine'/q['file']).convert('RGBA') for q in pm['sprites']];self.pine_meta=pm['sprites'];self.pine_config=pm
  pf=np.repeat(np.repeat(self.fP,T,0),T,1).astype(float);self.pine_weight=gaussian_filter(pf,5)/np.maximum(gaussian_filter(self.fraw.astype(float),5),1e-8)
  self.jungle_material=None;self.jungle_sprites=[];self.jungle_meta=[]
  if self.fJ.any():
   jm=json.loads((ROOT/'assets/jungle/jungle_manifest.json').read_text());self.jungle_config=jm;self.jungle_material=np.asarray(Image.open(ROOT/'assets/jungle'/jm['interior_material']).convert('RGB'),float);self.jungle_sprites=[Image.open(ROOT/'assets/jungle'/q['file']).convert('RGBA') for q in jm['sprites']];self.jungle_meta=jm['sprites']
  jf=np.repeat(np.repeat(self.fJ,T,0),T,1).astype(float);self.jungle_weight=gaussian_filter(jf,5)/np.maximum(gaussian_filter(self.fraw.astype(float),5),1e-8)
  self.sprite_meta=json.loads((ROOT/'kit_manifest.json').read_text())['sprites'];self.trees=[Image.open(ROOT/'assets/sprites'/f'broadleaf_edge_{i}.png').convert('RGBA') for i in range(4)];self.sites={n:Image.open(ROOT/'assets/sprites'/(n+'.png')).convert('RGBA') for n in ['city_compact','corn_field','cottage_plot','mine_site']}
  self.anchors=[];candidates=[]
  for gy in range(math.ceil(self.PH/17)):
   for gx in range(math.ceil(self.PW/17)):
    bx=gx*17+(hash32(gx,gy,1)%1700)/100;by=gy*17+(hash32(gx,gy,2)%1700)/100;ix=min(self.PW-1,int(bx));iy=min(self.PH-1,int(by))
    if bx>=self.PW or by>=self.PH:continue
    if self.fvalid[iy,ix] and 3<=self.fdist[iy,ix]<=22 and self.coast.signed_distance[iy,ix]>=4:candidates.append((hash32(gx,gy,3),bx,by,hash32(gx,gy,4)%4))
  for _,bx,by,idx in sorted(candidates):
   if all((bx-x)**2+(by-y)**2>=24**2 for y,x,_ in self.anchors):self.anchors.append((by,bx,idx))
  # Add only exterior roots. Existing27 roots, core density and material sampling are unchanged.
  self.retained_edge_anchor_count=len(self.anchors);edge_candidates=[]
  for gy in range(math.ceil(self.PH/10)):
   for gx in range(math.ceil(self.PW/10)):
    bx=gx*10+(hash32(gx,gy,2801)%1000)/100;by=gy*10+(hash32(gx,gy,2802)%1000)/100;ix=min(self.PW-1,int(bx));iy=min(self.PH-1,int(by))
    if bx>=self.PW or by>=self.PH:continue
    if self.fvalid[iy,ix] and 3<=self.fdist[iy,ix]<=18 and self.coast.signed_distance[iy,ix]>=4:edge_candidates.append((hash32(gx,gy,2803),bx,by,hash32(gx,gy,2804)%4))
  for _,bx,by,idx in sorted(edge_candidates):
   if all((bx-x)**2+(by-y)**2>=15.5**2 for y,x,_ in self.anchors):self.anchors.append((by,bx,idx))
  if self.clearance_mask.any():
   inner=[]
   for gy in range(math.ceil(self.PH/10)):
    for gx in range(math.ceil(self.PW/10)):
     bx=gx*10+(hash32(gx,gy,4001)%1000)/100;by=gy*10+(hash32(gx,gy,4002)%1000)/100;ix=min(self.PW-1,int(bx));iy=min(self.PH-1,int(by))
     if bx<self.PW and by<self.PH and self.fvalid[iy,ix] and 5<=self.clearance_distance[iy,ix]<=14:inner.append((hash32(gx,gy,4003),bx,by,hash32(gx,gy,4004)%4))
   for _,bx,by,idx in sorted(inner):
    if all((bx-ax)**2+(by-ay)**2>=22**2 for ay,ax,_ in self.anchors):self.anchors.append((by,bx,idx))
  if self.fJ.any():
   kept=[];jkept=[]
   for by,bx,idx in self.anchors:
    if not self.fJ[int(by/T),int(bx/T)]:kept.append((by,bx,idx));continue
    if all((bx-kx)**2+(by-ky)**2>=29**2 for ky,kx,_ in jkept):jkept.append((by,bx,idx))
   self.anchors=kept+jkept
  from vineyard_field import VineyardField
  wine_cells=[q['cell'] for q in self.coverage['rendered_features'] if q['asset']=='grapes_resource.png'];press_cells=[q['cell'] for q in self.coverage['rendered_features'] if q['asset']=='vineyard_press.png'];self.vineyard=VineyardField(wine_cells,press_cells,(self.H,self.W),self.coast.land_mask,self.river.channel_mask if self.river is not None else None) if wine_cells else None
  self.anchors.sort();self.ys=np.array(scene['geometry']['row_boundary_y'],float);self.xs=np.array(scene['geometry']['column_boundary_x_by_row'],float);self.x0,self.y0,self.x1,self.y1=scene['crop_bounds_px'];self.CW=self.x1-self.x0;self.CH=self.y1-self.y0;self.avgW=np.mean(np.diff(self.xs,axis=1));self.wood_scale=4.2/(self.avgW/128)
 def forward(self,u,v):
  r=int(np.clip(np.floor(v),0,self.H-1));q=v-r;c=int(np.clip(np.floor(u),0,self.W-1));t=u-c;left=self.xs[r,c]*(1-q)+self.xs[r+1,c]*q;right=self.xs[r,c+1]*(1-q)+self.xs[r+1,c+1]*q
  return left*(1-t)+right*t-self.x0,self.ys[r]*(1-q)+self.ys[r+1]*q-self.y0,right-left,self.ys[r+1]-self.ys[r]
 def inverse(self,X,Y):
  rf=np.interp(Y+self.y0,self.ys,np.arange(self.H+1));r=np.clip(np.floor(rf).astype(int),0,self.H-1);q=rf-r;bounds=np.stack([self.xs[r,c]*(1-q)+self.xs[r+1,c]*q for c in range(self.W+1)]);c=np.clip(np.sum(X[None]+self.x0>=bounds,axis=0)-1,0,self.W-1);left=np.take_along_axis(bounds,c[None],axis=0)[0];right=np.take_along_axis(bounds,(c+1)[None],axis=0)[0];u=c+(X+self.x0-left)/(right-left);valid=(Y+self.y0>=self.ys[0])&(Y+self.y0<self.ys[-1])&(u>=0)&(u<self.W)
  return u*T,rf*T,valid
 def object_instances(self):
  objects=self.hills.objects(self.forward,True,named=True) if self.hills else []
  if self.ice is not None:objects.extend(self.ice.objects(self.forward,T,named=True))
  for by,bx,idx in self.anchors:
   px,py,cw,ch=self.forward(bx/T,by/T);is_pine=bool(self.fP[min(self.H-1,int(by/T)),min(self.W-1,int(bx/T))]);is_jungle=bool(self.fJ[min(self.H-1,int(by/T)),min(self.W-1,int(bx/T))]);tr=self.jungle_sprites[idx%len(self.jungle_sprites)] if is_jungle else (self.pine_trees[idx%len(self.pine_trees)] if is_pine and self.pine_trees else self.trees[idx]);meta=self.jungle_meta[idx%len(self.jungle_meta)] if is_jungle else (self.pine_meta[idx%len(self.pine_meta)] if is_pine and self.pine_meta else self.sprite_meta[idx]);scale=cw/128*.92;size=(max(1,round(tr.width*scale)),max(1,round(tr.height*scale)));sprite=tr.resize(size,Image.Resampling.LANCZOS);anchor=meta['root_anchor'];objects.append((py,sprite,round(px-anchor[0]*scale),round(py-anchor[1]*scale),Path(meta['file']).stem if is_jungle else meta.get('name',f'broadleaf_edge_{idx}')))
  mapping={'city_compact.png':'city_compact','corn_field.png':'corn_field','cottage_plot.png':'cottage_plot','legacy_mine.png':'mine_site'}
  for feat in self.coverage['rendered_features']:
   row,col=feat['cell']
   if feat['asset']=='grapes_resource.png' and self.vineyard is not None:continue
   if feat['asset'] in ['grapes_resource.png','vineyard_press.png']:
    from vineyard_renderer import objects as vineyard_objects
    objects.extend(vineyard_objects('grapes' if feat['asset']=='grapes_resource.png' else 'press',row,col,self.forward,(row+col)%2,named=True));continue
   if feat['asset'].startswith('botanical_'):
    from botanical_renderer import objects as botanical_objects
    objects.extend(botanical_objects(feat['asset'][10:-4],row,col,self.forward,named=True));continue
   if feat['asset'].startswith('mineral_'):
    from mineral_renderer import objects as mineral_objects
    objects.extend(mineral_objects(feat['asset'][8:-4],row,col,self.forward,named=True));continue
   if feat['asset'].startswith('wildlife_'):
    from wildlife_renderer import objects as wildlife_objects,M as wildlife_manifest
    kind=feat['asset'][9:-4]
    if not wildlife_manifest['groups'][kind].get('water_resource'):
     objects.extend(wildlife_objects(kind,row,col,self.forward,(row+col)%2,named=True))
    continue
   if feat['asset']=='scarlet_pepper_bushes.png':
    from pepper_renderer import objects as pepper_objects
    objects.extend(pepper_objects(row,col,self.forward,(row+col)%2,named=True));continue
   if feat['asset']=='deer_herd.png':
    from fantasy_renderer import objects as fantasy_objects
    objects.extend(fantasy_objects('deer',row,col,self.forward,(row+col)%2,named=True));continue
   if feat.get('kind')=='fantasy_spice_proposal' and feat['asset']=='crimson_spice':
    from fantasy_renderer import objects as fantasy_objects
    objects.extend(fantasy_objects('spice',row,col,self.forward,int(feat.get('variant',0)),named=True));continue
   row,col=feat['cell'];px,py,cw,ch=self.forward(col+.5,row+.5);name=mapping.get(feat['asset'])
   if name=='mine_site' and [row,col] in self.hill_cells:py-=ch*.07
   if name:
    sprite=self.sites[name];sc=cw/128;sprite=sprite.resize((max(1,round(sprite.width*sc)),max(1,round(sprite.height*sc))),Image.Resampling.LANCZOS)
   else:
    asset=ROOT/'assets/resources'/feat['asset'];asset=asset if asset.exists() else self.old_asset_root/feat['asset'];sprite=Image.open(asset).convert('RGBA');sprite=sprite.resize((max(1,round(cw)),max(1,round(ch))),Image.Resampling.LANCZOS)
   objects.append((py+3,sprite,round(px-sprite.width/2),round(py-sprite.height/2),name or Path(feat['asset']).stem))
  return sorted(objects,key=lambda q:q[0])
 def water_resource_instances(self):
  from wildlife_renderer import objects as wildlife_objects,M as wildlife_manifest
  resources=[]
  for feat in self.coverage['rendered_features']:
   if not feat['asset'].startswith('wildlife_'):continue
   kind=feat['asset'][9:-4]
   if not wildlife_manifest['groups'][kind].get('water_resource'):continue
   row,col=feat['cell'];resources.append({'kind':kind,'cell':[row,col],'objects':wildlife_objects(kind,row,col,self.forward,(row+col)%2),'painted_waterline':wildlife_manifest['groups'][kind].get('painted_waterline',False)})
  return resources
 def resource_metadata(self):
  registry=json.loads((ROOT/'resource_semantics.json').read_text());aliases=registry['asset_categories'];out=[]
  from wildlife_renderer import M as wildlife_manifest
  for feat in self.coverage['rendered_features']:
   if feat.get('kind')!='resource' and not feat['asset'].startswith('wildlife_'):continue
   asset=feat['asset'];group=asset[9:-4] if asset.startswith('wildlife_') else None
   category=wildlife_manifest['groups'][group]['source_category'] if group else asset[8:-4] if asset.startswith('mineral_') else asset[10:-4] if asset.startswith('botanical_') else feat.get('resource_id',feat.get('source_category',aliases.get(asset,'unknown')))
   water=bool(group and wildlife_manifest['groups'][group].get('water_resource'))
   out.append({'cell':feat['cell'],'source_category':category,'semantic_resource_code':registry['categories'].get(category,0),'asset_identifier':asset,'runtime_group':group or '', 'render_pass':('baked_painted_waterline51' if wildlife_manifest['groups'][group].get('painted_waterline') else 'baked_water_treatment43') if water else 'baked_vineyard_field46' if asset=='grapes_resource.png' and self.vineyard is not None else 'upright_object_pass','implementation_status':'partial; provisional physical water contact' if category in ('clams','crab') else 'prototype; consult mapping registry'})
  return out
 def improvement_metadata(self):
  registry=json.loads((ROOT/'improvement_semantics.json').read_text());out=[]
  for feat in self.coverage['rendered_features']:
   if feat.get('kind')!='improvement':continue
   category=feat.get('source_category',registry['asset_categories'].get(feat['asset'],'unknown'))
   out.append({'cell':feat['cell'],'source_category':category,'semantic_improvement_code':registry['categories'].get(category,0),'asset_identifier':feat['asset'],'render_pass':'upright_object_pass','independent_of_resource_id':True})
  return out
 def render(self,box=None,include_objects=True,return_objects=False):
  if box is None:box=(0,0,self.CW,self.CH)
  x0,y0,w,h=box;y,x=np.mgrid[y0:y0+h,x0:x0+w];wx,wy,valid=self.inverse(x+.5,y+.5)
  rgb=np.stack([map_coordinates(self.worldbase[:,:,k],[wy-.5,wx-.5],order=1,mode='nearest',prefilter=False) for k in range(3)],axis=2)
  if self.hills is not None:rgb=np.asarray(self.hills.draw(Image.fromarray(np.uint8(np.round(rgb).clip(0,255))),self.forward,box).convert('RGB'),float)
  f=map_coordinates(self.floor_mask,[wy-.5,wx-.5],order=1,mode='nearest',prefilter=False);inside=map_coordinates(self.interior_mask,[wy-.5,wx-.5],order=1,mode='nearest',prefilter=False);land=map_coordinates(self.coast.land_alpha,[wy-.5,wx-.5],order=1,mode='nearest',prefilter=False)
  floor=sample(self.mats['forest_floor'],wx,wy,2.6);rgb=rgb*(1-f[:,:,None]*land[:,:,None])+(floor*.77+rgb*.23)*f[:,:,None]*land[:,:,None]
  # Tree-containing material is sampled in projected screen space so upright trunks are NOT ground-squashed.
  woods=sample(self.mats['woodland'],x+.5,y+.5,self.wood_scale,(43,79))
  if self.pine_material is not None:
   pw=map_coordinates(self.pine_weight,[wy-.5,wx-.5],order=1,mode='nearest',prefilter=False);pine_scale=self.pine_config.get('screen_sampling_scale_at128',4.2)/(self.avgW/128);pine=sample(self.pine_material,x+.5,y+.5,pine_scale,(37,113));woods=woods*(1-pw[:,:,None])+pine*pw[:,:,None]
  if self.jungle_material is not None:
   jw=map_coordinates(self.jungle_weight,[wy-.5,wx-.5],order=1,mode='nearest',prefilter=False);jscale=self.jungle_config['screen_sampling_scale_at128']/(self.avgW/128);jmat=sample(self.jungle_material,x+.5,y+.5,jscale,(67,131));woods=woods*(1-jw[:,:,None])+jmat*jw[:,:,None]
  a=inside*land;rgb=rgb*(1-a[:,:,None])+woods*a[:,:,None]
  if self.river is not None:
   ro=np.asarray(self.river.overlay,float);ras=ro[:,:,3]/255;ra=map_coordinates(ras,[wy-.5,wx-.5],order=1,mode='nearest',prefilter=False);rr=np.stack([map_coordinates(ro[:,:,k]*ras,[wy-.5,wx-.5],order=1,mode='nearest',prefilter=False) for k in range(3)],axis=2);rgb=rgb*(1-ra[:,:,None])+rr
  if self.vineyard is not None:rgb=self.vineyard.composite(rgb,wx,wy)
  im=Image.fromarray(np.uint8(np.round(rgb).clip(0,255))).convert('RGBA')
  # Water resources are a context-dependent ground pass, retained when objects are omitted.
  for resource in self.water_resource_instances():
   from submerged_resources import composite as composite_submerged
   row,col=resource['cell'];highlights=map_coordinates(self.water_surface_highlight,[wy-.5,wx-.5],order=1,mode='nearest',prefilter=False);owned=(wx>=col*T)&(wx<(col+1)*T)&(wy>=row*T)&(wy<(row+1)*T)
   im=composite_submerged(im,resource['objects'],box,(1-land)*owned,highlights,painted_waterline=resource.get('painted_waterline',False))
  objects=self.object_instances()
  if return_objects:return objects
  for _,sprite,l,t,_ in objects if include_objects else []:
   if l+sprite.width>x0 and l<x0+w and t+sprite.height>y0 and t<y0+h:im.alpha_composite(sprite,(l-x0,t-y0))
  rgb=np.asarray(im.convert('RGB')).copy();rgb[~valid]=[30,43,35];return Image.fromarray(rgb)
 def grid(self,im):
  im=im.copy();d=ImageDraw.Draw(im);f=get_font(BOLD,10)
  def segment(a,b):
   length=math.dist(a,b)
   for k in np.arange(0,length,11):
    p=np.array(a)+(np.array(b)-a)*(k/length);q=np.array(a)+(np.array(b)-a)*min(1,(k+6)/length);d.line((tuple(p),tuple(q)),fill=(18,31,22),width=3);d.line((tuple(p),tuple(q)),fill=(234,230,192),width=1)
  for r in range(self.H+1):
   for c in range(self.W):segment((self.xs[r,c]-self.x0,self.ys[r]-self.y0),(self.xs[r,c+1]-self.x0,self.ys[r]-self.y0))
  for c in range(self.W+1):
   for r in range(self.H):segment((self.xs[r,c]-self.x0,self.ys[r]-self.y0),(self.xs[r+1,c]-self.x0,self.ys[r+1]-self.y0))
  for r in range(self.H):
   for c in range(self.W):
    x,y,_,_=self.forward(c+.07,r+.07);label=f'{r+1}{chr(65+c)}'+(' H'+('?' if self.ids[r,c]==255 else '') if [r,c] in self.hill_cells else (' M'+('?' if self.ids[r,c]==255 else '') if [r,c] in self.mountain_cells else ''));d.text((x,y),label,font=f,fill=(245,241,210),stroke_width=1,stroke_fill=(20,33,23))
  return im
 def annotate_river_evidence(self,im):
  from source_occlusions import pairs
  points=[]
  for a,b in pairs(self.s):
   u=(a[-1][0]+b[0][0])/2;v=(a[-1][1]+b[0][1])/2;x,y,_,_=self.forward(u,v)
   if 0<=x<self.CW and 0<=y<self.CH and all((x-px)**2+(y-py)**2>57**2 for px,py in points):points.append((x,y))
  if not points:return im
  im=im.copy();d=ImageDraw.Draw(im);font=get_font(FONT,8)
  for x,y in points:
   tx=max(2,min(self.CW-58,x-27));ty=max(2,min(self.CH-13,y+5));d.rectangle((tx-2,ty-1,tx+58,ty+11),fill=(34,45,37));d.text((tx,ty),'Source hidden',font=font,fill=(235,216,172));d.line((x,y,tx+27,ty),fill=(235,216,172),width=1)
  return im
 def qa(self):
  whole=self.render();stitch=Image.new('RGB',whole.size)
  for y in range(0,self.CH,93):
   for x in range(0,self.CW,117):stitch.paste(self.render((x,y,min(117,self.CW-x),min(93,self.CH-y))),(x,y))
  diff=int(np.abs(np.asarray(whole).astype(int)-np.asarray(stitch).astype(int)).max());roots_valid=all(self.fvalid[int(y),int(x)] and self.coast.signed_distance[int(y),int(x)]>=4 for y,x,_ in self.anchors)
  centers=[]
  for r in range(self.H):
   for c in range(self.W):
    if self.ids[r,c]==255:continue
    got=self.coast.land_mask[r*T+T//2,c*T+T//2];centers.append(bool(got)==bool(self.ids[r,c]!=2))
  return {'screen_chunk_max_difference':diff,'upright_edge_tree_count':len(self.anchors),'all_explicit_trunk_roots_on_owned_forest_and_land':bool(roots_valid),'known_land_water_centers_matching':sum(centers),'known_land_water_centers_checked':len(centers),'hill_cells':len(self.hill_cells),'mountain_cells':len(self.mountain_cells),'hill_bump_instances':sum(i<2 for y,x,i in self.hills.anchors) if self.hills else 0,'mountain_instances':sum(i>=2 for y,x,i in self.hills.anchors) if self.hills else 0,'all_hill_anchors_on_owned_hill_cells':all(self.hills.mask[int(y/T),int(x/T)] for y,x,_ in self.hills.anchors) if self.hills else True,'reusable_materials':6+int(self.pine_material is not None)+int(self.jungle_material is not None)+len(self.cold_weights)+int(self.ice is not None),'reusable_tree_sprites':4+len(self.pine_trees),'reusable_jungle_sprites':len(self.jungle_sprites),'rendered_broadleaf_cells':int(self.fD.sum()),'rendered_pine_cells':int(self.fP.sum()),'rendered_jungle_cells':int(self.fJ.sum()),'resource_and_hill_clearance_records':self.clearance_records,'all_edge_roots_outside_support_openings':all(self.clearance_distance[int(by),int(bx)]>=5 for by,bx,_ in self.anchors),'jungle_edge_root_count':sum(bool(self.fJ[int(by/T),int(bx/T)]) for by,bx,idx in self.anchors),'vineyard_shared_row_field':self.vineyard.config if self.vineyard is not None else None,'visible_river_paths':len(self.river.path_ids) if self.river is not None else 0,'river_edge_topology':self.river_edge_records,'reusable_site_sprites':4,'unique_illustration_tiles_used':0,'forest_interior_sampled_upright_in_screen_space':True,'quality_verdict':'requires visual review; geometry tests are not quality proof'}
