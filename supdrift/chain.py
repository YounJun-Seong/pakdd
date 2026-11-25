"""Gate 1 agent chain: recursive summarization with compression pressure.

Depth d = number of LLM calls. Depth 1 is evidence -> final answer directly;
depth d>1 inserts d-1 intermediate note-passing steps, each limited to a token
budget (the compression condition). The same model is used at every step of a
chain, so depth effects are not confounded with model switches.

Citations are NOT pinned: step 1 receives the source id (PMC{pmcid}) inside the
material, and every step gets only a mild "preserve supporting evidence and
source information" instruction. Whether the citation and the meaning survive
are then measured independently.
"""
import json
import re

from .llm import LLMCache, chat, full_cache_key

FINAL_ANSWER_TOKENS = 80
AGENT_TEMPERATURE = 0.7
AGENT_SEED = 42

INTERMEDIATE_SYSTEM = """You are one step in a multi-step biomedical research assistant pipeline.
You receive working notes from the previous step about a clinical research question.
Rewrite them as concise notes for the next step, within the length limit.
Preserve the supporting evidence and source information as appropriate.
Output only the notes."""

INTERMEDIATE_USER = """Research question: What is the effect of "{intervention}" compared with "{comparator}" on "{outcome}"?

Notes from the previous step:
{material}

Write the notes for the next step. Maximum length: {budget} tokens (about {words} words)."""

FINAL_SYSTEM = """You are the final step of a multi-step biomedical research assistant pipeline.
Based on the working notes you receive, answer the research question for a clinical reader.
State the conclusion about the effect, citing the source as appropriate.
Output only the answer."""

FINAL_USER = """Research question: What is the effect of "{intervention}" compared with "{comparator}" on "{outcome}"?

Working notes:
{material}

Answer the research question. Maximum length: {budget} tokens (about {words} words)."""


def seed_material(evidence: str, pmcid: int) -> str:
    return f"Excerpt from source article [PMC{pmcid}]:\n{evidence}"


def citation_flags(text: str, pmcid: int) -> dict:
    """citation_present: any PMC-style citation appears; citation_correct: the right one."""
    found = re.findall(r"PMC\s?(\d+)", text)
    return {
        "citation_present": bool(found),
        "citation_correct": str(pmcid) in found,
    }


async def run_chain(
    sample: dict,
    *,
    model_name: str,
    depth: int,
    budget: int,
    cache: LLMCache,
    sem,
) -> list[dict]:
    """Returns one record per step: {step, role, text, citation flags}."""
    ico = {k: sample[k] for k in ("intervention", "comparator", "outcome")}
    material = seed_material(sample["evidence"], sample["pmcid"])
    steps = []

    for t in range(1, depth + 1):
        is_final = t == depth
        if is_final:
            system, user_tmpl, out_budget = FINAL_SYSTEM, FINAL_USER, FINAL_ANSWER_TOKENS
        else:
            system, user_tmpl, out_budget = INTERMEDIATE_SYSTEM, INTERMEDIATE_USER, budget
        user = user_tmpl.format(material=material, budget=out_budget,
                                words=int(out_budget * 0.75), **ico)
        cache_key = full_cache_key(model_name, {
            "task": "chain_step",
            "sample_id": sample["sample_id"],
            "depth": depth, "budget": budget, "step": t,
            "material": material,
        })
        text = (await chat(
            model_name,
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            cache=cache, cache_key=cache_key, sem=sem,
            temperature=AGENT_TEMPERATURE, seed=AGENT_SEED,
            # hard cap well above the instructed budget: we want instruction-driven
            # compression (like a real pipeline), not mid-sentence truncation
            max_tokens=out_budget * 2 + 64,
        )).strip()
        steps.append({
            "step": t,
            "role": "final" if is_final else "intermediate",
            "text": text,
            **citation_flags(text, sample["pmcid"]),
        })
        material = text

    return steps
