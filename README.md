QuantumFingerprint — AI Service Layer

This small Node.js + TypeScript project implements an AI service layer for QuantumFingerprint.

Features
- Receives: cryptographic key, entropy score, randomness metrics, artwork metadata
- Produces: explanation of randomness quality, security implications, uniqueness description, and a human-readable report
- Uses Groq API (configurable model via `GROQ_MODEL`, default `llama3-8b-8192`)

Quick start

1. Install:

```bash
npm install
```

2. Set `GROQ_API_KEY` in your environment (and optionally `GROQ_MODEL`). Get a free API key at https://console.groq.com

3. Run example CLI:

```bash
npm run dev
```

Files
- src/models/types.ts — domain types and DTOs
- src/infra/groqClient.ts — small wrapper around Groq
- src/services/ai/AIService.ts — core AI service layer
- src/controllers/reportController.ts — convenient controller entry
- src/cli.ts — example usage

Notes
- This is a focused service layer; integrate into your app by calling `generateReport()` from `reportController`.
- The project supports mock mode via `OPENAI_MOCK=1` environment variable for testing without API calls.