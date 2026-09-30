import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';

const stage=document.querySelector('#stage'), loading=document.querySelector('#loading');
const $=id=>document.getElementById(id);
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
let renderer,composer,root,face,uniforms,config,auto=false,flipped=false,dragging=false;
let targetX=0.025,targetY=-0.13,targetZoom=1,rotationX=targetX,rotationY=targetY;
let last={x:0,y:0},lastTime=0,elapsed=0;
const scene=new THREE.Scene();
const camera=new THREE.OrthographicCamera(-5,5,5.65,-5.65,.1,100); camera.position.set(0,0,20); camera.lookAt(0,0,0);
const vertex=`varying vec2 vUv;
void main(){vUv=vec2(uv.x,1.0-uv.y);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`;
const shared=`precision highp float;
varying vec2 vUv;
uniform float uTime,uFoil,uScale,uDepth,uBgDepth,uSafeScale;
uniform vec2 uSafeOffset;
uniform vec3 uView;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
vec3 spectrum(float t){t=fract(t);vec3 pink=vec3(1.,.32,.62),yellow=vec3(1.,.85,.32),blue=vec3(.22,.62,1.);if(t<.35)return mix(pink,yellow,t/.35);if(t<.7)return mix(yellow,blue,(t-.35)/.35);return mix(blue,vec3(1.),(t-.7)/.3);}
vec3 overlay(vec3 b,vec3 f){return mix(2.*b*f,1.-2.*(1.-b)*(1.-f),step(vec3(.5),b));}
float inside(vec2 p){return step(0.,p.x)*step(0.,p.y)*step(p.x,1.)*step(p.y,1.);}
vec2 parallax(vec2 p,float s,float d){return (p-.5)*s+.5+uView.xy/max(abs(uView.z),.35)*d*.14;}
float wave(vec2 p){vec2 a=p+uView.xy*2.4;return .5+.5*sin((a.x*.848-a.y*.530)*6.283*.55+7.*noise(a*1.5));}
float star(vec2 p){vec2 q=p*105.,id=floor(q),f=fract(q);float first=9.,second=9.;for(int y=-1;y<=1;y++){for(int x=-1;x<=1;x++){vec2 g=vec2(float(x),float(y));vec2 o=vec2(hash(id+g),hash(id+g+43.3));float d=length(g+o-f);if(d<first){second=first;first=d;}else second=min(second,d);}}float edge=1.-smoothstep(.01,.035,second-first);float sparse=step(.90,hash(id+8.8));float twinkle=pow(.5+.5*sin(uTime*1.8+hash(id)*30.+uView.x*27.+uView.y*21.),6.);return edge*sparse*twinkle;}
`;
const fragment=shared+`
uniform sampler2D tSubject,tBackground,tText,tLine;
void main(){
 vec2 uv=vUv;
 vec2 su=parallax(uv,uScale,uDepth)*uSafeScale+uSafeOffset;
 vec2 bu=parallax(uv,1.,uBgDepth);
 vec4 sub=texture2D(tSubject,clamp(su,0.,1.));sub.a*=inside(su);
 vec3 bg=texture2D(tBackground,clamp(bu,0.,1.)).rgb;
 float w=wave(uv); vec3 foil=spectrum(w*.8+noise(uv*5.)*.12);
 vec3 subject=mix(sub.rgb,overlay(sub.rgb,foil),uFoil*.28);
 bg=mix(bg,overlay(bg,foil),uFoil*.36);
 vec3 col=mix(bg,subject,sub.a);
 float sweep=pow(max(0.,sin((uv.x*.83+uv.y*.35+uView.x*1.8+uView.y*.9)*6.283)),12.);
 col+=foil*sweep*uFoil*.28;
 float line=1.-smoothstep(.06,.25,texture2D(tLine,clamp(su,0.,1.)).r);
 col+=vec3(1.,.94,.78)*line*inside(su)*sub.a*sweep*uFoil*.22;
 col+=vec3(.66,.86,1.)*star(bu)*uFoil*.65*(1.-sub.a*.7);
 vec4 text=texture2D(tText,uv);col=mix(col,text.rgb,text.a);
 // Keep print saturation; the selective high luminance feeds the bloom pass.
 gl_FragColor=vec4(pow(max(col,vec3(0.)),vec3(2.2)),1.);
 #include <tonemapping_fragment>
 #include <colorspace_fragment>
}`;
const edgeFragment=shared+`void main(){vec3 col=mix(vec3(.55,.34,.1),spectrum(wave(vUv)),.65+uFoil*.2);gl_FragColor=vec4(col*.8+.14,1.);
#include <tonemapping_fragment>
#include <colorspace_fragment>
}`;
// The rear shares the front UVs; compensate for viewing it from the opposite side.
const backFragment=shared+`uniform sampler2D tBack;
void main(){vec4 art=texture2D(tBack,vec2(1.-vUv.x,vUv.y));vec2 p=vUv-.5;float filigree=.5+.5*sin(length(p*vec2(1.,1.5))*100.+noise(p*15.)*4.);vec3 col=mix(vec3(.025,.042,.064),vec3(.085,.092,.11),filigree*.35);float border=step(.465,max(abs(p.x),abs(p.y)));col=mix(col,spectrum(wave(vUv))*.55,border);col+=spectrum(wave(vUv))*uFoil*.08;col=mix(col,art.rgb,art.a);gl_FragColor=vec4(pow(col,vec3(2.2)),1.);
#include <tonemapping_fragment>
#include <colorspace_fragment>
}`;
function backTexture(){
 const c=document.createElement('canvas');c.width=1024;c.height=1536;const ctx=c.getContext('2d');
 ctx.clearRect(0,0,1024,1536);ctx.fillStyle='rgba(255,255,255,.94)';ctx.fillRect(0,0,1024,1536);
 ctx.fillStyle='#0a0a0a';ctx.textAlign='left';ctx.font='700 26px Arial, sans-serif';ctx.fillText('HOLO CARD STUDIO',86,110);
 ctx.strokeStyle='rgba(191,162,107,.45)';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(86,142);ctx.lineTo(938,142);ctx.stroke();
 ctx.fillStyle='#0a0a0a';ctx.font='800 72px Arial, sans-serif';wrapCanvasText(ctx,String(config.title||'CARD TITLE').toUpperCase(),86,300,850,84);
 ctx.fillStyle='#555';ctx.font='600 25px Arial, sans-serif';ctx.fillText(String(config.collection||'').toUpperCase(),86,520);
 // 结构化卡背：有 stats/honors 字段时采用新版式；否则回退旧版式（仅 back_story 长文）
 if(config.stats||config.honors||config.quote){
  ctx.fillStyle='#1c1c1c';ctx.font='500 28px Arial, sans-serif';
  wrapTextSmart(ctx,String(config.back_story||'This card is a HoloLab original.'),86,568,850,38,5);
  const label=(t,y)=>{ctx.fillStyle='#bfa26b';ctx.font='700 21px Arial, sans-serif';ctx.fillText(t,86,y);ctx.strokeStyle='rgba(191,162,107,.5)';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(86,y+8);ctx.lineTo(938,y+8);ctx.stroke();};
  label('KARRIERE · CAREER',810);
  ctx.fillStyle='#0a0a0a';ctx.font='700 26px Arial, sans-serif';
  wrapTextSmart(ctx,String(config.stats||''),86,854,850,40,2);
  let hy=968;
  if(config.honors&&config.honors.length){
   label('ERFOLGE · HONORS',hy);
   hy=1020;
   ctx.fillStyle='#1c1c1c';ctx.font='500 24px Arial, sans-serif';
   for(const h of config.honors.slice(0,7)){ctx.fillStyle='#bfa26b';ctx.font='700 24px Arial, sans-serif';ctx.fillText('•',86,hy);ctx.fillStyle='#1c1c1c';ctx.font='500 24px Arial, sans-serif';ctx.fillText(String(h).slice(0,64),112,hy);hy+=34;}
  }
  if(config.quote){ctx.fillStyle='#0a0a0a';ctx.font='italic 700 27px Arial, sans-serif';wrapTextSmart(ctx,'“'+String(config.quote)+'”',86,hy+12,850,38,2);}
 } else {
  ctx.fillStyle='#1c1c1c';ctx.font='500 30px Arial, sans-serif';
  wrapTextSmart(ctx,String(config.back_story||'This card is a HoloLab original.'),86,580,850,46,12);
 }
 ctx.fillStyle='#696969';ctx.font='600 21px Arial, sans-serif';ctx.fillText('EDITION '+String(config.edition||'001'),86,1418);
 const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.NoColorSpace;return tex;
}
function wrapCanvasText(ctx,text,x,y,maxWidth,lineHeight){
 const words=text.split(/\s+/);let line='';let row=0;
 for(const word of words){const probe=line?line+' '+word:word;if(ctx.measureText(probe).width>maxWidth&&line){ctx.fillText(line,x,y+row*lineHeight);line=word;row++;}else line=probe;}
 if(line)ctx.fillText(line,x,y+row*lineHeight);
}
function wrapTextSmart(ctx,text,x,y,maxWidth,lineHeight,maxLines){
 const chars=[...text];let line='';let row=0;
 for(const ch of chars){
  const probe=line+ch;
  if(ctx.measureText(probe).width>maxWidth&&line){
   ctx.fillText(line,x,y+row*lineHeight);line=ch;row++;
   if(row>=maxLines)return;
  } else line=probe;
 }
 if(line&&row<maxLines)ctx.fillText(line,x,y+row*lineHeight);
}
function escHtml(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function renderMore(){
 const grid=$('more-grid');if(!grid)return;
 try{
  const all=await fetch('../../cards.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(d=>d.cards||[]);
  const cur=config._card_id||config.slug;
  const selfCard=all.find(c=>c.id===cur);
  const dateEl=$('meta-date');
  if(dateEl&&selfCard?.date){dateEl.textContent=String(selfCard.date);dateEl.closest('div')?.removeAttribute('hidden');}
  const others=all.filter(c=>c.id!==cur);
  const same=others.filter(c=>c.collection===config.collection);
  const rest=others.filter(c=>c.collection!==config.collection);
  const pick=[...same,...rest].slice(0,4);
  if(!pick.length)return;
  grid.innerHTML=pick.map(c=>`<a class="more-card" href="../../${escHtml(c.url)}">
    <img src="../../${escHtml(c.thumb)}" alt="${escHtml(c.title)}" loading="lazy">
    <span class="more-title">${escHtml(c.title)}</span>
    <span class="more-sub">${escHtml(c.edition||c.collection||'')}</span>
  </a>`).join('');
 }catch(e){grid.innerHTML='<p class="more-empty">More cards live in the <a href="../../index.html">gallery</a>.</p>';}
}
async function init(){
 config=await fetch('./card-config.json').then(r=>{if(!r.ok)throw Error('Card configuration was not found.');return r.json();});
 document.title=(config.title||'CARD TITLE')+' — HoloLab Studio';
 for(const [id,key]of Object.entries({'card-title':'title','subtitle':'subtitle','edition':'edition'}))if(config[key]&&$(id))$(id).textContent=config[key];
 for(const [id,key]of Object.entries({'meta-collection':'collection','meta-technique':'technique','meta-date':'date'})){
  const v=config[key];const el=$(id);
  if(el&&v){el.textContent=String(v);el.closest('div')?.removeAttribute('hidden');}
 }
 const descEl=$('desc');
 if(descEl&&config.description){
  const d=String(config.description).trim();descEl.textContent=d.length>260?d.slice(0,257)+'…':d;
 }
 renderMore();
 renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true,powerPreference:'high-performance'});renderer.setClearColor((window.HoloLabTheme&&HoloLabTheme.get()==='dark')?0x12100d:0xf6f4ee,1);if(window.HoloLabTheme){var _th=window.__hololabOnTheme||function(){};window.__hololabOnTheme=function(t){if(renderer)renderer.setClearColor(t==='dark'?0x12100d:0xf6f4ee,1);_th(t);};}renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.NoToneMapping;renderer.toneMappingExposure=1;stage.append(renderer.domElement);
 composer=new EffectComposer(renderer);composer.addPass(new RenderPass(scene,camera));composer.addPass(new UnrealBloomPass(new THREE.Vector2(720,1000),.18,.35,1.0));composer.addPass(new OutputPass());
 const loader=new THREE.TextureLoader();const names=['subject','background','text','lineart'];const textures=await Promise.all(names.map(name=>loader.loadAsync(config.assets[name])));textures.forEach(t=>{t.colorSpace=THREE.NoColorSpace;t.anisotropy=Math.min(renderer.capabilities.getMaxAnisotropy(),8);});
 const prm=config.parameters||{};uniforms={tSubject:{value:textures[0]},tBackground:{value:textures[1]},tText:{value:textures[2]},tLine:{value:textures[3]},tBack:{value:backTexture()},uTime:{value:0},uView:{value:new THREE.Vector3(0,0,1)},uFoil:{value:prm.foil??.65},uScale:{value:prm.subjectScale??1.25},uDepth:{value:prm.subjectDepth??.4},uBgDepth:{value:prm.backgroundDepth??-.25},uSafeScale:{value:config.safeArea?.scale??1.12},uSafeOffset:{value:new THREE.Vector2(...(config.safeArea?.offset??[-.06,-.085]))}};
 const frontMat=new THREE.ShaderMaterial({uniforms,vertexShader:vertex,fragmentShader:fragment,side:THREE.FrontSide});const edgeMat=new THREE.ShaderMaterial({uniforms,vertexShader:vertex,fragmentShader:edgeFragment});const backMat=new THREE.ShaderMaterial({uniforms,vertexShader:vertex,fragmentShader:backFragment});const goldMat=new THREE.MeshBasicMaterial({color:0xbfa26b});
 const gltf=await new GLTFLoader().loadAsync(config.assets.model);root=new THREE.Group();root.add(gltf.scene);scene.add(root);
 gltf.scene.traverse(ob=>{if(!ob.isMesh)return;const role=ob.material?.name;if(role==='web_front'){ob.material=frontMat;face=ob;}else if(role==='web_back')ob.material=backMat;else if(role==='web_gold')ob.material=goldMat;else if(role==='web_text')ob.visible=false;else ob.material=edgeMat;});
 if(!face)throw Error('The Blender model is missing the web_front material.');
 setupControls();new ResizeObserver(resize).observe(stage);resize();loading.remove();
 window.__holo={ready:true,config,renderer,root,uniforms,reset,modelSource:config.assets.model};renderer.setAnimationLoop(animate);
}
function resize(){const w=stage.clientWidth,h=stage.clientHeight;if(!w||!h||!renderer)return;const aspect=w/h;const halfH=5.65/targetZoom;camera.left=-halfH*aspect;camera.right=halfH*aspect;camera.top=halfH;camera.bottom=-halfH;camera.updateProjectionMatrix();renderer.setSize(w,h);composer.setSize(w,h);}
function setAuto(value){auto=value;$('auto').setAttribute('aria-pressed',String(auto));$('auto').textContent=auto?'PAUSE':'AUTO';}
function reset(){targetX=.025;targetY=-.13;targetZoom=1;flipped=false;setAuto(false);$('flip').textContent='FLIP';$('view-label').textContent='FRONT';resize();}
function flip(){flipped=!flipped;setAuto(false);targetY=flipped?Math.PI:0;targetX=0;$('flip').textContent=flipped?'FRONT':'FLIP';$('view-label').textContent=flipped?'BACK':'FRONT';}
function setupControls(){
 for(const [id,name,label] of [['foil','uFoil','foil-value'],['scale','uScale','scale-value'],['depth','uDepth','depth-value'],['bg-depth','uBgDepth','bg-depth-value']]){const input=$(id);input.value=uniforms[name].value;const update=()=>{uniforms[name].value=Number(input.value);$(label).value=id==='foil'?Math.round(input.value*100)+'%':Number(input.value).toFixed(2);};input.addEventListener('input',update);update();}
 stage.addEventListener('pointerdown',e=>{if(e.button!==0)return;dragging=true;setAuto(false);last={x:e.clientX,y:e.clientY};stage.setPointerCapture(e.pointerId);stage.focus({preventScroll:true});});
 stage.addEventListener('pointermove',e=>{if(!dragging)return;const base=flipped?Math.PI:0;targetY=THREE.MathUtils.clamp(targetY+(e.clientX-last.x)*.006,base-.65,base+.65);targetX=THREE.MathUtils.clamp(targetX+(e.clientY-last.y)*.005,-.43,.43);last={x:e.clientX,y:e.clientY};});
 const up=()=>{dragging=false;};stage.addEventListener('pointerup',up);stage.addEventListener('pointercancel',up);stage.addEventListener('lostpointercapture',up);
 stage.addEventListener('wheel',e=>{e.preventDefault();targetZoom=THREE.MathUtils.clamp(targetZoom-e.deltaY*.001,.82,1.18);resize();},{passive:false});
 stage.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','f','F','r','R'].includes(e.key)){e.preventDefault();setAuto(false);}const base=flipped?Math.PI:0;if(e.key==='ArrowLeft')targetY-=.07;if(e.key==='ArrowRight')targetY+=.07;if(e.key==='ArrowUp')targetX-=.06;if(e.key==='ArrowDown')targetX+=.06;if(e.key.toLowerCase()==='f')flip();if(e.key.toLowerCase()==='r')reset();const currentBase=flipped?Math.PI:0;targetY=THREE.MathUtils.clamp(targetY,currentBase-.65,currentBase+.65);targetX=THREE.MathUtils.clamp(targetX,-.43,.43);});
 $('auto').onclick=()=>{if(flipped)flip();setAuto(!auto);};$('flip').onclick=flip;$('reset').onclick=reset;
 $('save').onclick=()=>{try{composer.render();const a=document.createElement('a');a.download=(config.title||'card')+'-holographic.png';a.href=renderer.domElement.toDataURL('image/png');a.click();}catch(e){$('save').textContent='RETRY';}};
}
function animate(now){const dt=Math.min((now-lastTime)/1000,.1)||0;lastTime=now;if(!document.hidden)elapsed+=dt;if(auto){targetY=Math.sin(elapsed*.65)*.38;targetX=Math.sin(elapsed*.85)*.12;}
 const ease=reduced?1:1-Math.exp(-dt*8);rotationX+=(targetX-rotationX)*ease;rotationY+=(targetY-rotationY)*ease;root.rotation.set(rotationX,rotationY,0);root.updateMatrixWorld(true);
 uniforms.uView.value.copy(camera.position).applyMatrix4(new THREE.Matrix4().copy(root.matrixWorld).invert()).normalize();uniforms.uTime.value=reduced&&!auto?0:elapsed;composer.render();}
init().catch(error=>{console.error(error);loading.textContent='CARD UNAVAILABLE · 卡片暂不可用\n'+error.message;loading.setAttribute('role','alert');window.__holo={ready:false,error:error.message};});
