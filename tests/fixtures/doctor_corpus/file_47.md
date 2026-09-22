# arcjet-js — Runtime Security Protection
# D:\Repositories\arcjet-js\CLAUDE.md

## What This Is
Runtime security layer for JavaScript applications. Rate limiting (fixed window, sliding
window, token bucket), bot detection and blocking, email validation (disposable check,
MX records, typo detection), and Shield attack protection. Works as middleware for
Next.js, Express, Hono, SvelteKit, Bun, Node.js. Deployed as an edge service — decisions
made at the edge in <1ms. API abuse prevention, signup spam blocking, and DDoS mitigation.

## When to Load This
- Need rate limiting on API endpoints
- Bot detection and blocking
- Email validation (disposable email detection, typo correction)
- Signup spam prevention
- API abuse protection
- DDoS mitigation at the application layer
- Login brute-force protection
- Form submission protection

---

## CORE API

### Rate Limiting
```typescript
import arcjet, { fixedWindow, slidingWindow, tokenBucket } from '@arcjet/next'

// Fixed window — X requests per time window
const aj = arcjet({
  key: process.env.ARCJET_KEY!,
  rules: [
    fixedWindow({
      mode: 'LIVE',     // 'LIVE' blocks, 'DRY_RUN' logs only
      max: 100,
      window: '1m',     // 100 requests per minute
    }),
  ],
})

// Sliding window — smoother rate limiting
const aj = arcjet({
  key: process.env.ARCJET_KEY!,
  rules: [
    slidingWindow({
      mode: 'LIVE',
      max: 60,
      interval: '60s',
    }),
  ],
})

// Token bucket — burst-friendly rate limiting
const aj = arcjet({
  key: process.env.ARCJET_KEY!,
  rules: [
    tokenBucket({
      mode: 'LIVE',
      capacity: 10,         // Max burst
      interval: '10s',
      refillRate: 5,         // 5 tokens per interval
    }),
  ],
})
```

### Bot Detection
```typescript
import arcjet, { detectBot } from '@arcjet/next'

const aj = arcjet({
  key: process.env.ARCJET_KEY!,
  rules: [
    detectBot({
      mode: 'LIVE',
      allow: ['CATEGORY:SEARCH_ENGINE'],  // Allow Google, Bing crawlers
      // block: ['CATEGORY:AI_SCRAPER']   // Block AI scrapers
    }),
  ],
})
```

### Email Validation
```typescript
import arcjet, { validateEmail } from '@arcjet/next'

const aj = arcjet({
  key: process.env.ARCJET_KEY!,
  rules: [
    validateEmail({
      mode: 'LIVE',
      deny: ['DISPOSABLE', 'NO_MX_RECORDS'],
      // Blocks: temp-mail.org, guerrillamail.com, etc.
      // Also detects typos: gmial.com → gmail.com
    }),
  ],
})
```

### Shield (Attack Protection)
```typescript
import arcjet, { shield } from '@arcjet/next'

const aj = arcjet({
  key: process.env.ARCJET_KEY!,
  rules: [
    shield({ mode: 'LIVE' }),
    // Blocks: SQL injection attempts, XSS probes, path traversal
  ],
})
```

### Combined Rules (recommended)
```typescript
const aj = arcjet({
  key: process.env.ARCJET_KEY!,
  rules: [
    shield({ mode: 'LIVE' }),
    detectBot({ mode: 'LIVE', allow: ['CATEGORY:SEARCH_ENGINE'] }),
    fixedWindow({ mode: 'LIVE', max: 100, window: '1m' }),
  ],
})
```

---

## FRAMEWORK INTEGRATION

### Next.js
```typescript
import { NextRequest, NextResponse } from 'next/server'
import arcjet from '@arcjet/next'

export async function POST(req: NextRequest) {
  const decision = await aj.protect(req)
  if (decision.isDenied()) {
    return NextResponse.json({ error: 'Blocked' }, { status: 429 })
  }
  // Process request...
}
```

### Hono
```typescript
import arcjet from '@arcjet/node'

app.post('/api/signup', async (c) => {
  const decision = await aj.protect(c.req.raw)
  if (decision.isDenied()) {
    return c.json({ error: 'Rate limited' }, 429)
  }
  // Process signup...
})
```

### Express
```typescript
import arcjet from '@arcjet/node'

app.post('/api/login', async (req, res) => {
  const decision = await aj.protect(req)
  if (decision.isDenied()) {
    return res.status(429).json({ error: 'Too many attempts' })
  }
  // Process login...
})
```

---

## COMMON RECIPES

### Login brute-force protection
```typescript
const loginLimiter = arcjet({
  key: process.env.ARCJET_KEY!,
  rules: [
    fixedWindow({ mode: 'LIVE', max: 5, window: '15m' }),  // 5 attempts per 15 min
    shield({ mode: 'LIVE' }),
  ],
})
```

### API endpoint protection
```typescript
const apiProtection = arcjet({
  key: process.env.ARCJET_KEY!,
  rules: [
    tokenBucket({ mode: 'LIVE', capacity: 20, interval: '1m', refillRate: 10 }),
    detectBot({ mode: 'LIVE', allow: [] }),  // Block all bots
    shield({ mode: 'LIVE' }),
  ],
})
```

### Signup spam prevention
```typescript
const signupProtection = arcjet({
  key: process.env.ARCJET_KEY!,
  rules: [
    fixedWindow({ mode: 'LIVE', max: 3, window: '1h' }),  // 3 signups per hour per IP
    validateEmail({ mode: 'LIVE', deny: ['DISPOSABLE', 'NO_MX_RECORDS'] }),
    detectBot({ mode: 'LIVE' }),
    shield({ mode: 'LIVE' }),
  ],
})
```

---

## SELF-HEALING

| Error | Fix |
|---|---|
| `ARCJET_KEY` undefined | Set env var from Arcjet dashboard |
| Rate limit too aggressive | Increase `max` or decrease `window` |
| Legitimate bot blocked | Add bot category to `allow` list |
| Good emails rejected | Check MX records; may be new domain |
| Decision always ALLOW | Check `mode: 'LIVE'` not `'DRY_RUN'` |

---

## ANTI-PATTERNS

- Do NOT hardcode ARCJET_KEY — use environment variables
- Do NOT use DRY_RUN in production — switch to LIVE
- Do NOT skip rate limiting on auth endpoints — most critical protection point
- Do NOT rate limit health check endpoints — they need to always respond
- Do NOT block all bots — allow search engines for SEO

---

## INTEGRATION POINTS — CROSS-DEPARTMENT ROUTING

| Department | Repo | Relationship |
|---|---|---|
| SECURITY | helmet | Helmet for headers; Arcjet for active runtime protection |
| SECURITY | security guidance | Security guidance for code; Arcjet for runtime |
| SECURITY | unkey | Complement: Unkey for API keys; Arcjet for abuse protection |
| BACKEND | hono | Arcjet middleware for Hono routes |
| SECURITY | better-auth | Protect auth endpoints with rate limiting + bot detection |

## CROSS-WORKFLOW HOOKS

### API protection setup
1. Get API key from app.arcjet.com
2. Set `ARCJET_KEY` env var
3. Create protection rules: shield + detectBot + rateLimit
4. Apply to sensitive endpoints (login, signup, API)
5. Monitor decisions in Arcjet dashboard
6. Tune rules based on real traffic patterns

## OUTPUT CONTRACT
Delivers: Runtime security protection — rate limiting, bot detection, email validation.
Install: `npm install @arcjet/next` (or `@arcjet/node`, `@arcjet/bun`)
Docs: docs.arcjet.com
