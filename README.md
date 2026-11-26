# Viral Hai Kya?

**Know if your campaign will land — before you spend a rupee.**

Score campaign copy against the objective you actually picked. Six scores, one
weighted confidence number, and a reason for each.

**[Live demo](https://viral-hai-kya.vercel.app)** · no sign-in · 15 analyses a day

---

## Why it scores against an objective

Most copy checkers grade a message in a vacuum. That is the wrong question. A line
that is perfect for a loyalty email is a bad line for a conversion ad, so every
message here is scored against the goal you choose — awareness, consideration,
sales or loyalty — and each objective rewards different traits.

The weights are uneven on purpose. Objective fit counts for most, because a
well-written message aimed at the wrong goal still fails. Shareability counts for
least, because it is the most situational: a B2B renewal email is not supposed to
go viral.

---

## How it started, and what changed

**v1 — a Python NLP pipeline.** Four models doing four jobs: VADER for tone,
a fine-tuned RoBERTa classifier for emotional texture, MiniLM sentence embeddings
for semantic trend matching, Empath for the social and emotional categories behind
shareability, with Flesch Reading Ease for clarity. Every score was arithmetic:
the same copy in gave the same number out, and you could trace any result back to
the line of code that produced it.

It also could not be shared. It ran in a notebook, pulled down several hundred
megabytes of models, and wanted three Excel files before it would tell you
anything. I could use it. I could not hand it to a colleague who wanted an answer
about a subject line in the next ten minutes.

**v2 — this app.** No install, no models to download, no spreadsheet unless you
want one. A colleague can score a subject line in ten seconds on their phone.

The cost is real and worth stating. The scoring moved from four specialised models
into one general-purpose language model, and with it went determinism: run the same
copy twice and the numbers can differ. v1 could tell you exactly why a score was
2.8. v2 can give you a reason, but not a derivation.

**Auditable but unusable, against usable but unauditable.** v2 is the right trade
for the job this tool actually does — a fast second opinion before a line ships,
where being roughly right in ten seconds beats being precisely right in an hour.
But v1 is the better artefact, so it is published rather than deleted.

---

## What is in here

| | |
|---|---|
| [`METHODOLOGY.md`](METHODOLOGY.md) | What each dimension measures, which model produces it, and why that one |
| [`archive/v1/`](archive/v1/) | The original Python engine, corrected and runnable |
| `App.tsx`, `api/`, `components/` | The v2 web app |

The methodology ends with five defects found in the original paper and code —
including one where the weights in the write-up were not the weights in the code,
and one where emotion silently drove half the score. They are fixed in the archived
engine and documented rather than quietly corrected.

---

## Running v1

```bash
pip install transformers torch textstat vaderSentiment empath \
            sentence-transformers pandas openpyxl

python archive/v1/score_campaigns.py \
    --campaigns messages.xlsx --keywords keywords.xlsx --ctas ctas.xlsx
```

Input formats are in the methodology annexure. First run downloads the models.

## Running v2

```bash
npm install
npm run dev     # needs GEMINI_API_KEY in .env.local
```

---

## What this is not

A structured second opinion, not a prediction. The scores come from models
reasoning about copy, **not from campaign performance data**, so nothing here is
validated against real outcomes.

The weights are judgement, not regression output. Calibrating them against actual
post-launch results is the most useful thing that could happen to this model, and
it has not happened.

Good for catching a vague CTA, spotting a tone that fights the objective, and
forcing a decision about what a campaign is actually for before it ships. Treat a
low score as a reason to look harder, not as a verdict.

---

MIT
