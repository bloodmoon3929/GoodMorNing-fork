import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const status = document.querySelector('#status');
const hint = document.querySelector('#hint');
const send = (type, data={}) => parent.postMessage({source:'goodmorning-scene',type,...data}, location.origin);
try {
const renderer = new THREE.WebGLRenderer({antialias:true, alpha:true, preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
document.body.prepend(renderer.domElement);
const scene = new THREE.Scene();
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(),.04).texture;
const camera = new THREE.PerspectiveCamera(36,1,.1,1000);
camera.position.set(0,0,260);
const board = new THREE.Group();
scene.add(board);
const light = new THREE.DirectionalLight(0xffffff,2.5); light.position.set(-60,100,180); scene.add(light);
scene.add(new THREE.AmbientLight(0xffffff,1.1));
const paperMaterial = new THREE.MeshStandardMaterial({color:0xffffff,roughness:.92});
const cover = new THREE.Mesh(new THREE.BoxGeometry(105,145,2),new THREE.MeshStandardMaterial({color:0xafd2e7,roughness:.7}));
cover.position.z=-1.4; board.add(cover);
const paper = new THREE.Mesh(new THREE.PlaneGeometry(99,139),paperMaterial); board.add(paper);
for(let i=0;i<6;i++){
  const ring = new THREE.Mesh(new THREE.TorusGeometry(2.5,.58,10,24),new THREE.MeshStandardMaterial({color:0xb8c5cb,metalness:.92,roughness:.24}));
  ring.position.set(-49,50-i*20,1.3); ring.rotation.y=.45; board.add(ring);
}
let data={assets:[],diary:{placements:[]}}, selected=null, tilt=false, generation=0;
const objects = new Map(), cache=new Map(), loader=new GLTFLoader(), textureLoader=new THREE.TextureLoader();
const selection = new THREE.BoxHelper(new THREE.Object3D(),0x609bb9); selection.visible=false; scene.add(selection);
function paperTexture(diary){
  const canvas=document.createElement('canvas'); canvas.width=1024; canvas.height=1434;
  const ctx=canvas.getContext('2d'); ctx.fillStyle=diary.paper||'#fff9eb';ctx.fillRect(0,0,1024,1434);
  ctx.strokeStyle='#a7b9ce35';ctx.lineWidth=1.5;
  for(let y=115;y<1400;y+=42){ctx.beginPath();ctx.moveTo(58,y);ctx.lineTo(990,y);ctx.stroke();}
  ctx.fillStyle='#67828f';ctx.font='20px "Malgun Gothic",sans-serif';ctx.fillText((diary.date||'').replaceAll('-',' . '),78,66);
  ctx.fillStyle='#3e505b';ctx.font='bold 36px "Malgun Gothic",sans-serif';ctx.fillText(diary.title||'나의 다이어리',78,142,860);
  ctx.fillStyle='#768792';ctx.font='23px "Malgun Gothic",sans-serif';
  const text=diary.note||'';let line='', y=200;
  for(const char of text){if(char==='\n'||ctx.measureText(line+char).width>850){ctx.fillText(line,78,y);y+=36;line='';if(y>1300)break;if(char==='\n')continue;}line+=char;}
  if(y<=1300)ctx.fillText(line,78,y);
  ctx.fillStyle='#94b4c5';ctx.font='16px sans-serif';ctx.fillText('goodmorning  ·  little things, lovely days',78,1385);
  const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
  paperMaterial.map?.dispose();paperMaterial.map=texture;paperMaterial.needsUpdate=true;
}
function pose(group,p){
  group.position.set((p.x-.5)*99,(.5-p.y)*139,.25+data.diary.placements.indexOf(p)*.1);
  group.rotation.z=-p.rotation*Math.PI/180;
  group.scale.setScalar(p.size*99/group.userData.width);
}
async function model(asset){
  if(cache.has(asset.id))return cache.get(asset.id);
  let object;
  if(asset.kind==='photo'){
    const response=await fetch(asset.thumbnail,{headers:data.headers||{}});
    if(!response.ok)throw Error('사진을 불러오지 못했어요.');
    const url=URL.createObjectURL(await response.blob());
    let tex;
    try{tex=await textureLoader.loadAsync(url);}finally{URL.revokeObjectURL(url);}
    tex.colorSpace=THREE.SRGBColorSpace;
    const ratio=tex.image.height/tex.image.width;
    object=new THREE.Group();
    const frame=new THREE.Mesh(new THREE.BoxGeometry(1.12,ratio+.2,.015),new THREE.MeshStandardMaterial({color:0xfffef8,roughness:.8}));
    object.add(frame);
    const photo=new THREE.Mesh(new THREE.PlaneGeometry(1,ratio),new THREE.MeshBasicMaterial({map:tex}));
    photo.position.set(0,.035,.02);object.add(photo);
  }else{
    loader.setRequestHeader(data.headers||{});
    object=(await loader.loadAsync(asset.model)).scene;
    object.traverse(o=>{if(o.isMesh){o.material.side=THREE.DoubleSide;}});
  }
  cache.set(asset.id,object);return object;
}
async function load(payload){
  const revision=++generation;data=payload;
  paperTexture(data.diary);
  for(const [id,object]of objects){if(!data.diary.placements.some(p=>p.id===id)){board.remove(object);objects.delete(id);}}
  let errors=[];
  for(const p of data.diary.placements){
    let group=objects.get(p.id);
    if(!group){
      const asset=data.assets.find(a=>a.id===p.asset_id);if(!asset)continue;
      try{
        const original=await model(asset);if(revision!==generation)return;
        group=new THREE.Group();const item=original.clone(true);
        const bounds=new THREE.Box3().setFromObject(item), center=bounds.getCenter(new THREE.Vector3());
        item.position.sub(center);item.position.z+=bounds.getSize(new THREE.Vector3()).z/2;
        group.add(item);group.userData={id:p.id,width:bounds.max.x-bounds.min.x};
        group.traverse(o=>o.userData.placement=p.id);
        objects.set(p.id,group);board.add(group);
      }catch(error){errors.push(p.asset_id);send('error',{message:'스티커 모델을 불러오지 못했어요.'});continue;}
    }
    pose(group,p);
  }
  if(revision!==generation)return;
  status.textContent=errors.length?'일부 스티커를 불러오지 못했어요. 새로고침해 주세요.':'';
  select(data.selected);send('loaded',{count:objects.size});
}
function select(id){
  selected=objects.has(id)?id:null;
  selection.visible=!!selected;
  if(selected){board.updateMatrixWorld(true);selection.setFromObject(objects.get(selected));}
  send('select',{id:selected});
}
const raycaster=new THREE.Raycaster(), pointer=new THREE.Vector2();
function ray(event){const r=renderer.domElement.getBoundingClientRect();pointer.set((event.clientX-r.left)/r.width*2-1,-(event.clientY-r.top)/r.height*2+1);raycaster.setFromCamera(pointer,camera);}
function onPaper(){const hit=raycaster.intersectObject(paper)[0];return hit?board.worldToLocal(hit.point):null;}
let drag=null;
renderer.domElement.addEventListener('pointerdown',event=>{
  ray(event);const hits=raycaster.intersectObjects([...objects.values()],true), point=onPaper();
  if(tilt){drag={kind:'tilt',x:event.clientX,y:event.clientY,rx:board.rotation.x,ry:board.rotation.y};}
  else if(hits.length&&point){const id=hits[0].object.userData.placement;select(id);const obj=objects.get(id);drag={kind:'move',id,dx:point.x-obj.position.x,dy:point.y-obj.position.y};}
  else select(null);
  renderer.domElement.setPointerCapture(event.pointerId);
});
renderer.domElement.addEventListener('pointermove',event=>{
  if(!drag)return;
  if(drag.kind==='tilt'){board.rotation.x=THREE.MathUtils.clamp(drag.rx+(event.clientY-drag.y)*.006,-.8,.8);board.rotation.y=THREE.MathUtils.clamp(drag.ry+(event.clientX-drag.x)*.006,-.7,.7);}
  else {ray(event);const point=onPaper();if(!point)return;const p=data.diary.placements.find(p=>p.id===drag.id);if(!p)return;p.x=THREE.MathUtils.clamp((point.x-drag.dx)/99+.5,.03,.97);p.y=THREE.MathUtils.clamp(.5-(point.y-drag.dy)/139,.03,.97);pose(objects.get(p.id),p);}
});
const end=()=>{if(drag?.kind==='move')send('change',{placements:data.diary.placements});drag=null;};
renderer.domElement.addEventListener('pointerup',end);renderer.domElement.addEventListener('pointercancel',end);
addEventListener('message',event=>{
  if(event.origin!==location.origin||event.source!==parent||event.data?.source!=='goodmorning-app')return;
  const m=event.data;
  if(m.type==='load')load(m.data);
  if(m.type==='select')select(m.id);
  if(m.type==='tilt'){tilt=m.enabled;hint.textContent=tilt?'빈 곳을 끌어 유광 스티커를 기울여 보세요':'스티커를 끌어 옮겨 보세요';if(!tilt){board.rotation.set(0,0,0);}}
  if(m.type==='patch'){
    const p=data.diary.placements.find(p=>p.id===m.id);if(p){Object.assign(p,m.patch);pose(objects.get(p.id),p);}
  }
  if(m.type==='export'){
    const visible=selection.visible;selection.visible=false;renderer.render(scene,camera);
    const link=document.createElement('a');link.download='goodmorning-diary.png';link.href=renderer.domElement.toDataURL('image/png');link.click();selection.visible=visible;
  }
});
function resize(){const w=innerWidth,h=innerHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.position.z=Math.max(245,180/camera.aspect);camera.updateProjectionMatrix();}
addEventListener('resize',resize);resize();
renderer.setAnimationLoop(()=>{if(selected&&objects.has(selected))selection.setFromObject(objects.get(selected));renderer.render(scene,camera);});
send('ready');
}catch(error){status.textContent='입체 보기를 시작하지 못했어요. WebGL을 지원하는 브라우저에서 열어 주세요.';send('error',{message:String(error)});}
