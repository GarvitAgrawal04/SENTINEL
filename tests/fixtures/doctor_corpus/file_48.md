# astro — Content-Driven Web Framework
# D:\Repositories\astro\CLAUDE.md

## What This Is
Web framework for content-driven websites. Islands architecture — ship zero JS by
default, hydrate interactive components on demand. Supports React, Vue, Svelte, Solid,
Preact components in the same project. Built-in Markdown and MDX support. File-based
routing. SSG and SSR. Content collections with type safety. View transitions.
Image optimization. Extremely fast builds.

## When to Load This
- Content-driven websites (blogs, docs, marketing)
- Static site generation with partial hydration
- Multi-framework components (React + Vue + Svelte)
- Markdown/MDX content sites
- Performance-critical landing pages
- Documentation sites
- Portfolio sites with minimal JS

---

## CORE API

### Setup
```bash
npm create astro@latest my-site
cd my-site
npm run dev  # http://localhost:4321
```

### Pages (File-Based Routing)
```astro
---
// src/pages/index.astro
import Layout from '../layouts/Layout.astro'
import Card from '../components/Card.astro'

const posts = await Astro.glob('./blog/*.md')
---
<Layout title="Home">
  <h1>Welcome</h1>
  {posts.map(post => <Card title={post.frontmatter.title} href={post.url} />)}
</Layout>
```

### Components
```astro
---
// src/components/Card.astro
interface Props { title: string; href: string; body?: string }
const { title, href, body } = Astro.props
---
<a href={href} class="card">
  <h2>{title}</h2>
  {body && <p>{body}</p>}
</a>

<style>
  .card {
    padding: 1.5rem;
    border-radius: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: transform 0.2s;
  }
  .card:hover { transform: translateY(-4px); }
</style>
```

### Content Collections
```typescript
// src/content/config.ts
import { defineCollection, z } from 'astro:content'

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.date(),
    tags: z.array(z.string()),
    draft: z.boolean().default(false),
    image: z.string().optional(),
  }),
})

export const collections = { blog }
```

```astro
---
// src/pages/blog/[...slug].astro
import { getCollection } from 'astro:content'

export async function getStaticPaths() {
  const posts = await getCollection('blog', ({ data }) => !data.draft)
  return posts.map(post => ({ params: { slug: post.slug }, props: { post } }))
}

const { post } = Astro.props
const { Content } = await post.render()
---
<Layout title={post.data.title}>
  <h1>{post.data.title}</h1>
  <Content />
</Layout>
```

### Islands (Partial Hydration)
```astro
---
import ReactCounter from '../components/Counter.tsx'
import VueWidget from '../components/Widget.vue'
---
<!-- No JS shipped by default -->
<h1>Static content</h1>

<!-- Hydrate on page load -->
<ReactCounter client:load />

<!-- Hydrate when visible -->
<VueWidget client:visible />

<!-- Hydrate on idle -->
<ReactCounter client:idle />

<!-- Hydrate on media query -->
<VueWidget client:media="(max-width: 768px)" />

<!-- Never hydrate (SSR only) -->
<ReactCounter />
```

### View Transitions
```astro
---
import { ViewTransitions } from 'astro:transitions'
---
<html>
  <head>
    <ViewTransitions />
  </head>
  <body transition:animate="slide">
    <nav transition:persist>...</nav>
    <main transition:animate="fade">
      <slot />
    </main>
  </body>
</html>
```

### API Routes
```typescript
// src/pages/api/hello.ts
import type { APIRoute } from 'astro'

export const GET: APIRoute = async ({ params, request }) => {
  return new Response(JSON.stringify({ message: 'Hello!' }), {
    headers: { 'Content-Type': 'application/json' },
  })
}
```

### Integrations
| Integration | Install | Purpose |
|---|---|---|
| @astrojs/react | `npx astro add react` | React components |
| @astrojs/vue | `npx astro add vue` | Vue components |
| @astrojs/svelte | `npx astro add svelte` | Svelte components |
| @astrojs/tailwind | `npx astro add tailwind` | Tailwind CSS |
| @astrojs/mdx | `npx astro add mdx` | MDX support |
| @astrojs/sitemap | `npx astro add sitemap` | Auto sitemap |
| @astrojs/vercel | `npx astro add vercel` | Vercel deployment |
| @astrojs/node | `npx astro add node` | Node.js SSR |

---

## DECISION: Astro vs Next.js vs Nuxt

| Feature | Astro | Next.js | Nuxt |
|---|---|---|---|
| Zero JS default | ✅ | ❌ | ❌ |
| Multi-framework | ✅ | ❌ React only | ❌ Vue only |
| Content collections | ✅ Built-in | ❌ | ✅ |
| View transitions | ✅ Built-in | ❌ | ❌ |
| App complexity | Content sites | Full apps | Full apps |
| SSR | ✅ | ✅ | ✅ |
| Best for | Content + perf | React apps | Vue apps |

---

## SELF-HEALING

| Error | Fix |
|---|---|
| Component not rendering | Check `client:*` directive for hydration |
| Content collection error | Verify schema matches frontmatter |
| Build failing | Check for SSR-only APIs in static paths |
| Styles not applying | Use `<style>` in `.astro` files (scoped by default) |
| View transitions broken | Ensure `<ViewTransitions />` in head |

## ANTI-PATTERNS

- Do NOT use Astro for highly interactive SPAs — use Next.js
- Do NOT forget `client:*` directives — component won't hydrate
- Do NOT import CSS frameworks globally — use scoped styles
- Do NOT put runtime JS in `.astro` files — use framework components
- Do NOT skip content collections for structured content

---

## INTEGRATION POINTS — CROSS-DEPARTMENT ROUTING

| Department | Repo | Relationship |
|---|---|---|
| FRONTEND | next.js | Alternative: Next.js for React SPAs |
| CMS | keystatic | Keystatic as CMS for Astro |
| CMS | Ghost | Ghost as headless CMS for Astro |
| DOCS | fumadocs | Alternative: Fumadocs for Next.js docs |
| ANIMATION | GSAP | GSAP animations in Astro components |
| ANALYTICS | plausible-analytics | Plausible tracking script |

## OUTPUT CONTRACT
Delivers: Content-driven web framework with islands architecture.
Install: `npm create astro@latest`
Docs: docs.astro.build
