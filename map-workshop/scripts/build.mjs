import {cp,mkdir,readdir,rm,writeFile,stat} from 'node:fs/promises';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {resolve,dirname,join} from 'node:path';
import {assetPaths} from '../renderer.js';
const root=fileURLToPath(new URL('../',import.meta.url));
export async function buildSite(destination=join(root,'dist')){
 // The default dist folder is disposable. Test callers provide an empty temp folder.
 if(resolve(destination)===join(root,'dist'))await rm(destination,{recursive:true,force:true});
 await mkdir(destination,{recursive:true});
 const files=(await readdir(root)).filter(name=>/\.(js|css|html)$/.test(name));
 for(const name of await readdir(join(root,'tests')))if(name.endsWith('.html'))files.push(`tests/${name}`);
 files.push(...assetPaths.map(name=>`assets/${name}`));
 let bytes=0;
 for(const file of files){const target=join(destination,file);await mkdir(dirname(target),{recursive:true});await cp(join(root,file),target);bytes+=(await stat(target)).size;}
 await writeFile(join(destination,'.nojekyll'),'');
 return {files:files.length+1,bytes,destination};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){const result=await buildSite();console.log(`Built ${result.files} files (${(result.bytes/1024/1024).toFixed(1)} MiB) in ${result.destination}`);}
