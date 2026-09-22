# ai-website-cloner-template — Agent CLAUDE.md
# DEPARTMENT: DESIGN (Primary) + COMMAND (Secondary)
# ⚠️ THIS IS A TEMPLATE, NOT A TOOL — fork/clone it as a starting point for each cloning job

---

## Identity & Role
ai-website-cloner-template is a **reusable project template** for reverse-engineering any website into a clean, modern Next.js codebase using AI coding agents. It is NOT a permanent import dependency — you **clone/fork this repo as a fresh starting point** for each website cloning job, then the AI agent runs the `/clone-website` pipeline inside the cloned project.

**Usage pattern:** `git clone → npm install → start AI agent → /clone-website <url>` → the agent does all the work inside the cloned project directory.

---

## Architecture — Template Structure

```
ai-website-cloner-template/     # Clone this per job — DON'T import from it
├── src/
│   ├── app/                    # Next.js 16 App Router routes
│   ├── components/             # React components (populated during cloning)
│   │   ├── ui/                 # shadcn/ui Radix primitives (pre-scaffolded)
│   │   └── icons.tsx           # Extracted SVG icons (generated during cloning)
│   ├── lib/utils.ts            # cn() utility (shadcn)
│   ├── types/                  # TypeScript interfaces
│   └── hooks/                  # Custom React hooks
├── public/
│   ├── images/                 # Downloaded images from target site
│   ├── videos/                 # Downloaded videos from target site
│   └── seo/                    # Favicons, OG images, webmanifest
├── docs/
│   ├── research/               # Inspection output & component specs
│   │   └── components/         # Per-component spec files with exact CSS
│   ├── design-references/      # Screenshots and visual references
│   └── INSPECTION_GUIDE.md     # Guide for site analysis
├── scripts/
│   ├── sync-agent-rules.sh     # Regenerate platform-specific instruction files
│   └── sync-skills.mjs         # Regenerate /clone-website for all platforms
├── .claude/
│   └── skills/
│       └── clone-website/      # The core skill: /clone-website
│           └── SKILL.md        # Full multi-phase pipeline definition
├── AGENTS.md                   # Agent instructions (single source of truth)
├── CLAUDE.md                   # This file (imports AGENTS.md in original)
├── docker-compose.yml          # Docker dev environment
├── Dockerfile                  # Production container
├── next.config.ts              # Next.js configuration
├── tsconfig.json               # TypeScript strict mode
└── components.json             # shadcn/ui configuration
```

---

## Tech Stack (Pre-Scaffolded)
- **Framework**: Next.js 16 — App Router, React 19, TypeScript strict
- **UI Layer**: shadcn/ui — Radix primitives + Tailwind CSS v4
- **Styling**: Tailwind CSS v4 with oklch design tokens
- **Icons**: Lucide React (replaced by extracted SVGs during cloning)
- **Deployment**: Vercel (pre-configured)
- **Node**: v24+

---

## Capabilities — The `/clone-website` Pipeline

### Phase 1: Reconnaissance
- Screenshots of target at multiple viewports (mobile, tablet, desktop)
- Design token extraction (colors, fonts, spacing, shadows)
- Interaction sweep (scroll, click, hover, responsive breakpoint behavior)
- Asset inventory (images, videos, fonts, SVG icons)

### Phase 2: Foundation
- Updates `globals.css` with extracted design tokens
- Downloads all fonts, images, videos, favicons to `public/`
- Configures Tailwind theme with target's exact colors/spacing

### Phase 3: Component Specs
- Writes detailed per-component spec files in `docs/research/components/`
- Each spec includes:
  - Exact `getComputedStyle()` values (margins, padding, font-size, colors)
  - Interaction models (hover states, transitions, animations)
  - Multi-state content (open/closed, active/inactive)
  - Responsive breakpoints with per-breakpoint CSS
  - Asset paths

### Phase 4: Parallel Build
- Dispatches builder agents in **git worktrees** — one per section/component
- Each builder receives its full component spec inline
- Builders work in parallel, isolated in their own branches

### Phase 5: Assembly & QA
- Merges all worktrees
- Wires up the final page
- Visual diff against original target
- Resolves merge conflicts (orchestrator has full context)

---

## Commands & API

