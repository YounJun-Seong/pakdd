"""Gate 2 chains: question-aware vs question-blind compression over
single-ICO vs multi-ICO material.

Modes
  aware  — every intermediate step sees the target ICO question (Gate 1 style)
  blind  — intermediate steps only condense "for future use"; ONLY the final
           step sees the target question. Depth 1 has no intermediate steps,
           so aware==blind there; run it once as mode "direct".

Material
  single — the target prompt's evidence span only
  multi  — target + distractor spans from the same article, deterministically
           shuffled, presented as one set of research notes

Same model at every step. Citations not pinned (mild preserve-sources
instruction), identical to Gate 1.
"""
import random
import re

from .chain import FINAL_SYSTEM, FINAL_USER, INTERMEDIATE_SYSTEM, INTERMEDIATE_USER
from .llm import LLMCache, chat, full_cache_key

FINAL_ANSWER_TOKENS = 80
AGENT_TEMPERATURE = 0.7
AGENT_SEED = 42

BLIND_SYSTEM = """You are one step in a multi-step biomedical research assistant pipeline.
You receive working notes about a clinical study. The specific question that a later
step will need to answer is not yet known.
Condense the notes for future use, within the length limit.
Preserve the supporting evidence and source information as appropriate.
Output only the notes."""

BLIND_USER = """Notes from the previous step:
{material}

Condense these notes so a later step can use them. Maximum length: {budget} tokens (about {words} words)."""

# QAWP ablation arm: same budget, adds only an INSTRUCTION to protect qualifiers
BLIND_INSTR_SYSTEM = """You are one step in a multi-step biomedical research assistant pipeline.
You receive working notes about a clinical study. The specific question that a later
step will need to answer is not yet known.
Condense the notes for future use, within the length limit.
Because any finding may be asked about later, never strengthen a claim: keep each
finding's effect direction and statistical significance exactly as stated (especially
"no significant difference"), and keep population, condition, and uncertainty
qualifiers. Preserve the supporting evidence and source information as appropriate.
Output only the notes."""

# QAWP: same budget, structured compact warrant tags inside the notes
QAWP_SYSTEM = """You are one step in a multi-step biomedical research assistant pipeline.
You receive working notes about a clinical study. The specific question that a later
step will need to answer is not yet known.
Condense the notes for future use, within the length limit, as compact warrant tags:
one line per distinct finding, naming the actual outcome measure and comparison.
Format: [<outcome>, <intervention> vs <comparator> | dir=up/down/none | sig=y/n | <qualifiers>]
Examples:
[systolic BP, drug A vs placebo | dir=down | sig=y | adults 45-60, 12wk]
[mortality, drug A vs placebo | dir=none | sig=n | -]
Never strengthen a claim: record dir=none and sig=n exactly as stated in the notes.
Keep the source id if present. Output only the tag lines."""

QAWP_USER = """Notes from the previous step:
{material}

Rewrite as compact warrant tags for future use. Maximum length: {budget} tokens (about {words} words)."""


def seed_material(sample: dict, icoset: str) -> str:
    pmcid = sample["pmcid"]
    spans = [sample["target"]["evidence"]]
    if icoset == "multi":
        spans = spans + [d["evidence"] for d in sample["distractors"]]
        random.Random(f"{sample['sample_id']}-order").shuffle(spans)
    body = "\n".join(f"- {s}" for s in spans)
    return f"Excerpts from source article [PMC{pmcid}]:\n{body}"


def citation_flags(text: str, pmcid: int) -> dict:
    found = re.findall(r"PMC\s?(\d+)", text)
    return {"citation_present": bool(found), "citation_correct": str(pmcid) in found}


async def run_chain2(
    sample: dict,
    *,
    model_name: str,
    mode: str,        # "aware" | "blind" | "direct" (depth 1)
    icoset: str,      # "single" | "multi"
    depth: int,
    budget: int,
    cache: LLMCache,
    sem,
    seed: int = AGENT_SEED,
    cache_tag: str = "",
) -> list[dict]:
    t = sample["target"]
    ico = {k: t[k] for k in ("intervention", "comparator", "outcome")}
    material = seed_material(sample, icoset)
    steps = []

    for step in range(1, depth + 1):
        is_final = step == depth
        if is_final:
            system = FINAL_SYSTEM
            user = FINAL_USER.format(material=material, budget=FINAL_ANSWER_TOKENS,
                                     words=int(FINAL_ANSWER_TOKENS * 0.75), **ico)
            out_budget = FINAL_ANSWER_TOKENS
        elif mode == "aware":
            system = INTERMEDIATE_SYSTEM
            user = INTERMEDIATE_USER.format(material=material, budget=budget,
                                            words=int(budget * 0.75), **ico)
            out_budget = budget
        elif mode == "blind_instr":
            system = BLIND_INSTR_SYSTEM
            user = BLIND_USER.format(material=material, budget=budget,
                                     words=int(budget * 0.75))
            out_budget = budget
        elif mode == "blind_qawp":
            system = QAWP_SYSTEM
            user = QAWP_USER.format(material=material, budget=budget,
                                    words=int(budget * 0.75))
            out_budget = budget
        else:  # blind
            system = BLIND_SYSTEM
            user = BLIND_USER.format(material=material, budget=budget,
                                     words=int(budget * 0.75))
            out_budget = budget
        key_payload = {
            "task": "chain2_step", "sample_id": sample["sample_id"],
            "mode": mode, "icoset": icoset, "depth": depth, "budget": budget,
            "step": step, "material": material,
        }
        if cache_tag:  # only tagged runs get distinct keys (keeps old cache valid)
            key_payload["tag"] = cache_tag
        cache_key = full_cache_key(model_name, key_payload)
        text = (await chat(
            model_name,
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            cache=cache, cache_key=cache_key, sem=sem,
            temperature=AGENT_TEMPERATURE, seed=seed,
            max_tokens=out_budget * 2 + 64,
        )).strip()
        steps.append({
            "step": step,
            "role": "final" if is_final else "intermediate",
            "text": text,
            **citation_flags(text, sample["pmcid"]),
        })
        material = text

    return steps
