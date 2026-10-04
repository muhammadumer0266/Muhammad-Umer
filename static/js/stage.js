// 3D stage: an icosahedron orb with noise-displaced shader, three orbit rings
// with satellites, and a GPU-animated particle field. Ported from
// reference/prototype.html for the full visual specification.
//
// Adaptation note: the prototype is a single scrolling page with six named
// sections (hero, work, system, ask, stack, contact) driving one continuous
// scroll choreography. This site is multi-page, so each page may only
// contain a subset of those anchors (e.g. /about/ has just #stack). Rather
// than force every page to carry all six, layoutKeys() below only builds
// keyframes from whichever anchors exist on the current page. A page with
// one anchor gets a static resting view (the original sample() logic
// already handles a single keyframe correctly: a === b, no interpolation).
// A page with none falls back to the "contact" resting values.
import * as THREE from "./vendor/three.module.min.js";

const VIEW = {
  hero: { x: 1.7, py: 0.05, z: 0, s: 1.25, a: 0.3, d: 1.0 },
  work: { x: -2.9, py: 0.2, z: -1.8, s: 1, a: 0.2, d: 0.35 },
  system: { x: 3.0, py: -0.1, z: -1.6, s: 1, a: 0.24, d: 0.42 },
  ask: { x: -3.0, py: 0.2, z: -1.8, s: 1, a: 0.22, d: 0.35 },
  stack: { x: 2.9, py: 0.1, z: -1.8, s: 1, a: 0.26, d: 0.42 },
  contact: { x: 0, py: 0, z: -2.4, s: 1.5, a: 0.4, d: 0.6 },
};
const ANCHOR_ORDER = ["hero", "work", "system", "ask", "stack", "contact"];

const NOISE = `
vec3 mod289(vec3 x){return x-floor(x*(1.0/289.0))*289.0;}
vec4 mod289(vec4 x){return x-floor(x*(1.0/289.0))*289.0;}
vec4 permute(vec4 x){return mod289(((x*34.0)+1.0)*x);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159-0.85373472095314*r;}
float snoise(vec3 v){
const vec2 C=vec2(1.0/6.0,1.0/3.0);const vec4 D=vec4(0.0,0.5,1.0,2.0);
vec3 i=floor(v+dot(v,C.yyy));vec3 x0=v-i+dot(i,C.xxx);
vec3 g=step(x0.yzx,x0.xyz);vec3 l=1.0-g;
vec3 i1=min(g.xyz,l.zxy);vec3 i2=max(g.xyz,l.zxy);
vec3 x1=x0-i1+C.xxx;vec3 x2=x0-i2+C.yyy;vec3 x3=x0-D.yyy;
i=mod289(i);
vec4 p=permute(permute(permute(i.z+vec4(0.0,i1.z,i2.z,1.0))+i.y+vec4(0.0,i1.y,i2.y,1.0))+i.x+vec4(0.0,i1.x,i2.x,1.0));
float n_=0.142857142857;vec3 ns=n_*D.wyz-D.xzx;
vec4 j=p-49.0*floor(p*ns.z*ns.z);
vec4 x_=floor(j*ns.z);vec4 y_=floor(j-7.0*x_);
vec4 x=x_*ns.x+ns.yyyy;vec4 y=y_*ns.x+ns.yyyy;
vec4 h=1.0-abs(x)-abs(y);
vec4 b0=vec4(x.xy,y.xy);vec4 b1=vec4(x.zw,y.zw);
vec4 s0=floor(b0)*2.0+1.0;vec4 s1=floor(b1)*2.0+1.0;
vec4 sh=-step(h,vec4(0.0));
vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy;vec4 a1=b1.xzyw+s1.xzyw*sh.zzww;
vec3 p0=vec3(a0.xy,h.x);vec3 p1=vec3(a0.zw,h.y);vec3 p2=vec3(a1.xy,h.z);vec3 p3=vec3(a1.zw,h.w);
vec4 norm=taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
p0*=norm.x;p1*=norm.y;p2*=norm.z;p3*=norm.w;
vec4 m=max(0.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.0);m=m*m;
return 42.0*dot(m*m,vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));}
`;

