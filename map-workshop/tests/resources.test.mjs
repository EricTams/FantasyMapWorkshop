import test from 'node:test';import assert from 'node:assert/strict';
import {resourceMembers} from '../resources.js';
test('stags and pepper bushes use distinct native sprites with independent ground depth',()=>{
 for(const kind of ['white_stags','scarlet_pepper']){
  const members=resourceMembers(kind,5,7);assert.equal(members.length,2);
  assert.notEqual(members[0].path,members[1].path);assert.ok(members[0].y<members[1].y);
  for(const m of members){assert.ok(m.x>5*128&&m.x<6*128);assert.ok(m.y>7*96&&m.y<8*96);assert.ok(m.width>40);assert.ok(m.protectedFraction>.8&&m.protectedFraction<1);}
  assert.deepEqual(resourceMembers(kind,5,7),members);
 }
 assert.deepEqual(resourceMembers('fish',5,7),[]);
});
