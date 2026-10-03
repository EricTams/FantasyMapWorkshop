import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readdir,readFile,stat,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,relative} from 'node:path';
import {buildSite} from '../scripts/build.mjs';
import {assetPaths} from '../renderer.js';
test('Pages artifact includes loaded assets and resolves local links under a repository subpath',async()=>{
 const out=await mkdtemp(join(tmpdir(),'atlas-pages-'));
 try{
  const result=await buildSite(out);assert.ok(result.bytes<30*1024*1024);
  const rootNames=await readdir(out);for(const excluded of ['checkpoints','scripts','package.json','README.md','Fantasy_Terrain_Codex'])assert.ok(!rootNames.includes(excluded));
  assert.ok(rootNames.includes('.nojekyll'));
  for(const asset of assetPaths)assert.ok((await stat(join(out,'assets',asset))).size>0,asset);
  async function check(dir){for(const item of await readdir(dir,{withFileTypes:true})){const file=join(dir,item.name);if(item.isDirectory()){await check(file);continue;}if(!/\.(html|js|css)$/.test(item.name))continue;
   const text=await readFile(file,'utf8'),base=new URL(relative(out,file),'https://example.github.io/fantasy-map/');
   const refs=[...text.matchAll(/(?:href|src)=["']([^"']+)["']/g),...text.matchAll(/(?:from\s*|import\s*)["'](\.{1,2}\/[^"']+)["']/g)].map(m=>m[1]);
   for(const ref of refs){if(/^(?:https?:|data:|#)/.test(ref))continue;const url=new URL(ref,base);assert.ok(url.pathname.startsWith('/fantasy-map/'),`${file}: ${ref} escapes project path`);let path=url.pathname.slice('/fantasy-map/'.length);if(!path||path.endsWith('/'))path+='index.html';assert.ok((await stat(join(out,decodeURIComponent(path)))).isFile(),ref);}
  }}
  await check(out);
 }finally{await rm(out,{recursive:true,force:true});}
});