const ORB_VERTEX = `${NOISE}
uniform float uTime;uniform float uAmp;uniform float uAudio;
varying vec3 vN;varying vec3 vV;varying float vD;
void main(){
float n=snoise(position*1.25+vec3(0.0,uTime*0.22,uTime*0.14));
float n2=snoise(position*3.1-vec3(uTime*0.3))*0.22;
float d=(n*0.6+n2)*uAmp+uAudio*0.14;
vec3 p=position+normal*d;vD=d;
vec4 mv=modelViewMatrix*vec4(p,1.0);
vN=normalize(normalMatrix*normal);vV=normalize(-mv.xyz);
gl_Position=projectionMatrix*mv;}
`;

const ORB_FRAGMENT = `
uniform vec3 uMid;uniform vec3 uHi;uniform vec3 uDeep;uniform float uTime;uniform float uDim;
varying vec3 vN;varying vec3 vV;varying float vD;
void main(){
float ndv=max(dot(normalize(vN),normalize(vV)),0.0);
float f=pow(1.0-ndv,2.4);
float c=abs(fract(vD*13.0+uTime*0.04)-0.5);
float line=smoothstep(0.455,0.5,c);
vec3 col=mix(uDeep,uMid*0.5,f);
col+=uHi*pow(f,5.0)*0.85;
col+=uMid*line*(0.14+0.5*f);
float spec=pow(max(dot(normalize(vN),normalize(vec3(-0.4,0.7,0.6))),0.0),24.0);
col+=uHi*spec*0.2;
col*=mix(0.62,1.0,uDim);
gl_FragColor=vec4(col,1.0);}
`;

const PARTICLE_VERTEX = `
attribute float aR;attribute float aA;attribute float aY;attribute float aS;attribute float aSz;
uniform float uTime;uniform float uPx;varying float vA;
void main(){
float a=aA+uTime*aS;
vec3 p=vec3(cos(a)*aR,aY+sin(a*2.0+aR)*0.08,sin(a)*aR);
vec4 mv=modelViewMatrix*vec4(p,1.0);
gl_PointSize=aSz*uPx*(150.0/-mv.z);
vA=clamp((11.0+mv.z)/7.0,0.12,1.0);
gl_Position=projectionMatrix*mv;}
`;

const PARTICLE_FRAGMENT = `
uniform vec3 uColor;uniform float uDim;varying float vA;
void main(){vec2 c=gl_PointCoord-0.5;float d=length(c);if(d>0.5)discard;
gl_FragColor=vec4(uColor,smoothstep(0.5,0.0,d)*vA*0.7*uDim);}
`;

