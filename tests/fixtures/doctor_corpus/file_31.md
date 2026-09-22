# Plausible Analytics — Privacy-First Web Analytics
# D:\Repositories\analytics\CLAUDE.md
# NOTE: This directory is Plausible Analytics (alias: plausible-analytics)

## What This Is
Open-source, privacy-first web analytics. Lightweight alternative to Google Analytics.
No cookies, fully GDPR/CCPA/PECR compliant out of the box. Script is under 1KB.
Simple one-page dashboard. Built with Elixir (Phoenix) and ClickHouse for blazing
performance. Self-hosted community edition or Plausible Cloud. EU-hosted. Tracks
pageviews, sources, devices, locations, conversions, and custom events without
collecting personal data. Trusted by 10,000+ subscribers.

## When to Load This
- Privacy-first website analytics
- GDPR-compliant tracking without cookie banners
- Lightweight alternative to Google Analytics
- Self-hosted analytics platform
- Conversion and goal tracking
- UTM campaign analytics
- Custom event tracking
- Real-time visitor dashboard
- Revenue tracking for e-commerce

---

## CORE SETUP

### Self-Hosted (Docker Compose)
```yaml
services:
  plausible:
    image: ghcr.io/plausible/community-edition:v2
    ports: ["8000:8000"]
    env_file: plausible-conf.env
    depends_on:
      - plausible_db
      - plausible_events_db

  plausible_db:
    image: postgres:16-alpine
    volumes:
      - db-data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: postgres

  plausible_events_db:
    image: clickhouse/clickhouse-server:24-alpine
    volumes:
      - event-data:/var/lib/clickhouse
    ulimits:
      nofile:
        soft: 262144
        hard: 262144

volumes:
  db-data:
  event-data:
```

### Environment Configuration
```bash
# plausible-conf.env
BASE_URL=https://analytics.example.com
SECRET_KEY_BASE=$(openssl rand -base64 48)
DATABASE_URL=postgres://postgres:postgres@plausible_db:5432/plausible_db
CLICKHOUSE_DATABASE_URL=http://plausible_events_db:8123/plausible_events_db

# Optional: Email
MAILER_EMAIL=analytics@example.com
SMTP_HOST_ADDR=smtp.example.com
SMTP_HOST_PORT=587
SMTP_USER_NAME=user
SMTP_USER_PWD=password
SMTP_HOST_SSL_ENABLED=true

# Optional: Google Search Console integration
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx

# Optional: MaxMind for geolocation
MAXMIND_LICENSE_KEY=xxx
MAXMIND_EDITION=GeoLite2-City
```

### Launch
```bash
docker compose up -d
# Access at http://localhost:8000
# Create admin account on first visit
```

### Tracking Script (Add to Your Site)
```html
<!-- Plausible Analytics — 1KB, no cookies -->
<script defer data-domain="yourdomain.com"
  src="https://analytics.example.com/js/script.js">
</script>
```

### Script Variants
| Variant | File | Purpose |
|---|---|---|
| Default | `script.js` | Basic pageview tracking |
| Hash mode | `script.hash.js` | SPA hash-based routing |
| Outbound links | `script.outbound-links.js` | Track external link clicks |
| File downloads | `script.file-downloads.js` | Track file downloads |
| Tagged events | `script.tagged-events.js` | CSS class-based events |
| Revenue | `script.revenue.js` | E-commerce revenue tracking |
| Pageview props | `script.pageview-props.js` | Custom pageview properties |
| Combined | `script.hash.outbound-links.file-downloads.tagged-events.js` | Multiple extensions |

---

## CUSTOM EVENTS API

### JavaScript Event Tracking
```javascript
// Track custom event
plausible('Signup', { props: { plan: 'Premium', source: 'homepage' } })

// Track form submission
document.getElementById('signup-form').addEventListener('submit', () => {
  plausible('Form Submit', { props: { form: 'newsletter' } })
})

// Track purchase with revenue
plausible('Purchase', {
  revenue: { currency: 'USD', amount: 29.99 },
  props: { product: 'Pro Plan' },
})

// Track outbound link click
plausible('Outbound Link: Click', { props: { url: 'https://example.com' } })

// Track 404 pages
plausible('404', { props: { path: document.location.pathname } })
```

### Next.js Integration
```typescript
// next-plausible
import PlausibleProvider from 'next-plausible'

// app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html>
      <head>
        <PlausibleProvider domain="yourdomain.com" customDomain="https://analytics.example.com" />
      </head>
      <body>{children}</body>
    </html>
  )
}

// Track events in components
import { usePlausible } from 'next-plausible'

function SignupButton() {
  const plausible = usePlausible()
  return (
    <button onClick={() => plausible('Signup', { props: { plan: 'free' } })}>
      Sign Up
    </button>
  )
}
```

### Stats API (v2)
```typescript
// Aggregate stats
const stats = await fetch('https://analytics.example.com/api/v2/query', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${PLAUSIBLE_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    site_id: 'yourdomain.com',
    metrics: ['visitors', 'pageviews', 'bounce_rate', 'visit_duration'],
    date_range: '30d',
  }),
})

// Breakdown by source
const sources = await fetch('https://analytics.example.com/api/v2/query', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${PLAUSIBLE_API_KEY}` },
  body: JSON.stringify({
    site_id: 'yourdomain.com',
    metrics: ['visitors', 'pageviews'],
    date_range: '7d',
    dimensions: ['visit:source'],
    order_by: [['visitors', 'desc']],
    limit: 10,
  }),
})