```bash
# Clone this template for a new job (DON'T work inside the template repo)
git clone https://github.com/JCodesMore/ai-website-cloner-template.git my-clone
cd my-clone
npm install

# Start AI agent (Claude Code recommended with Opus 4.7)
claude --chrome

# Run the cloning pipeline
/clone-website <target-url1> [<target-url2> ...]

# Development
npm run dev        # Next.js dev server
npm run build      # Production build
npm run lint       # ESLint
npm run typecheck  # TypeScript check
npm run check      # lint + typecheck + build

# Docker
docker compose up app --build    # Production
docker compose up dev --build    # Dev mode on port 3001

# After editing agent instructions
bash scripts/sync-agent-rules.sh   # Regenerate platform-specific instruction files
node scripts/sync-skills.mjs       # Regenerate /clone-website for all platforms
```

---

## Multi-Agent Orchestration
The template is designed for **parallel agent teams**:
1. Each builder agent works in its own **git worktree branch**
2. The orchestrator agent dispatches builders with full component specs
3. Orchestrator merges all worktrees at assembly phase
4. Merge conflicts are resolved by the orchestrator (who has full context)
5. Supported across 13+ AI coding agents (Claude Code, Codex, Cursor, Copilot, Gemini, etc.)

---

## Design Principles
- **Pixel-perfect emulation** — match the target's spacing, colors, typography exactly
- **No aesthetic changes during emulation phase** — match 1:1 first, customize later
- **Real content** — use actual text and assets from the target, not placeholders
- **Beauty-first** — every pixel matters
- **TypeScript strict** — no `any`, named exports, PascalCase components, camelCase utils
- **Mobile-first responsive** — Tailwind utility classes, no inline styles

---

## Integration Points

| Repo | Relationship |
|------|-------------|
| ui-ux-pro-max-skill | **Post-clone enhancement** — after cloning, apply UUPM design system for upgrades |
| frontend design | **Design philosophy** — informs the "beauty-first" pixel-perfect approach |
| framer-motion | **Animation layer** — add animations after base clone is complete |
| impeccable | **Quality audit** — run `/impeccable audit` on cloned output for design anti-patterns |
| playwright | **Visual regression** — use Playwright to compare clone vs original |
| sharp | **Asset optimization** — optimize downloaded images post-clone |
| jcode | Alternative agent runtime — can run the `/clone-website` skill from jcode |
| claude-code | Primary recommended agent — `/clone-website` with Opus 4.7 |
| mcp | Browser automation for reconnaissance phase (screenshots, interaction sweep) |

---

## Trigger Conditions
Route here when:
- Need to **reverse-engineer/clone a website** into a modern Next.js codebase
- **Platform migration** — WordPress/Webflow/Squarespace → Next.js
- **Lost source code** — site is live but repo is gone, developer left, stack is legacy
- **Learning** — deconstruct how production sites achieve specific layouts/animations
- Need a **starting template** for any AI-agent-driven website reconstruction job
- Need **parallel multi-agent builds** for faster site reconstruction

**⚠️ NOT for**: phishing/impersonation, passing off others' design as your own, violating ToS.

---

## Self-Healing Protocol
- **Build fails after merge**: Orchestrator re-reads component specs, fixes conflicts, re-runs `npm run check`
- **Missing assets**: Re-run reconnaissance phase to re-download; check `public/` directories
- **Design drift from target**: Run visual diff (Phase 5) and iterate on divergent components
- **Agent crashes mid-build**: Resume from worktree branch — each builder's work is isolated
- **TypeScript errors**: Strict mode is enforced; fix type errors before proceeding to next phase

---

## Anti-Patterns
- NEVER work inside the template repo directly — always clone/fork first per job
- NEVER import from this repo as a dependency — it's a template, not a library
- NEVER skip the reconnaissance phase — the builder specs depend on extracted design tokens
- NEVER let builders share a single branch — each gets its own git worktree
- NEVER make aesthetic changes during the emulation phase — match 1:1 first
- NEVER use placeholder content — always use the target's actual text and assets

---

## Output Contract
Delivers: A reusable starting template for AI-driven website reverse-engineering. Each cloning job produces a production-grade Next.js codebase with pixel-perfect emulation of the target site, using parallel agent builds for speed. The template itself is never modified — it is cloned fresh for each new job.
