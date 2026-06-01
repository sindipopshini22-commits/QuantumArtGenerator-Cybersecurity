QuantumFingerprint — AI Service Layer

This small Node.js + TypeScript project implements an AI service layer for QuantumFingerprint.

Features
- Receives: cryptographic key, entropy score, randomness metrics, artwork metadata
- Produces: explanation of randomness quality, security implications, uniqueness description, and a human-readable report
- Uses OpenAI API (configurable model via `OPENAI_MODEL`, default `gpt-5-mini`)

Quick start

1. Install:

```bash
npm install
```

2. Set `OPENAI_API_KEY` in your environment (and optionally `OPENAI_MODEL`).

3. Run example CLI:

```bash
npm run dev
```

Files
- src/models/types.ts — domain types and DTOs
- src/infra/openaiClient.ts — small wrapper around OpenAI
- src/services/ai/AIService.ts — core AI service layer
- src/controllers/reportController.ts — convenient controller entry
- src/cli.ts — example usage

Notes
- This is a focused service layer; integrate into your app by calling `generateReport()` from `reportController`.