// Filter by page
const pageStats = await fetch('https://analytics.example.com/api/v2/query', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${PLAUSIBLE_API_KEY}` },
  body: JSON.stringify({
    site_id: 'yourdomain.com',
    metrics: ['visitors', 'pageviews'],
    date_range: '30d',
    dimensions: ['event:page'],
    filters: [['contains', 'event:page', ['/blog']]],
  }),
})

// Realtime visitors
const realtime = await fetch(
  'https://analytics.example.com/api/v1/stats/realtime/visitors?site_id=yourdomain.com',
  { headers: { 'Authorization': `Bearer ${PLAUSIBLE_API_KEY}` } }
)
```

### Hono API Proxy
```typescript
app.get('/api/analytics/visitors', async (c) => {
  const res = await fetch('https://analytics.example.com/api/v2/query', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.PLAUSIBLE_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      site_id: 'yourdomain.com',
      metrics: ['visitors', 'pageviews', 'bounce_rate'],
      date_range: '30d',
    }),
  })
  return c.json(await res.json())
})
```

---

## AVAILABLE METRICS

| Metric | Description |
|---|---|
| `visitors` | Unique visitors |
| `visits` | Total sessions |
| `pageviews` | Total page views |
| `views_per_visit` | Pages per session |
| `bounce_rate` | Single-page visit rate |
| `visit_duration` | Average session duration |
| `events` | Custom event count |
| `conversion_rate` | Goal conversion rate |

## DIMENSIONS

| Dimension | Description |
|---|---|
| `visit:source` | Traffic source (Google, Twitter, etc.) |
| `visit:referrer` | Full referrer URL |
| `visit:utm_medium` | UTM medium parameter |
| `visit:utm_source` | UTM source parameter |
| `visit:utm_campaign` | UTM campaign parameter |
| `visit:country` | Visitor country |
| `visit:city` | Visitor city |
| `visit:device` | Device type (Desktop, Mobile, Tablet) |
| `visit:browser` | Browser name |
| `visit:os` | Operating system |
| `event:page` | Page path |
| `event:name` | Custom event name |

## GOALS AND CONVERSIONS

```
Dashboard → Site Settings → Goals

Goal Types:
1. Pageview goal  → Track visits to specific pages (e.g., /thank-you)
2. Custom event   → Track JS events (e.g., Signup, Purchase)
3. Revenue goal   → Track revenue with currency and amount
```

---

## DECISION: Plausible vs Google Analytics vs Umami

| Feature | Plausible | Google Analytics | Umami |
|---|---|---|---|
| Privacy-first | ✅ No cookies | ❌ Cookies + tracking | ✅ No cookies |
| GDPR compliant | ✅ No consent needed | ❌ Consent required | ✅ |
| Script size | ✅ <1KB | ❌ ~45KB | ✅ ~2KB |
| Dashboard | ✅ Simple one-page | ❌ Complex | ✅ Simple |
| Self-hosted | ✅ | ❌ | ✅ |
| Revenue tracking | ✅ | ✅ | ❌ |
| API | ✅ REST | ✅ | ✅ |
| Cost (cloud) | $9+/mo | Free | Free (self-hosted) |
| Best for | Privacy + simplicity | Full marketing stack | Free self-hosted |

---

## SELF-HEALING

| Error | Fix |
|---|---|
| No data appearing | Verify tracking script domain matches site |
| ClickHouse OOM | Increase Docker memory limits for events DB |
| Geolocation missing | Configure MaxMind GeoLite2 license key |
| Email not sending | Check SMTP configuration in env file |
| API 401 | Generate new API key in site settings |
| Dashboard slow | Check ClickHouse health, increase resources |
| Script blocked | Use custom domain to avoid ad-blocker detection |

## ANTI-PATTERNS

- Do NOT use Google Analytics script alongside Plausible — redundant
- Do NOT track personally identifiable information in custom props
- Do NOT skip setting `BASE_URL` — required for self-hosted
- Do NOT expose API keys in client-side code
- Do NOT use default `SECRET_KEY_BASE` in production
- Do NOT forget to set up automated ClickHouse backups

---

## INTEGRATION POINTS — CROSS-DEPARTMENT ROUTING

| Department | Repo | Relationship |
|---|---|---|
| ANALYTICS | umami | Alternative: Umami for free self-hosted |
| ANALYTICS | posthog | Alternative: PostHog for product analytics |
| FRONTEND | next.js | next-plausible for Next.js integration |
| BACKEND | hono | Stats API proxy through Hono |
| INFRA | compose | Docker Compose deployment |
| INFRA | cloudflared | Expose via Cloudflare Tunnel |
| PRIVACY | klaro | Cookie consent (not needed with Plausible) |

## OUTPUT CONTRACT
Delivers: Privacy-first web analytics with <1KB script and one-page dashboard.
Install: `docker compose up -d` (self-hosted) or plausible.io (cloud)
Script: `<script defer data-domain="site.com" src="https://plausible.io/js/script.js"></script>`
API: `https://plausible.io/api/v2/query`
Docs: plausible.io/docs