export function initStage(canvas, { reducedMotion, getAudioSpike } = {}) {
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
  } catch (webglError) {
    return null;
  }
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 60);
  camera.position.z = 6;
  const group = new THREE.Group();
  scene.add(group);

  const orbU = {
    uTime: { value: 0 },
    uAmp: { value: 0.3 },
    uAudio: { value: 0 },
    uDim: { value: 1 },
    uMid: { value: new THREE.Color(0x9247a8) },
    uHi: { value: new THREE.Color(0xe6b6f2) },
    uDeep: { value: new THREE.Color(0x07040a) },
  };
  const orbMat = new THREE.ShaderMaterial({
    uniforms: orbU,
    vertexShader: ORB_VERTEX,
    fragmentShader: ORB_FRAGMENT,
  });
  const orb = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 22), orbMat);
  group.add(orb);

  const ringMat = new THREE.MeshBasicMaterial({ color: 0xb56bd6, transparent: true, opacity: 0.42 });
  const satMat = new THREE.MeshBasicMaterial({ color: 0xffe9dc });
  const rings = [];
  [
    [1.75, 0.55, 0.2, 0.0035, 0.35],
    [2.15, -0.35, 0.9, 0.003, -0.24],
    [2.6, 0.15, -0.6, 0.0025, 0.16],
  ].forEach(([radius, rotX, rotY, tube, speed]) => {
    const tilt = new THREE.Group();
    tilt.rotation.x = rotX;
    tilt.rotation.y = rotY;
    const pivot = new THREE.Group();
    pivot.add(new THREE.Mesh(new THREE.TorusGeometry(radius, tube, 6, 180), ringMat));
    const sat = new THREE.Mesh(new THREE.SphereGeometry(0.035, 12, 12), satMat);
    sat.position.x = radius;
    pivot.add(sat);
    tilt.add(pivot);
    group.add(tilt);
    rings.push({ pivot, speed });
  });

  const N = 2200;
  const aR = new Float32Array(N);
  const aA = new Float32Array(N);
  const aY = new Float32Array(N);
  const aS = new Float32Array(N);
  const aSz = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    const r = 2.3 + Math.pow(Math.random(), 1.5) * 4.6;
    aR[i] = r;
    aA[i] = Math.random() * Math.PI * 2;
    aY[i] = (Math.random() - 0.5) * (1.1 + r * 0.32);
    aS[i] = ((Math.random() < 0.5 ? -1 : 1) * (0.06 + Math.random() * 0.22)) / (r * 0.45);
    aSz[i] = 0.6 + Math.random() * 1.4;
  }
  const pGeo = new THREE.BufferGeometry();
  pGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(N * 3), 3));
  pGeo.setAttribute("aR", new THREE.BufferAttribute(aR, 1));
  pGeo.setAttribute("aA", new THREE.BufferAttribute(aA, 1));
  pGeo.setAttribute("aY", new THREE.BufferAttribute(aY, 1));
  pGeo.setAttribute("aS", new THREE.BufferAttribute(aS, 1));
  pGeo.setAttribute("aSz", new THREE.BufferAttribute(aSz, 1));
  const pU = { uTime: { value: 0 }, uPx: { value: 1 }, uDim: { value: 1 }, uColor: { value: new THREE.Color(0xd9a6ee) } };
  const pMat = new THREE.ShaderMaterial({
    uniforms: pU,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    vertexShader: PARTICLE_VERTEX,
    fragmentShader: PARTICLE_FRAGMENT,
  });
  const points = new THREE.Points(pGeo, pMat);
  points.frustumCulled = false;
  group.add(points);

  let K = [];
  let narrow = false;
  let quality = 0;

  function layoutKeys() {
    const maxS = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    const found = ANCHOR_ORDER.map((id) => {
      const node = document.getElementById(id);
      if (!node) return null;
      const center = node.offsetTop + node.offsetHeight / 2 - window.innerHeight / 2;
      return { id, y: Math.max(0, Math.min(center, maxS)) };
    }).filter(Boolean);

    if (found.length === 0) {
      K = [{ y: 0, ...VIEW.contact }];
      return;
    }
    found.sort((a, b) => a.y - b.y);
    let prev = -1;
    K = found.map((f, n) => {
      let y = f.y;
      if (n === 0) y = 0;
      if (n === found.length - 1) y = maxS;
      y = Math.max(prev + 1, Math.min(y, maxS));
      prev = y;
      return { y, ...VIEW[f.id] };
    });
  }

  const cur = { x: 0, py: 0, z: 0, s: 1, a: 0.3, d: 1 };
  function sample(sy) {
    let a, b, u;
    if (sy <= K[0].y) {
      a = b = K[0];
      u = 0;
    } else if (sy >= K[K.length - 1].y) {
      a = b = K[K.length - 1];
      u = 0;
    } else {
      for (let i = 1; i < K.length; i++) {
        if (sy <= K[i].y) {
          a = K[i - 1];
          b = K[i];
          break;
        }
      }
      u = (sy - a.y) / (b.y - a.y);
      u = u * u * (3 - 2 * u);
    }
    cur.x = a.x + (b.x - a.x) * u;
    cur.py = a.py + (b.py - a.py) * u;
    cur.z = a.z + (b.z - a.z) * u;
    cur.s = a.s + (b.s - a.s) * u;
    cur.a = a.a + (b.a - a.a) * u;
    cur.d = a.d + (b.d - a.d) * u;
    return cur;
  }

  function resize() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    renderer.setPixelRatio(quality >= 1 ? 1 : Math.min(window.devicePixelRatio || 1, 1.75));
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    pU.uPx.value = renderer.getPixelRatio();
    narrow = camera.aspect < 0.9;
    layoutKeys();
  }
  window.addEventListener("resize", resize);
  window.addEventListener("load", layoutKeys);
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(layoutKeys);
  }
  if ("ResizeObserver" in window) {
    new ResizeObserver(layoutKeys).observe(document.body);
  }
  resize();

  let mx = 0;
  let my = 0;
  let tx = 0;
  let ty = 0;
  window.addEventListener(
    "pointermove",
    (e) => {
      tx = e.clientX / window.innerWidth - 0.5;
      ty = e.clientY / window.innerHeight - 0.5;
    },
    { passive: true },
  );

  let t = 0;
  let last = performance.now();
  let sy = window.scrollY;
  let prevSy = sy;
  let energy = 0;
  let fc = 0;
  let ft = last;
  let rafId = null;
  let disposed = false;

  function frame(now) {
    if (disposed) return;
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    t += dt * (reducedMotion ? 0.2 : 1);
    const target = window.scrollY;
    sy += (target - sy) * Math.min(1, dt * 5);
    const vel = Math.abs(sy - prevSy) / Math.max(dt, 0.001);
    prevSy = sy;
    energy += (Math.min(vel / 2200, 1) - energy) * Math.min(1, dt * 6);
    mx += (tx - mx) * Math.min(1, dt * 3);
    my += (ty - my) * Math.min(1, dt * 3);

    const s = sample(sy);
    let x = s.x;
    let y = s.py;
    let sc = s.s;
    if (narrow) {
      x *= 0.12;
      y = y * 0.4 + 1.35;
      sc *= 0.72;
    } else {
      x *= Math.min(1, camera.aspect / 1.7);
    }
    group.position.set(x + mx * 0.25, y - my * 0.18, s.z);
    group.scale.setScalar(sc);
    group.rotation.y = t * 0.16 + sy * 0.0009 + mx * 0.5;
    group.rotation.x = my * 0.25 + Math.sin(t * 0.3) * 0.05;

    const spike = getAudioSpike ? getAudioSpike() : 0;
    orbU.uTime.value = t;
    pU.uTime.value = t;
    orbU.uAmp.value = s.a + energy * 0.16;
    orbU.uAudio.value = spike;
    orbU.uDim.value = s.d;
    pU.uDim.value = s.d;
    for (const ring of rings) {
      ring.pivot.rotation.z += dt * ring.speed * 2.2;
    }
    ringMat.opacity = 0.16 + 0.3 * s.d;
    renderer.render(scene, camera);

    fc++;
    if (now - ft >= 1000) {
      const fps = Math.round((fc * 1000) / (now - ft));
      fc = 0;
      ft = now;
      const fpsEl = document.getElementById("fps-readout");
      if (fpsEl) fpsEl.textContent = `${fps} fps`;
      if (!reducedMotion && now > 4000 && fps < 38 && quality < 2) {
        quality++;
        if (quality === 1) resize();
        else pGeo.setDrawRange(0, Math.floor(N / 3));
      }
    }
    rafId = requestAnimationFrame(frame);
  }
  rafId = requestAnimationFrame(frame);

  let visible = true;
  document.addEventListener("visibilitychange", () => {
    visible = document.visibilityState === "visible";
    if (visible && rafId === null) {
      last = performance.now();
      rafId = requestAnimationFrame(frame);
    } else if (!visible && rafId !== null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
  });

  function dispose() {
    disposed = true;
    if (rafId !== null) cancelAnimationFrame(rafId);
    window.removeEventListener("resize", resize);
    orb.geometry.dispose();
    orbMat.dispose();
    pGeo.dispose();
    pMat.dispose();
    ringMat.dispose();
    satMat.dispose();
    renderer.dispose();
  }
  window.addEventListener("pagehide", dispose, { once: true });

  return { dispose };
}
