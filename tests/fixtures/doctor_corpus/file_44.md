# apprise — Universal Notification Library
# D:\Repositories\apprise\CLAUDE.md

## What This Is
Universal notification library. Send notifications to 80+ services from a single API.
Slack, Discord, Telegram, Email, SMS, Pushover, Gotify, Ntfy, Matrix, Teams, Webhooks,
and many more. Python library and CLI tool. URL-based configuration — one URL per
service. Batch notifications to multiple services. Attachment support. Docker image
for standalone use.

## When to Load This
- Send notifications to multiple services simultaneously
- Quick notification setup without per-service SDKs
- Script and cron job notifications
- Alert routing to multiple channels
- Self-hosted notification gateway
- Monitoring alert delivery (Uptime Kuma, Netdata)
- CI/CD pipeline notifications

---

## CORE API

### CLI Usage
```bash
pip install apprise

# Slack
apprise -t "Alert" -b "Server is down" \
  "slack://TokenA/TokenB/TokenC/#channel"

# Discord
apprise -t "Build Complete" -b "Build #123 passed" \
  "discord://WebhookID/WebhookToken"

# Telegram
apprise -t "Alert" -b "Database backup failed" \
  "tgram://BotToken/ChatID"

# Email
apprise -t "Report" -b "Monthly report attached" \
  "mailto://user:pass@smtp.gmail.com?to=admin@example.com"

# Multiple services at once
apprise -t "Critical" -b "Server unreachable" \
  "slack://TokenA/TokenB/TokenC/#alerts" \
  "tgram://BotToken/ChatID" \
  "mailto://user:pass@smtp.gmail.com"
```

### Python API
```python
import apprise

apobj = apprise.Apprise()

# Add multiple notification services
apobj.add('slack://TokenA/TokenB/TokenC/#alerts')
apobj.add('discord://WebhookID/WebhookToken')
apobj.add('tgram://BotToken/ChatID')
apobj.add('mailto://user:pass@smtp.gmail.com')

# Send to all
apobj.notify(
    title='Server Alert',
    body='CPU usage above 95%',
    notify_type=apprise.NotifyType.WARNING,
)
```

### Configuration File
```yaml
# /etc/apprise/apprise.yml
urls:
  - slack://TokenA/TokenB/TokenC/#alerts:
    - tag: devops
  - discord://WebhookID/WebhookToken:
    - tag: devops, team
  - tgram://BotToken/ChatID:
    - tag: critical
  - mailto://user:pass@smtp.gmail.com:
    - tag: email

# Send to specific tags
# apprise -t "Alert" -b "Message" --tag=critical --config=/etc/apprise/apprise.yml
```

### Docker (Standalone API)
```bash
docker run -d -p 8000:8000 \
  -v /etc/apprise:/config \
  caronc/apprise:latest

# REST API
curl -X POST http://localhost:8000/notify \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["slack://TokenA/TokenB/TokenC/#alerts"],
    "title": "Alert",
    "body": "Something happened"
  }'
```

### Supported Services (Selection)
| Category | Services |
|---|---|
| Chat | Slack, Discord, Teams, Matrix, Mattermost, Rocket.Chat |
| Messaging | Telegram, WhatsApp (via Twilio), Signal |
| Push | Pushover, Pushbullet, Gotify, Ntfy, SimplePush |
| Email | SMTP, Gmail, Outlook, SES, Mailgun |
| SMS | Twilio, Vonage, Sinch, AWS SNS |
| Monitoring | PagerDuty, Opsgenie, VictorOps |
| Custom | Webhooks (JSON/XML/Form), Custom scripts |

### Hono Integration
```typescript
import { Hono } from 'hono'

// Use Apprise Docker API as notification backend
async function notify(title: string, body: string, tags?: string[]) {
  await fetch('http://apprise:8000/notify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      urls: process.env.APPRISE_URLS!.split(','),
      title, body,
      type: 'warning',
    }),
  })
}

app.post('/api/alert', async (c) => {
  const { message } = await c.req.json()
  await notify('System Alert', message)
  return c.json({ sent: true })
})
```

---

## SELF-HEALING

| Error | Fix |
|---|---|
| Service not found | Check URL scheme — see docs for correct format |
| Auth failed | Verify tokens/credentials in URL |
| Email not sending | Check SMTP credentials and port |
| Rate limited | Add delays between batch notifications |
| Docker API 404 | Ensure Apprise container is running |

## ANTI-PATTERNS

- Do NOT use Apprise for complex notification workflows — use Novu
- Do NOT hardcode URLs in scripts — use config files
- Do NOT send to all services for every event — use tags for routing
- Do NOT expose Apprise API without authentication
- Do NOT skip attachment limits — check per-service limits

---

## INTEGRATION POINTS — CROSS-DEPARTMENT ROUTING

| Department | Repo | Relationship |
|---|---|---|
| OBSERVE | uptime-kuma | Apprise as notification backend for Kuma |
| OBSERVE | netdata | Apprise for Netdata alert delivery |
| INTEGRATION | novu | Alternative: Novu for multi-channel with preferences |
| INTEGRATION | ntfy | Ntfy is one of 80+ Apprise backends |
| INFRA | compose | Docker Compose for Apprise API |

## OUTPUT CONTRACT
Delivers: Universal notification delivery to 80+ services.
Install: `pip install apprise`
Docker: `docker pull caronc/apprise`
Docs: github.com/caronc/apprise/wiki

## URL FORMATS (Selection)

| Service | URL Format |
|---|---|
| Slack | `slack://TokenA/TokenB/TokenC/#channel` |
| Discord | `discord://WebhookID/WebhookToken` |
| Telegram | `tgram://BotToken/ChatID` |
| Email | `mailto://user:pass@smtp.host` |
| Ntfy | `ntfy://topic` or `ntfys://topic` |
| Gotify | `gotify://host/token` |
| PagerDuty | `pagerduty://IntegrationKey` |
| Pushover | `pover://UserKey@AppToken` |
| Webhook | `json://host/path` or `xml://host/path` |

## NOTIFICATION TYPES

| Type | Usage |
|---|---|
| `info` | General information |
| `success` | Successful operations |
| `warning` | Warnings and alerts |
| `failure` | Errors and failures |

## BATCH NOTIFICATIONS

```bash
# Send same alert to all services in config
apprise --config=/etc/apprise/apprise.yml \
  --tag=critical \
  -t "CRITICAL" -b "Database down"
```
