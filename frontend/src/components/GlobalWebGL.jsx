import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { gsap } from 'gsap';

export default function GlobalWebGL({ appState, scrollProgress = 0, band = null }) {
  const mountRef = useRef(null);
  
  // Keep refs for our 3D objects so we can transition them
  const refs = useRef({
    scene: null, camera: null, renderer: null,
    particles: null, pGeo: null, pMat: null,
    aurora: null, auroraMat: null,
    torus: null, torusMat: null,
    targetState: appState
  });

  useEffect(() => {
    const el = mountRef.current;
    if (!el) return;
    const W = window.innerWidth, H = window.innerHeight;
    
    // 1. Setup Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#05050f');
    scene.fog = new THREE.FogExp2('#05050f', 0.002);
    
    const camera = new THREE.PerspectiveCamera(60, W / H, 0.1, 2000);
    camera.position.z = 300;
    
    const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.0));
    renderer.setSize(W, H);
    el.appendChild(renderer.domElement);
    
    // 2. Setup Particles (15,000 count)
    const PC = 5000;
    const pGeo = new THREE.BufferGeometry();
    const pos = new Float32Array(PC * 3);
    const targetPos = new Float32Array(PC * 3);
    const chaosPos = new Float32Array(PC * 3);
    const spherePos = new Float32Array(PC * 3);
    const gridPos = new Float32Array(PC * 3);
    const tunnelPos = new Float32Array(PC * 3);
    
    for(let i = 0; i < PC; i++) {
      // Chaos
      chaosPos[i*3] = (Math.random() - 0.5) * 800;
      chaosPos[i*3+1] = (Math.random() - 0.5) * 800;
      chaosPos[i*3+2] = (Math.random() - 0.5) * 800;
      
      // Tunnel
      const tAngle = Math.random() * Math.PI * 2;
      const tRadius = 150 + Math.random() * 200; 
      tunnelPos[i*3] = Math.cos(tAngle) * tRadius;
      tunnelPos[i*3+1] = Math.sin(tAngle) * tRadius;
      tunnelPos[i*3+2] = (Math.random() - 0.5) * 2000;

      // Sphere
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = Math.random() * Math.PI * 2;
      const r = 100 + (Math.random() * 20); 
      spherePos[i*3] = r * Math.sin(phi) * Math.cos(theta);
      spherePos[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
      spherePos[i*3+2] = r * Math.cos(phi);
      
      // Grid (Agent Eye View)
      const sq = Math.ceil(Math.cbrt(PC));
      const x = (i % sq) - sq/2;
      const y = (Math.floor(i / sq) % sq) - sq/2;
      const z = (Math.floor(i / (sq*sq))) - sq/2;
      gridPos[i*3] = x * 20;
      gridPos[i*3+1] = y * 20;
      gridPos[i*3+2] = z * 20;
      
      // Initial
      pos[i*3] = chaosPos[i*3];
      pos[i*3+1] = chaosPos[i*3+1];
      pos[i*3+2] = chaosPos[i*3+2];
      targetPos[i*3] = chaosPos[i*3];
      targetPos[i*3+1] = chaosPos[i*3+1];
      targetPos[i*3+2] = chaosPos[i*3+2];
    }
    
    pGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const pMat = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uColor: { value: new THREE.Color('#7c3aed') }, // Purple base
        uOpacity: { value: 0.8 },
        uSize: { value: 4.5 }
      },
      vertexShader: `
        uniform float uTime;
        uniform float uSize;
        varying float vDist;
        void main() {
          vec3 p = position;
          p.x += sin(uTime * 2.0 + p.y * 0.01) * 2.0;
          p.y += cos(uTime * 1.5 + p.x * 0.01) * 2.0;
          vec4 mvPos = modelViewMatrix * vec4(p, 1.0);
          gl_Position = projectionMatrix * mvPos;
          gl_PointSize = uSize * (300.0 / -mvPos.z);
          vDist = length(p);
        }
      `,
      fragmentShader: `
        uniform vec3 uColor;
        uniform float uOpacity;
        varying float vDist;
        void main() {
          vec2 xy = gl_PointCoord.xy - vec2(0.5);
          float ll = length(xy);
          if(ll > 0.5) discard;
          float alpha = (0.5 - ll) * 2.0 * uOpacity;
          gl_FragColor = vec4(uColor, alpha);
        }
      `,
      transparent: true, blending: THREE.AdditiveBlending, depthWrite: false
    });
    const particles = new THREE.Points(pGeo, pMat);
    scene.add(particles);
    
    // 3. Setup Aurora/Plasma (Entry & Results)
    const auroraGeo = new THREE.PlaneGeometry(1200, 1200);
    const auroraMat = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uIntensity: { value: 0.0 }, // 0 in intro, 1 in entry
        uColor1: { value: new THREE.Color('#002244') },
        uColor2: { value: new THREE.Color('#440022') },
      },
      vertexShader: `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
      fragmentShader: `
        uniform float uTime; uniform float uIntensity;
        uniform vec3 uColor1; uniform vec3 uColor2;
        varying vec2 vUv;
        float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
        float noise(vec2 p) {
          vec2 i = floor(p); vec2 f = fract(p); vec2 u = f*f*(3.0-2.0*f);
          return mix(mix(hash(i+vec2(0.0,0.0)), hash(i+vec2(1.0,0.0)), u.x), mix(hash(i+vec2(0.0,1.0)), hash(i+vec2(1.0,1.0)), u.x), u.y);
        }
        void main() {
          vec2 uv = vUv * 3.0; uv.y += uTime * 0.05; uv.x += sin(uTime * 0.05) * 0.5;
          float n = noise(uv * 2.0 + noise(uv * 4.0 + uTime*0.2));
          vec3 col = mix(uColor1, uColor2, sin(uTime*0.3 + vUv.x*4.0)*0.5+0.5);
          float alpha = n * 0.4 * uIntensity * (1.0 - length(vUv - 0.5) * 2.0);
          gl_FragColor = vec4(col, max(0.0, alpha));
        }
      `,
      transparent: true, blending: THREE.AdditiveBlending, depthWrite: false
    });
    const aurora = new THREE.Mesh(auroraGeo, auroraMat);
    aurora.position.z = -300;
    scene.add(aurora);
    
    // 4. Setup Torus Knot (Scanning)
    const torusGeo = new THREE.TorusKnotGeometry(60, 15, 200, 32);
    const torusMat = new THREE.MeshBasicMaterial({
      color: 0x00d9ff, wireframe: true, transparent: true, opacity: 0.0,
      blending: THREE.AdditiveBlending
    });
    const torus = new THREE.Mesh(torusGeo, torusMat);
    scene.add(torus);

    // Save refs
    refs.current = {
      scene, camera, renderer,
      particles, pGeo, pMat,
      aurora, auroraMat,
      torus, torusMat,
      chaosPos, spherePos, gridPos, targetPos, tunnelPos, pos,
      targetState: appState,
      scrollProgress: scrollProgress
    };
    
    // Animation Loop
    let raf;
    const animate = () => {
      raf = requestAnimationFrame(animate);
      const t = Date.now() * 0.001;
      const r = refs.current;
      
      // Update Uniforms
      r.pMat.uniforms.uTime.value = t;
      r.auroraMat.uniforms.uTime.value = t;
      
      // Rotations
      r.particles.rotation.y = t * 0.05;
      r.torus.rotation.x = t * 0.2;
      r.torus.rotation.y = t * 0.3;
      
      // Physics Lerp for Particles
      const pArr = r.pGeo.attributes.position.array;
      const tArr = r.targetPos;
      for(let i=0; i<PC*3; i++) {
        pArr[i] += (tArr[i] - pArr[i]) * 0.05;
      }
      r.pGeo.attributes.position.needsUpdate = true;
      
      // Intro Scroll Logic (only if state === 'intro')
      if (r.targetState === 'intro') {
        const sp = r.scrollProgress; // 0 to 1
        r.camera.position.z = 1000 - (sp * 800); // Fly deeper into tunnel
        r.pMat.uniforms.uOpacity.value = 1.0;
        
        // Thunder flashes: randomly spike aurora intensity based on time and scroll
        r.auroraMat.uniforms.uIntensity.value = Math.random() > 0.92 ? (0.3 + Math.random() * 0.7) : 0.05;
        r.auroraMat.uniforms.uColor1.value = new THREE.Color('#00ffff'); // Cyan flashes
        r.auroraMat.uniforms.uColor2.value = new THREE.Color('#ff00ff'); // Purple flashes
        r.pMat.uniforms.uColor.value = new THREE.Color('#00ffff'); // Particles are cyan

        r.torusMat.opacity = 0;
        
        const speed = 10 + (sp * 40); // Base speed + warp speed on scroll
        
        for(let i=0; i<PC; i++) {
          const idx = i*3;
          // Set X and Y to tunnel shape
          tArr[idx] = r.tunnelPos[idx]; 
          tArr[idx+1] = r.tunnelPos[idx+1];
          // We let lerp handle X/Y, but we directly manipulate Z!
          pArr[idx+2] += speed;
          if (pArr[idx+2] > r.camera.position.z + 100) {
            pArr[idx+2] -= 2000; // Wrap around to far back
          }
          // Also set tArr Z so it doesn't fight the lerp
          tArr[idx+2] = pArr[idx+2];
        }
      }
      
      r.renderer.render(r.scene, r.camera);
    };
    animate();
    
    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', onResize);
    
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
      if(el.contains(renderer.domElement)) el.removeChild(renderer.domElement);
    };
  }, []);

  // Handle State Changes
  useEffect(() => {
    if (!refs.current.scene) return;
    const r = refs.current;
    r.targetState = appState;
    const PC = 5000;
    
    let pColor = { r: 1.0, g: 0.35, b: 0.1 }; // Vivid Amber default
    let aColor1 = new THREE.Color('#002244');
    let aColor2 = new THREE.Color('#440022');
    
    if (band === 'red') {
      pColor = { r: 1.0, g: 0.16, b: 0.16 };
      aColor1 = new THREE.Color('#330000');
      aColor2 = new THREE.Color('#990000');
    } else if (band === 'amber') {
      pColor = { r: 1.0, g: 0.55, b: 0.0 };
      aColor1 = new THREE.Color('#331500');
      aColor2 = new THREE.Color('#995500');
    } else if (band === 'green') {
      pColor = { r: 0.0, g: 1.0, b: 0.53 };
      aColor1 = new THREE.Color('#003311');
      aColor2 = new THREE.Color('#006633');
    }
    
    if (appState === 'entry' || appState === 'results') {
      // Background Aurora high intensity, particles form a subtle grid
      gsap.to(r.auroraMat.uniforms.uIntensity, { value: 1.0, duration: 2 });
      gsap.to(r.torusMat, { opacity: 0.0, duration: 1 });
      gsap.to(r.camera.position, { z: 400, x: 0, y: 0, duration: 2, ease: 'power2.inOut' });
      gsap.to(r.pMat.uniforms.uColor.value, { ...pColor, duration: 2 });
      gsap.to(r.auroraMat.uniforms.uColor1.value, { r: aColor1.r, g: aColor1.g, b: aColor1.b, duration: 2 });
      gsap.to(r.auroraMat.uniforms.uColor2.value, { r: aColor2.r, g: aColor2.g, b: aColor2.b, duration: 2 });
      gsap.to(r.pMat.uniforms.uOpacity, { value: 0.6, duration: 2 });
      
      for(let i=0; i<PC*3; i++) r.targetPos[i] = r.gridPos[i] * 2.0;
    } 
    else if (appState === 'scanning') {
      // Reveal the massive Torus Matrix, hide aurora
      gsap.to(r.auroraMat.uniforms.uIntensity, { value: 0.1, duration: 1 });
      gsap.to(r.torusMat, { opacity: 0.25, duration: 2 });
      gsap.to(r.camera.position, { z: 150, x: 40, y: 20, duration: 3, ease: 'power3.inOut' });
      r.camera.lookAt(0,0,0);
      gsap.to(r.pMat.uniforms.uColor.value, { r: 1.0, g: 0.1, b: 0.1, duration: 2 }); // Red warning
      gsap.to(r.pMat.uniforms.uOpacity, { value: 0.1, duration: 1 });
      
      for(let i=0; i<PC*3; i++) r.targetPos[i] = r.spherePos[i] * 1.5;
    }
    else if (appState === 'agentEye') {
      // Matrix rain / terminal grid
      gsap.to(r.auroraMat.uniforms.uIntensity, { value: 0.0, duration: 1 });
      gsap.to(r.torusMat, { opacity: 0.0, duration: 1 });
      gsap.to(r.camera.position, { z: 200, x: 0, y: 0, duration: 2, ease: 'power2.inOut' });
      gsap.to(r.pMat.uniforms.uColor.value, { r: 0.5, g: 0.0, b: 1.0, duration: 2 }); // Deep purple
      gsap.to(r.pMat.uniforms.uOpacity, { value: 0.6, duration: 2 });
      
      for(let i=0; i<PC*3; i++) r.targetPos[i] = r.gridPos[i];
    }
  }, [appState, band]);
  
  // Handle Scroll updates specifically for Intro
  useEffect(() => {
    if (refs.current.scene) refs.current.scrollProgress = scrollProgress;
  }, [scrollProgress]);

  return <div ref={mountRef} style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }} />;
}
