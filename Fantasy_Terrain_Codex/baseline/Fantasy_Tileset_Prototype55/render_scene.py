"""Render any bundled semantic scene; no screenshot or Tiled export dependency."""
from pathlib import Path
import argparse,json
from kit_renderer import KitScene
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('scene_directory',type=Path);a=p.parse_args();folder=a.scene_directory.resolve()
 scene=KitScene(json.loads((folder/'scene.json').read_text()),folder/'shoreline.json',json.loads((folder/'features.json').read_text()))
 out=folder/'generated';out.mkdir(exist_ok=True);im=scene.render();im.save(out/'preview.png');scene.grid(im).save(out/'grid.png')
 qa=scene.qa();(out/'validation.json').write_text(json.dumps(qa,indent=2)+'\n');print(json.dumps(qa,indent=2))
