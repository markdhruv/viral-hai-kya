"""
Viral Hai Kya? - v1 scoring engine (corrected).

Pre-launch scoring for campaign copy. Four weighted dimensions plus one
reported diagnostic, every score computed here in code.

This is the archived v1 engine, published as the reference implementation of
METHODOLOGY.md. It is the original Python NLP pipeline with five documented
defects corrected; see CORRECTIONS in METHODOLOGY.md for what changed and why.
The notebook/ipywidgets front end has been dropped in favour of a CLI, so the
scoring logic can be read, diffed and tested on its own.

    pip install transformers torch textstat vaderSentiment empath \
                sentence-transformers pandas openpyxl

    python score_campaigns.py --campaigns messages.xlsx \
                              --keywords keywords.xlsx \
                              --ctas ctas.xlsx \
                              --out scorecard.xlsx

Every score is on a 1-5 scale. Nothing here is validated against real campaign
outcomes - it is a structured second opinion, not a prediction.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict

import pandas as pd
from empath import Empath
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import textstat

# ---------------------------------------------------------------------------
# Weights - the single source of truth.
#
# Derived from the ratios in the methodology paper (30 : 20 : 20 : 20), with
# Campaign Resonance removed from the weighted total and renormalised to 1.00.
# Resonance is still computed and reported; it is simply not double-counted,
# because it is defined as the emotion score and weighting it meant emotion
# silently drove half the result. Change a weight here and nowhere else.
# ---------------------------------------------------------------------------
WEIGHTS = {
    "emotion": 0.34,
    "readability": 0.22,
    "trend": 0.22,
    "shareability": 0.22,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "weights must sum to 1.00"

# STEPPS sub-weights, exactly as the paper specifies them.
STEPPS_WEIGHTS = {
    "emotional_trigger": 0.30,
    "cta_quality": 0.30,
    "format": 0.20,
    "social_lexicon": 0.20,
}
assert abs(sum(STEPPS_WEIGHTS.values()) - 1.0) < 1e-9

TREND_TF_WEIGHT = 0.60          # exact keyword presence
TREND_SEMANTIC_WEIGHT = 0.40    # embedding similarity

EMOTION_MODEL = "j-hartmann/emotion-english-distilroberta-base"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Empath returns normalised category fractions. These are small numbers, so we
# rescale with an explicit, declared ceiling rather than an undocumented *5.
# This is a heuristic rescale, not a calibrated one.
EMPATH_CEILING = 0.30


def clamp(value: float, low: float = 1.0, high: float = 5.0) -> float:
    """Hold a score inside the 1-5 scale the whole model is defined on."""
    return max(low, min(high, value))


def rescale(value: float, lo: float, hi: float) -> float:
    """Map a raw value in [lo, hi] onto the 1-5 scale."""
    if hi <= lo:
        return 1.0
    return clamp(1.0 + 4.0 * (value - lo) / (hi - lo))


class Scorer:
    def __init__(self) -> None:
        self.vader = SentimentIntensityAnalyzer()
        self.emotion = pipeline("text-classification", model=EMOTION_MODEL, top_k=5)
        self.empath = Empath()
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)

    # -- emotion ------------------------------------------------------------
    def vader_score(self, text: str) -> float:
        """VADER compound (-1..+1) mapped onto 1-5."""
        compound = self.vader.polarity_scores(text)["compound"]
        return clamp((compound + 1.0) * 2.0 + 1.0)

    def roberta_score(self, text: str) -> float:
        """
        Weighted emotional polarity from the RoBERTa classifier, mapped onto 1-5.

        Softmax confidences across the detected emotions are combined into a
        single polarity in roughly [-1, +1], then rescaled. The original mapped
        this with (p + 1) * 2.5, which bottoms out at 0 - below the scale the
        rest of the model uses. It is clamped here.
        """
        results = self.emotion(text)
        if not results or not isinstance(results[0], list):
            return 3.0  # neutral, not 0.0: a failure should not read as negative
        scores = {r["label"].lower(): r["score"] for r in results[0]}
        polarity = (
            scores.get("joy", 0.0) * 1.0
            + scores.get("optimism", 0.0) * 0.8
            - scores.get("sadness", 0.0) * 0.8
            - scores.get("anger", 0.0) * 1.0
        )
        return clamp((polarity + 1.0) * 2.0 + 1.0)

    def emotion_score(self, text: str) -> float:
        """Mean of the lexicon reading and the transformer reading."""
        return round((self.vader_score(text) + self.roberta_score(text)) / 2, 2)

    # -- readability --------------------------------------------------------
    @staticmethod
    def readability_score(text: str) -> float:
        """Flesch Reading Ease, binned to 1-5."""
        fre = textstat.flesch_reading_ease(text)
        if fre > 80:
            return 5.0
        if fre > 60:
            return 4.0
        if fre > 40:
            return 3.0
        if fre > 20:
            return 2.0
        return 1.0

    # -- trend relevance ----------------------------------------------------
    def trend_score(self, text: str, keywords: list[str], weights: list[float]) -> float:
        """
        0.60 * weighted keyword presence + 0.40 * semantic similarity.

        The original called the first term `tfidf_score`; it is a weighted
        count of keyword presence, with no inverse document frequency anywhere,
        so it is named for what it is.
        """
        if not keywords:
            return 1.0
        lowered = text.lower()
        hit_weight = sum(w for k, w in zip(keywords, weights) if k.lower() in lowered)
        max_weight = max(sum(weights), 1e-9)
        presence = rescale(min(hit_weight, max_weight), 0.0, max_weight)

        text_vec = self.embedder.encode(text, convert_to_tensor=True)
        trend_vec = self.embedder.encode(" ".join(keywords), convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(text_vec, trend_vec).item()
        semantic = rescale(max(similarity, 0.0), 0.0, 1.0)

        return round(
            TREND_TF_WEIGHT * presence + TREND_SEMANTIC_WEIGHT * semantic, 2
        )

    # -- STEPPS shareability ------------------------------------------------
    def shareability_score(self, text: str, ctas: pd.DataFrame) -> float:
        """
        The paper's weighted STEPPS formula, which the original code did not
        implement: it summed the components and divided by three, and folded
        the emotional-trigger and social-lexicon signals into one variable.
        They are separated and weighted here as documented.
        """
        categories = self.empath.analyze(text, normalize=True) or {}

        trigger_raw = sum(categories.get(c, 0.0) for c in ("joy", "anger", "positive_emotion"))
        social_raw = sum(categories.get(c, 0.0) for c in ("social_media", "affection", "fun"))
        emotional_trigger = rescale(trigger_raw, 0.0, EMPATH_CEILING)
        social_lexicon = rescale(social_raw, 0.0, EMPATH_CEILING)

        lowered = text.lower()
        matched = ctas[ctas["CTA Text"].str.lower().apply(lambda c: c in lowered)]
        cta_quality = (
            clamp(float(matched["Simple Avg"].mean())) if not matched.empty else 2.5
        )

        points = (1 if len(text.split()) <= 20 else 0) + (1 if "?" in text else 0)
        fmt = rescale(points, 0, 2)

        total = (
            STEPPS_WEIGHTS["emotional_trigger"] * emotional_trigger
            + STEPPS_WEIGHTS["cta_quality"] * cta_quality
            + STEPPS_WEIGHTS["format"] * fmt
            + STEPPS_WEIGHTS["social_lexicon"] * social_lexicon
        )
        return round(clamp(total), 2)


@dataclass
class Result:
    campaign_message: str
    emotion: float
    readability: float
    trend: float
    shareability: float
    resonance: float          # reported, not weighted - see WEIGHTS
    weighted_score: float
    recommendation: str


def weighted_score(parts: dict[str, float]) -> float:
    """The headline score. Arithmetic belongs in code, not in a prompt."""
    return round(sum(parts[k] * w for k, w in WEIGHTS.items()), 2)


def recommend(score: float) -> str:
    if score >= 4.0:
        return "Strong potential to succeed"
    if score >= 3.0:
        return "Good, but revise key elements"
    return "Needs rework before launch"


def analyse(campaigns: pd.DataFrame, keywords: pd.DataFrame, ctas: pd.DataFrame) -> pd.DataFrame:
    scorer = Scorer()
    kw = keywords["Keyword"].astype(str).tolist()
    kw_weights = keywords.get("Weightage (1-5)", pd.Series([1.0] * len(kw))).astype(float).tolist()

    rows = []
    for message in campaigns["Campaign Message"].astype(str):
        parts = {
            "emotion": scorer.emotion_score(message),
            "readability": scorer.readability_score(message),
            "trend": scorer.trend_score(message, kw, kw_weights),
            "shareability": scorer.shareability_score(message, ctas),
        }
        total = weighted_score(parts)
        rows.append(
            Result(
                campaign_message=message,
                resonance=parts["emotion"],  # resonance is defined as emotion
                weighted_score=total,
                recommendation=recommend(total),
                **parts,
            )
        )
    return pd.DataFrame([asdict(r) for r in rows])


def main() -> None:
    p = argparse.ArgumentParser(description="Score campaign copy before launch.")
    p.add_argument("--campaigns", required=True, help="xlsx with a 'Campaign Message' column")
    p.add_argument("--keywords", required=True, help="xlsx with 'Keyword' and 'Weightage (1-5)'")
    p.add_argument("--ctas", required=True, help="xlsx with 'CTA Text' and 'Simple Avg'")
    p.add_argument("--out", default="scorecard.xlsx")
    args = p.parse_args()

    result = analyse(
        pd.read_excel(args.campaigns),
        pd.read_excel(args.keywords),
        pd.read_excel(args.ctas),
    )
    result.to_excel(args.out, index=False)
    print(result.to_string(index=False))
    print(f"\nSaved: {args.out}")


if __name__ == "__main__":
    main()
