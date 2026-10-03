"""Explicit shared-edge topology for authored game rivers. Source traces stay separate."""
from collections import defaultdict
import math,numpy as np
VERSION=1
DEFAULT_BROOK={'version':1,'coordinate_order':'integer grid corners [x,y]','mode':'shared_edges','routes':[{'id':'brook','nodes':[[4,0],[4,1],[4,2],[3,2],[3,3],[4,3],[4,4],[4,5],[4,6]],'coast_outlet':True}],'provenance':'Authored game design: rivers run between gameplay cells. Centerline meanders locally near these shared edges.'}
def edge_key(a,b):
 x,y=a;xx,yy=b
 if abs(xx-x)+abs(yy-y)!=1:raise ValueError('River routes must contain unit grid edges')
 return f'V:{x}:{min(y,yy)}' if x==xx else f'H:{min(x,xx)}:{y}'
def compile_edges(spec,shape,tile=128):
 H,W=shape;edges={};graph=defaultdict(set);paths=[]
 for ri,route in enumerate(spec.get('routes',[])):
  nodes=route['nodes'];points=[]
  if len(nodes)<2:raise ValueError('River route needs at least one edge')
  for a,b in zip(nodes[:-1],nodes[1:]):
   if any(int(v)!=v for v in a+b):raise ValueError('River semantic vertices are integer grid corners')
   if any(not(0<=q[0]<=W and 0<=q[1]<=H) for q in [a,b]):raise ValueError('River corner outside map')
   key=edge_key(a,b);x,y=a;xx,yy=b;graph[tuple(a)].add(tuple(b));graph[tuple(b)].add(tuple(a));adj=[]
   if x==xx:
    r=min(y,yy)
    if x>0:adj.append({'cell':[r,x-1],'side':'E'})
    if x<W:adj.append({'cell':[r,x],'side':'W'})
   else:
    c=min(x,xx)
    if y>0:adj.append({'cell':[y-1,c],'side':'S'})
    if y<H:adj.append({'cell':[y,c],'side':'N'})
   edges[key]={'id':key,'grid_start':min(a,b),'grid_end':max(a,b),'adjacent_cells':adj}
   # Canonical edge coordinates ensure two routes sharing an edge use identical paint geometry.
   lo=np.array(min(a,b),float)*tile;hi=np.array(max(a,b),float)*tile;direction=(hi-lo)/tile;normal=np.array([-direction[1],direction[0]]);seed=(int(lo[0])*31+int(lo[1])*17+55)%997;phase=seed/997*math.tau;amp=2.2+(seed%7)/10
   local=[]
   for t in np.linspace(0,1,5):
    offset=amp*math.sin(math.pi*t)*math.sin(math.tau*t+phase);local.append((lo+(hi-lo)*t+normal*offset).tolist())
   if list(a)!=min(a,b):local.reverse()
   points.extend(local if not points else local[1:])
  paths.append({'path_id':route['id'],'route_id':route['id'],'world_nodes':points,'role':'authored_shared_edge','semantic_edge_ids':[edge_key(a,b) for a,b in zip(nodes[:-1],nodes[1:])]})
 unseen=set(graph);components=0
 while unseen:
  components+=1;todo=[unseen.pop()]
  while todo:
   for q in graph[todo.pop()]:
    if q in unseen:unseen.remove(q);todo.append(q)
 records={'version':1,'mode':'shared_edges','edge_count':len(edges),'edges':list(edges.values()),'node_degrees':{f'{x},{y}':len(v) for (x,y),v in graph.items()},'connected_components':components,'junction_nodes':[list(q) for q,v in graph.items() if len(v)>2],'endpoint_nodes':[list(q) for q,v in graph.items() if len(v)==1],'centerline_meander_max_px':2.8,'all_segments_unit_grid_edges':True}
 return paths,records
