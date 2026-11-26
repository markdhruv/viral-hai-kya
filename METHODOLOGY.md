# Viral Hai Kya? — A Marketer's Guide to Predictive Messaging

How campaign copy is scored before it ships: what each dimension measures, which
model produces it, and why that model was chosen.

This is the methodology for **v1**, the Python NLP engine, which is the reference
implementation in [`archive/v1/score_campaigns.py`](archive/v1/score_campaigns.py).
The live web app is a later rebuild that scores the same idea differently —
see [the README](README.md) for what changed and why. Where the two disagree, this
document describes v1.

**[Corrections](#corrections) at the end lists five defects found in the original
paper and code, and what was done about each.** Nothing here is validated against
real campaign outcomes.

---

## 1. What the tool does

A campaign evaluation and scoring engine built with natural language processing,
sentiment analysis and heuristic models. It lets a marketing team evaluate messages
objectively before launch, without writing code.

Each message is scored on four weighted dimensions:

| Dimension | What it measures | Weight |
|---|---|---|
| Emotional resonance | How strongly the message is likely to strike a chord | 0.34 |
| Readability | Whether it is understood at a glance | 0.22 |
| Trend relevance | How well it connects to what is current | 0.22 |
| Shareability (STEPPS) | Whether anyone has a reason to pass it on | 0.22 |

A fifth score, **campaign resonance**, is computed and reported but deliberately
not weighted — see [Correction 2](#2-emotion-drove-half-the-score).

The output is a scorecard with every component visible, a weighted confidence
score, and a recommendation band.

---

## 2. Process flow

| Stage | Component | Function |
|---|---|---|
| **Inputs** | Campaign messages | Manual entry or Excel upload |
| | Keyword list with weightages | Excel input for trend relevance |
| | CTA library with tone/type scores | Excel input for CTA quality |
| **Processing** | Emotion scoring | VADER (tone) + RoBERTa (emotional depth), normalised to 1–5 |
| | Readability scoring | `textstat` → Flesch Reading Ease → binned to 1–5 |
| | Trend relevance | Weighted keyword presence + semantic similarity (MiniLM) |
| | STEPPS shareability | Empath categories + CTA lookup + format heuristics |
| | Campaign resonance | Emotion score used as a proxy for brand fit |
| **Final** | Weighted score engine | Blends the four weighted dimensions |
| | Recommendation engine | Bands the final score |
| **Outputs** | Scorecard | Every component, final score, recommendation |
| | Excel export | All input and output data |

---

## 3. The components

### 3.1 Emotion scoring

Emotional response is a core predictor of recall and sharing. This module uses a
hybrid of two complementary NLP tools, because each answers a different question.

**VADER** (Valence Aware Dictionary and sEntiment Reasoner), Hutto and Gilbert,
Georgia Tech, 2014. A rule-based sentiment lexicon tuned for social media and
marketing language. It handles exclamation marks, capitalisation, negation and
slang, needs no training data, and returns a compound score from −1 to +1.
Chosen because it is fast, light, and built for the kind of language campaigns
actually use.

**RoBERTa**, a transformer model from Facebook AI Research, 2019 — a refined BERT
trained on far more data. This implementation uses
`j-hartmann/emotion-english-distilroberta-base`, a distilled model fine-tuned on
emotion categories: joy, anger, sadness, fear, optimism. Chosen because it reads
text bidirectionally and captures emotional *texture* rather than just polarity —
cheerful versus bold, concerned versus angry.

| | VADER | RoBERTa |
|---|---|---|
| Core logic | Lexicon + rules | Transformer |
| Strength | Fast, handles slang and emoji | Emotional granularity |
| Weakness | Limited nuance | Slower; can miss short-phrase tone |

> One gives us tone. The other gives us texture.

Both are mapped onto 1–5 and averaged. The RoBERTa polarity is built as
`joy×1.0 + optimism×0.8 − sadness×0.8 − anger×1.0`, giving roughly −1 to +1,
then rescaled and clamped to the 1–5 floor and ceiling.

### 3.2 Readability scoring

A marketing message has milliseconds to land. If it is too dense, the reader
scrolls past.

Computed with the `textstat` library using **Flesch Reading Ease**, chosen over
Flesch-Kincaid (outputs grade levels, less intuitive), Gunning Fog (penalises
passive voice too harshly) and SMOG (better suited to long text).

$$FRE = 206.835 - (1.015 \times ASL) - (84.6 \times ASW)$$

where ASL is average sentence length and ASW is average syllables per word.

| FRE | Score | Reading |
|---|---|---|
| > 80 | 5 | Very easy |
| 61–80 | 4 | Easy |
| 41–60 | 3 | Moderate |
| 21–40 | 2 | Fairly hard |
| ≤ 20 | 1 | Difficult |

*Write drunk, edit with Flesch.*

### 3.3 Trend relevance

Trends live in ideas and phrasing, not only in keywords, so this measures both
surface relevance and deep relevance.

- **Weighted keyword presence** — the uploaded keyword list carries a 1–5
  weightage per term; matched weights are summed and rescaled.
- **Semantic similarity** — the message and the keyword block are each encoded
  with `all-MiniLM-L6-v2`, a compact sentence-transformer, and compared by cosine
  similarity. This catches meaning the exact words miss: *sneakers* ≈
  *trainers* ≈ *running shoes*.

$$Trend = 0.60 \times Presence + 0.40 \times Semantic$$

Presence is weighted higher to reward precision; similarity carries the rest to
reward conceptual alignment.

**Assigning keyword weightages.** Score a keyword 5 if it is culturally hot right
now, 3 if it is evergreen but vague, 4 if it is seasonal with a large audience.
Avoid making everything a 5.

### 3.4 STEPPS shareability

Why do some messages spread and others fizzle, at equal emotional weight? The
answer is shareability, and the frame here is Jonah Berger's **STEPPS** — Social
currency, Triggers, Emotion, Public, Practical value, Stories — from *Contagious*.

Not all six elements are computationally measurable, so core STEPPS themes are
translated into proxies:

| Component | How it is measured | Weight |
|---|---|---|
| Emotional triggers | Empath categories: joy, anger, positive emotion | 0.30 |
| CTA quality | Matched against the uploaded CTA library's tone/type scores | 0.30 |
| Format heuristics | ≤ 20 words; contains a question | 0.20 |
| Social lexicon | Empath categories: social media, affection, fun | 0.20 |

$$STEPPS = 0.30\,T + 0.30\,C + 0.20\,F + 0.20\,S$$

Each component is normalised to 1–5 before weighting, and the total is clamped.

Empath is used rather than a bespoke lexicon because it detects psychological and
social themes across roughly 200 validated categories. It is layered with custom
logic because it understands neither formatting triggers — brevity, questions —
nor CTA effectiveness, which depends on tone and type.

> Going viral isn't magic. It's architecture.

### 3.5 Campaign resonance

Resonance asks the reality check: *does this sound like us?* It is the overlap
between brand personality, audience mindset and emotional appeal.

In this version, the combined emotion score is used **directly as a proxy** for
resonance. The reasoning: emotion is the first test of fit — if a message does not
resonate emotionally, it does not matter how trendy or readable it is — and the
emotion score already blends tone and emotional intent.

A manual fit slider was considered and dropped: it varies by user, adds friction
to batch testing, and makes results harder to replicate. The framework can support
a manual override in a later version.

**Because resonance is defined as the emotion score, it is reported but not
weighted.** Weighting it meant counting the same signal twice — see
[Correction 2](#2-emotion-drove-half-the-score).

A caveat worth stating plainly: emotional resonance is not brand fit. The logic
assumes that a message scoring low on emotional resonance probably does not fit
any strong brand personality. That filters out tone-dead copy early. It does not
guarantee a fit with yours.

---

## 4. Reading the output

| Metric | What it tells you |
|---|---|
| Emotion | How strongly it might connect emotionally |
| Readability | How quickly it is understood |
| Trend | How topical or timely it is |
| STEPPS | Spread potential, from triggers that drive sharing |
| Resonance | Strategic alignment with tone and objective *(reported, unweighted)* |

$$Final = 0.34\,E + 0.22\,R + 0.22\,T + 0.22\,S$$

| Score | Recommendation |
|---|---|
| ≥ 4.0 | Strong potential to succeed |
| 3.0 – 3.9 | Good, but revise key elements |
| < 3.0 | Needs rework before launch |

**What to look for:**

| Situation | What to do |
|---|---|
| High trend, low emotion | Add emotional framing; make it feel urgent or joyful |
| High emotion, low shareability | Check the format — shorten it, or use a punchier CTA |
| Low readability, high resonance | Rewrite in simpler terms, keep the tone |
| Final score below 3.0 | Consider overhauling the message entirely |

---

## 5. Using it on real campaigns

| Stage | How to apply it |
|---|---|
| Conceptualisation | Score early drafts before deep production investment |
| A/B testing | Compare hero-line variants |
| Localisation | Check that translated messages retain tone parity |
| Internal alignment | Support creative rationale with score-based evidence |
| Post-mortem | Back-test what the winning creatives scored high on |

The loop: write variations → score → edit the weak dimension → re-score → ship
the best version.

**Not every campaign needs a 5 everywhere.** Top-funnel ads should prioritise trend
and STEPPS. Brand tone testing should focus on emotion. Performance campaigns
should aim for readability and CTA clarity.

---

## 6. What this is not

This is a structured second opinion, not a prediction. The scores come from
language models and lexicons reasoning about copy, **not from campaign performance
data**, so nothing here is validated against real outcomes. Treat a low score as a
reason to look harder, not as a verdict.

The weights are judgement, not regression output. They were set from reasoning
about which dimensions matter most for short-form copy, and they have not been
fitted to results. Calibrating them against actual post-launch performance is the
most valuable thing that could be done to this model.

---

## Corrections

Five defects were found in the original paper and code while preparing this
publication. All are fixed in `archive/v1/score_campaigns.py`, and this document
describes the corrected model.

### 1. The paper and the code disagreed on the weights

Section 4 of the original paper gave the formula as
`0.30 emotion + 0.20 readability + 0.20 trend + 0.20 STEPPS + 0.10 resonance`.
The code used
`0.25 subjective fit + 0.25 emotion + 0.20 readability + 0.15 trend + 0.15 STEPPS`.
Both summed to 1.00, but they were different models, and the paper documented one
while the tool ran the other.

**Fixed:** one `WEIGHTS` dictionary in the code is now the only definition, and
this document reflects it.

### 2. Emotion drove half the score

The code assigned `Subjective Fit Score = Combined Emotion Score` — a literal
copy — and then weighted both at 0.25. Emotion therefore accounted for **50%** of
the final score, against the 0.40 the paper implied. The paper disclosed that
resonance used emotion as a proxy, but not that this doubled emotion's influence.

**Fixed:** resonance is computed and reported, but removed from the weighted
total. The paper's remaining ratios (30:20:20:20) are renormalised to 1.00.

### 3. The STEPPS formula in the paper was not the one in the code

The paper specified
`0.30 emotional trigger + 0.30 CTA quality + 0.20 format + 0.20 social lexicon`.
The code summed the components and divided by three, and merged the emotional
trigger and social lexicon signals into a single variable.

**Fixed:** the components are separated and the documented weights applied.

### 4. The emotion score could fall below its own scale

The RoBERTa polarity was mapped with `(polarity + 1) × 2.5`. With polarity
reaching −1, that produces 0 — below the 1–5 floor every other score respects,
and it was never clamped.

**Fixed:** every score is clamped to 1–5 at the point it is produced.

### 5. A term was named for something it was not

The keyword component was called `tfidf_score`. It is a weighted count of keyword
presence; there is no inverse document frequency in it.

**Fixed:** renamed to reflect what it computes.

---

## Annexure: input formats

**Campaign messages** — `Serial Number`, `Campaign Message`.

**Trend keywords** — `Serial Number`, `Keyword`, `Weightage (1-5)`. Checked by both
exact presence and semantic similarity.

**CTA reference** — `Serial Number`, `CTA Text`, `CTA Type`, `Type Score`,
`CTA Tone`, `Tone Score`, `Simple Avg`. Type scores how actionable and directional
the CTA is; tone scores whether it creates urgency, optimism or social proof;
the simple average of the two feeds the shareability formula.
