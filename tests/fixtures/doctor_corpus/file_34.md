# anime-universe-teaser â€” Immersive 3D Next.js Teaser
# D:\Repositories\anime-universe-teaser\CLAUDE.md

## What This Is
An immersive, interactive Next.js 3D teaser for "anime-universe". It leverages React Three Fiber (R3F) for 3D rendering, Theatre.js for cinematic animation sequencing, and GSAP with Lenis for smooth scroll-driven experiences.

## When to Load This
- When making modifications to the Anime Universe teaser site.
- When referencing a "winning combination" of Theatre.js + R3F + GSAP.
- When studying how to integrate complex 3D scenes within a Next.js App Router context.

---

## CORE API & SETUP

### Setup
```bash
npm install
npm run dev
```

### Architecture
- **Framework**: Next.js (App Router)
- **3D Engine**: @react-three/fiber, @react-three/drei, three
- **Animations**: GSAP, motion, @theatre/core
- **Scrolling**: Lenis
- **Audio**: Tone.js

---

## INTEGRATION POINTS â€” CROSS-DEPARTMENT ROUTING

| Department | Repo | Relationship |
|---|---|---|
| FRONTEND | next.js | Application shell and routing |
| 3D | react-three-fiber | Core rendering canvas |
| 3D | drei | 3D helpers and environment |
| ANIMATION | theatre | Cinematic 3D keyframing |
| ANIMATION | GSAP | DOM/Scroll animations |
