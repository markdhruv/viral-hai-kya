# Viral Hai Kya

**Know if your campaign will land — before you spend a rupee.**

Paste a campaign message, pick what you are actually trying to achieve, and get a
scored read on it: emotion, clarity, trend relevance, shareability and CTA strength,
weighted into a single confidence score with a recommendation.

> **Live demo:** _add your Vercel URL here_

---

## Why the scoring works this way

Most "AI copy checkers" grade a message in a vacuum. That is the wrong question.
A line that is perfect for a loyalty email is a bad line for a conversion ad.

So every message is scored **against a stated objective**, and the objective changes
what counts as good:

| Objective | What the model rewards |
|---|---|
| **Create Awareness** | Simple, catchy, strong emotional hook. Memorability over detail. |
| **Drive Consideration** | Informative, benefit-led, trustworthy. Hype is penalised. |
| **Drive Sales** | Urgency, scarcity, an unmistakable CTA. A passive tone is a fail. |
| **Build Loyalty** | Warmth, gratitude, exclusivity. Selling hard is penalised. |

Six scores are produced, each 1–5:

| Score | What it measures |
|---|---|
| **Objective fit** | Does this serve the stated goal? The most heavily weighted score. |
| **Clarity & impact** | Active voice, strong verbs, no jargon. |
| **Emotion** | Raw emotional charge, independent of intent. |
| **CTA strength** | Is the ask clear, urgent and persuasive? |
| **Trend relevance** | Does it connect to the keywords that matter right now? |
| **Shareability** | Social pass-along potential (emotional hook, practical value). |

They combine into the confidence score using these weights:

```
Objective fit     0.25     Objective fit is weighted highest because a
Clarity & impact  0.20     technically good message aimed at the wrong
Emotion           0.20     goal still fails. Trend relevance and
CTA strength      0.15     shareability are weighted lowest because they
Trend relevance   0.10     are the most situational — a B2B renewal email
Shareability      0.10     is not supposed to go viral.
```

- **≥ 4.0** ✅ Strong potential to succeed
- **3.0 – 3.9** ⚠️ Good, but revise key elements
- **< 3.0** ❌ Needs rework before launch

## An honest limitation

This is a **structured second opinion, not a prediction.** The scores come from a
language model reasoning about copy, not from performance data, so nothing here is
validated against real campaign outcomes.

What it is genuinely good for: catching vague CTAs, spotting a tone that fights the
objective, and forcing a decision about what a campaign is actually for before it
ships. Treat a low score as a prompt to look harder, not as a verdict.

## Using it

1. Pick your **marketing objective**.
2. Optionally add **audience, brand tone and your key message** for a sharper read.
3. Type your **campaign messages** (one per line), **keywords** and **CTAs**.
4. Hit **Run Analysis**, then export to CSV.

Analysing many messages at once? Upload `.xlsx` files instead — there is a template
download next to each upload box.

## Running it locally

**Prerequisites:** Node.js 18+ and a free [Gemini API key](https://aistudio.google.com/apikey).

```bash
npm install
cp .env.example .env.local   # then paste your key into .env.local
npm run dev
```

Open http://localhost:3000.

`.env.local` is git-ignored — your key never leaves your machine.

## Deploying

```bash
npx vercel
```

Then set `GEMINI_API_KEY` in **Vercel → Settings → Environment Variables**, and
`npx vercel --prod`.

Because a public deployment runs on the owner's API quota, the server limits each
visitor to **15 analyses per day** and **10 messages per request**. Both are constants
at the top of `api/analyze.ts`. The limiter is in-memory, so it resets on cold starts —
fine for a demo, not strict enough for a real product.

## How it is built

```text
index.html            Tailwind + SheetJS from CDN, app shell
App.tsx               State, loading and error handling
components/
  Header.tsx          Title bar
  InputForm.tsx       Objective, optional context, typed input, .xlsx parsing
  ResultsTable.tsx    Score breakdown and CSV export
  ScoreCard.tsx       Individual score display
  icons.tsx           SVG icons
services/
  geminiService.ts    Calls /api/analyze, with a request timeout
api/
  analyze.ts          Serverless function: prompt, schema, rate limiting
types.ts              Shared types, audience and tone presets
vite.config.ts        Vite config + a dev bridge that serves api/ locally
```

The Gemini key is only ever read server-side in `api/analyze.ts`. The browser calls
`/api/analyze` and never sees the key.

**Stack:** React 19, TypeScript, Vite, Tailwind, Google Gemini, Vercel.
