# ai — Vercel AI SDK
# D:\Repositories\ai\CLAUDE.md

## What This Is
Vercel AI SDK. Build AI-powered applications with React, Next.js, and any LLM provider.
Unified LLM API: OpenAI, Anthropic, Google, Mistral, Cohere, AWS Bedrock, Azure.
Streaming UI primitives: useChat, useCompletion, useObject, useAssistant. AI SDK Core:
generateText, streamText, generateObject, streamObject. Tool calling with typed schemas.
Structured output via Zod. Multi-step agent workflows. RAG helpers. Middleware.
Edge runtime compatible.

## When to Load This
- Building AI-powered chat UIs
- Streaming LLM responses in React/Next.js
- Multi-provider LLM abstraction (switch providers without code changes)
- Structured AI output (JSON, typed objects)
- Tool calling with typed schemas
- Multi-step agent workflows
- RAG integration in applications

---

## CORE API

### Server: generateText / streamText
```typescript
import { generateText, streamText } from 'ai'
import { openai } from '@ai-sdk/openai'
import { anthropic } from '@ai-sdk/anthropic'
import { google } from '@ai-sdk/google'

// Generate text (non-streaming)
const { text } = await generateText({
  model: openai('gpt-4o'),
  prompt: 'Explain TypeScript generics in one paragraph.',
})

// Stream text (recommended for chat UX)
const result = streamText({
  model: anthropic('claude-sonnet-4-20250514'),
  messages: [
    { role: 'system', content: 'You are a helpful assistant.' },
    { role: 'user', content: 'Explain React hooks.' },
  ],
})

// Return as streaming response (Hono/Next.js/Express)
return result.toDataStreamResponse()
```

### Server: generateObject / streamObject
```typescript
import { generateObject, streamObject } from 'ai'
import { z } from 'zod'

// Structured output with Zod schema
const { object } = await generateObject({
  model: openai('gpt-4o'),
  schema: z.object({
    recipe: z.string(),
    ingredients: z.array(z.object({
      name: z.string(),
      amount: z.string(),
    })),
    steps: z.array(z.string()),
    prepTime: z.number().describe('Preparation time in minutes'),
  }),
  prompt: 'Generate a pasta carbonara recipe',
})
// object is fully typed!

// Stream structured output
const result = streamObject({
  model: openai('gpt-4o'),
  schema: z.object({ title: z.string(), summary: z.string() }),
  prompt: 'Summarize the concept of microservices',
})
for await (const partial of result.partialObjectStream) {
  console.log(partial)  // Partial object as it streams
}
```

### Tool Calling
```typescript
import { generateText, tool } from 'ai'
import { z } from 'zod'

const { text, toolResults } = await generateText({
  model: openai('gpt-4o'),
  tools: {
    weather: tool({
      description: 'Get weather for a location',
      parameters: z.object({
        city: z.string(),
        unit: z.enum(['celsius', 'fahrenheit']).default('celsius'),
      }),
      execute: async ({ city, unit }) => {
        const data = await fetchWeather(city, unit)
        return { temperature: data.temp, conditions: data.conditions }
      },
    }),
    calculator: tool({
      description: 'Calculate a math expression',
      parameters: z.object({ expression: z.string() }),
      execute: async ({ expression }) => ({ result: eval(expression) }),
    }),
  },
  maxSteps: 5,  // Allow multi-step tool use
  prompt: 'What is the weather in Tokyo? Convert the temperature to Fahrenheit.',
})
```

### Client: useChat (React)
```tsx
'use client'
import { useChat } from 'ai/react'

export function Chat() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
  })

  return (
    <div>
      {messages.map(m => (
        <div key={m.id} className={m.role === 'user' ? 'user' : 'assistant'}>
          {m.content}
        </div>
      ))}
      <form onSubmit={handleSubmit}>
        <input value={input} onChange={handleInputChange} placeholder="Ask me anything..." />
        <button type="submit" disabled={isLoading}>Send</button>
      </form>
    </div>
  )
}
```

### Client: useObject (Streaming Structured Output)
```tsx
import { useObject } from 'ai/react'
import { z } from 'zod'

const schema = z.object({
  notifications: z.array(z.object({
    title: z.string(),
    message: z.string(),
    priority: z.enum(['low', 'medium', 'high']),
  })),
})

export function Notifications() {
  const { object, submit, isLoading } = useObject({ api: '/api/notifications', schema })

  return (
    <div>
      <button onClick={() => submit('Generate 5 sample notifications')}>Generate</button>
      {object?.notifications?.map((n, i) => (
        <div key={i}>{n.title}: {n.message}</div>
      ))}
    </div>
  )
}
```

### Hono API Route
```typescript
import { Hono } from 'hono'
import { streamText } from 'ai'
import { openai } from '@ai-sdk/openai'

const app = new Hono()

app.post('/api/chat', async (c) => {
  const { messages } = await c.req.json()
  const result = streamText({
    model: openai('gpt-4o'),
    messages,
  })
  return result.toDataStreamResponse()
})
```

---

## PROVIDERS

| Provider | Package | Models |
|---|---|---|
| OpenAI | `@ai-sdk/openai` | gpt-4o, gpt-4o-mini, o1, o3 |
| Anthropic | `@ai-sdk/anthropic` | claude-sonnet-4-20250514, claude-3-5-haiku |
| Google | `@ai-sdk/google` | gemini-2.0-flash, gemini-pro |
| Mistral | `@ai-sdk/mistral` | mistral-large, mistral-small |
| Cohere | `@ai-sdk/cohere` | command-r-plus |
| Amazon Bedrock | `@ai-sdk/amazon-bedrock` | Claude, Llama, Titan |
| Azure OpenAI | `@ai-sdk/azure` | Deployed models |

---

## SELF-HEALING

| Error | Fix |
|---|---|
| Provider not found | Install provider package: `npm install @ai-sdk/openai` |
| Streaming fails | Ensure route returns `result.toDataStreamResponse()` |
| Tool call errors | Verify Zod schema matches tool parameters |
| Rate limited | Switch provider or add retry middleware |
| Object schema mismatch | Simplify schema — complex nested schemas may fail |

---

## ANTI-PATTERNS

- Do NOT use raw fetch to LLM APIs — use AI SDK for unified interface
- Do NOT block on generateText for chat — use streamText for UX
- Do NOT hardcode provider — use provider registry for flexibility
- Do NOT skip Zod schemas for structured output — they ensure type safety
- Do NOT use AI SDK for simple completions — direct API may be simpler

---

## INTEGRATION POINTS — CROSS-DEPARTMENT ROUTING

| Department | Repo | Relationship |
|---|---|---|
| AI | langchainjs | Alternative: LangChain for chains; AI SDK for streaming UI |
| AI | instructor-js | Alternative for structured output |
| AI | mastra | Mastra uses AI SDK under the hood |
| PLATFORM | zod | Schema definitions for tools and structured output |
| BACKEND | hono | AI SDK API routes in Hono |
| DATA | pgvector / chroma | Vector stores for RAG pipelines |

## OUTPUT CONTRACT
Delivers: AI-powered application with streaming UI, tool calling, and multi-provider support.
Install: `npm install ai @ai-sdk/openai`
Docs: sdk.vercel.ai/docs