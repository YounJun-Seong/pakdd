"""ICO claim classifier.

Given an (intervention, comparator, outcome) triple and a text, decide what the
text asserts about the effect of the intervention (vs the comparator) on the
outcome. Two fields are extracted:

  direction : INCREASE | DECREASE | NO_DIFFERENCE | NOT_MENTIONED
  certainty : ASSERTED | HEDGED | NONE

The primary 4-way claim label used for support scoring is derived as:

  claim_label = direction            if certainty == ASSERTED
              = UNCERTAIN            if certainty == HEDGED
              = NOT_MENTIONED        if direction == NOT_MENTIONED

Keeping direction+certainty separate lets us score both mutation
(definitive wrong direction) and omission/hedging drift from the same output,
and feeds the modality-drift taxonomy later without extra calls.
"""
import json
import re

from .llm import LLMCache, chat, full_cache_key

CLASSIFIER_MODEL = "qwen3-32b"
PROMPT_VERSION = "v3"  # v2 prompt + FP8 backend; bump invalidates AWQ-era cache

SYSTEM_PROMPT = """You are an expert at reading reports of randomized controlled trials.

You will be given:
- an INTERVENTION, a COMPARATOR, and an OUTCOME
- a TEXT (an excerpt from a trial report, or a summary written about one)

Your task: determine what the TEXT claims about the effect of the INTERVENTION,
relative to the COMPARATOR, on the OUTCOME. Judge ONLY what the text asserts.
Do not judge whether the claim is medically true.

Think through the following before answering:
1. Which group in the text corresponds to the INTERVENTION and which to the
   COMPARATOR? Groups are often named by abbreviations, brand names, doses, or
   generically ("the treatment group", "the experimental group") — match them to
   the given INTERVENTION/COMPARATOR whenever the correspondence is reasonable.
2. Does the text report the given OUTCOME (or an obvious rewording of it)?
   A different outcome measure is NOT this outcome (e.g. progression-free
   survival is not overall survival; bacteria counts are not acetate levels).
3. What direction does the text claim, FOR THE INTERVENTION RELATIVE TO THE
   COMPARATOR? Be careful with reversed phrasing: "X was higher in the
   comparator group" means the intervention DECREASED X.
4. Translate improvement/worsening language into the direction of the quantity
   named by the OUTCOME: "symptoms improved" = symptoms DECREASE; "survival
   improved" = survival INCREASE — regardless of how a score scale moves.

Then output a single JSON object with exactly these fields:

"direction": one of
  "INCREASE"       — the text claims the intervention increased/raised the outcome relative to the comparator
  "DECREASE"       — the text claims the intervention decreased/reduced the outcome relative to the comparator
  "NO_DIFFERENCE"  — the text claims there was no (significant) difference between the groups on this outcome
  "NOT_MENTIONED"  — the text does not address this intervention/comparator/outcome relationship

"certainty": one of
  "ASSERTED" — the claim is stated as a finding/fact (e.g. "significantly reduced", "was lower", "no significant difference was found", "improves")
  "HEDGED"   — the claim is explicitly tentative (e.g. "may reduce", "a trend toward", "suggests", "possibly", "numerically lower but not significant")
  "NONE"     — use only with direction NOT_MENTIONED

Rules:
- A numeric difference reported WITH "not statistically significant" (or p > 0.05)
  is a NO_DIFFERENCE claim with certainty ASSERTED, unless the text itself frames
  the numeric difference as a real effect, in which case it is that direction
  with certainty HEDGED.
- "Comparable", "similar between groups" => NO_DIFFERENCE, ASSERTED.
- Use NOT_MENTIONED only when the text clearly concerns different interventions
  or a different outcome measure, not merely because names are abbreviated or
  implicit.
- If the text makes both a hedged and an asserted claim about the same
  relationship, use the asserted one.

End your answer with the JSON object on its own line."""

USER_TEMPLATE = """INTERVENTION: {intervention}
COMPARATOR: {comparator}
OUTCOME: {outcome}

TEXT:
{text}"""

VALID_DIRECTIONS = {"INCREASE", "DECREASE", "NO_DIFFERENCE", "NOT_MENTIONED"}
VALID_CERTAINTY = {"ASSERTED", "HEDGED", "NONE"}


def derive_claim_label(direction: str, certainty: str) -> str:
    if direction == "NOT_MENTIONED":
        return "NOT_MENTIONED"
    if certainty == "ASSERTED":
        return direction
    return "UNCERTAIN"


def parse_response(raw: str) -> dict:
    # thinking models emit <think>...</think> first; take the last JSON object
    # that carries a "direction" field
    tail = raw.split("</think>")[-1]
    candidates = [m for m in re.findall(r"\{[^{}]*\}", tail, re.DOTALL) if "direction" in m]
    if not candidates:
        return {"direction": "PARSE_ERROR", "certainty": "PARSE_ERROR", "claim_label": "PARSE_ERROR"}
    try:
        obj = json.loads(candidates[-1])
    except json.JSONDecodeError:
        return {"direction": "PARSE_ERROR", "certainty": "PARSE_ERROR", "claim_label": "PARSE_ERROR"}
    d = str(obj.get("direction", "")).upper()
    c = str(obj.get("certainty", "")).upper()
    if d not in VALID_DIRECTIONS or c not in VALID_CERTAINTY:
        return {"direction": d or "PARSE_ERROR", "certainty": c or "PARSE_ERROR", "claim_label": "PARSE_ERROR"}
    return {"direction": d, "certainty": c, "claim_label": derive_claim_label(d, c)}


async def classify(
    intervention: str,
    comparator: str,
    outcome: str,
    text: str,
    *,
    cache: LLMCache,
    sem,
    model: str = CLASSIFIER_MODEL,
) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_TEMPLATE.format(
            intervention=intervention, comparator=comparator, outcome=outcome, text=text
        )},
    ]
    base_key = {"task": "ico_classify", "v": PROMPT_VERSION,
                "i": intervention, "c": comparator, "o": outcome, "t": text}
    # attempts 0-1: thinking mode (reseeded retry catches occasional degeneration
    # or overlong reasoning); attempt 2: no-think fallback so a JSON always lands
    attempts = [
        {"a": 0, "seed": 42, "think": True, "max_tokens": 2500},
        {"a": 1, "seed": 43, "think": True, "max_tokens": 3500},
        {"a": 2, "seed": 42, "think": False, "max_tokens": 600},
    ]
    def _not_degenerate(raw: str) -> bool:
        # guards against silent server collapse ('!!!!...'); never an evaluator
        # semantic change — a degenerate string was never a valid judgment
        return "!" * 30 not in raw

    out = None
    for att in attempts:
        # infra failures (timeout on a pathological thinking generation, a
        # server restart) advance to the next frozen attempt instead of
        # aborting — attempt order and sampling params are unchanged
        try:
            raw = await chat(
                model, messages,
                cache=cache, cache_key=full_cache_key(model, {**base_key, "a": att["a"]}),
                sem=sem, retries=2, validate=_not_degenerate,
                # Qwen3 thinking mode: recommended sampling; greedy decoding degrades it
                temperature=0.6, top_p=0.95, seed=att["seed"],
                max_tokens=att["max_tokens"],
                extra_body={"chat_template_kwargs": {"enable_thinking": att["think"]},
                            "repetition_penalty": 1.05},
            )
        except Exception:
            if att is attempts[-1]:
                raise
            continue
        out = parse_response(raw)
        if out["claim_label"] != "PARSE_ERROR":
            break
    assert out is not None
    out["raw"] = raw
    return out
