"""Only explicit source-evidence links produce occlusion labels; never zip unrelated rivers."""
def pairs(scene):
 rd=scene.get('river_digitization',{});paths=rd.get('paths',[]);lookup={p.get('path_id'):p['fractional_grid_nodes'] for p in paths if p.get('path_id')};out=[]
 for gap in rd.get('occlusions',[]):
  after=lookup.get(gap.get('after_path_id'));before=lookup.get(gap.get('before_path_id'))
  if after and before:out.append((after,before))
  elif after:out.append((after,[after[-1]]))
  elif before:out.append(([before[0]],before))
 return out
