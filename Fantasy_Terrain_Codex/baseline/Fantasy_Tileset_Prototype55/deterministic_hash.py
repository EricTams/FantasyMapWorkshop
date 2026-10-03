def hash32(x,y,z):
 v=(x*374761393+y*668265263+z*1442695041+641029)&0xffffffff;v=((v^(v>>13))*1274126177)&0xffffffff;return(v^(v>>16))&0xffffffff
