"""Phase-6 E6 Contextual Evidence Robustness, generation (docs/phase6_prereg.md, 2026-11-22).

  gen --model qwen3-14b   truncation-free chains, budgets 100/200/400:
                            arm=context  Aware/Blind x Single/Multi on the context-rich inputs
                            arm=span     Aware/Blind x Multi on the original span-only material
                                         (span-only Single = E13 truncation-free Single chains, reused in analysis)
                          + final answer straight from the uncompressed context inputs
Outputs: results/e6_{model}.jsonl (all chains, failures kept), _ok.jsonl (finals), _mem.jsonl (memories),
         results/e6_answers_{model}.jsonl
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_phase4 import MODELS, material_text, spans_original  # noqa: E402
from run_phase5 import answer_from, notrunc_chain  # noqa: E402
from run_rev import Runner, dump, ico, mem_rows  # noqa: E402
from supdrift.llm import LLMCache  # noqa: E402

BUDGETS = [100, 200, 400]


class E6(Runner):
    async def gen(self):
        cache = LLMCache(f"cache/e6_{self.model}.jsonl")
        ctx = {json.loads(l)["sample_id"]: json.loads(l) for l in open("data/e6/e6_context_v1.jsonl")}

        async def one(s, arm, b, mode, cond):
            spans = spans_original(s, cond)
            mat = ctx[s["sample_id"]][cond] if arm == "context" else None
            r = await notrunc_chain(self.model, s, spans, mode, cond, b, cache, self.sem, self.enc, material_override=mat)
            r.update(ico(s))
            r.update(exp="e6", arm=arm, source_tokens=len(self.enc(self.model, mat or material_text(s["pmcid"], spans))))
            if r.get("memory"):
                r["memory_tokens"] = len(self.enc(self.model, r["memory"]))
            return r

        async def full(s, cond):
            text = await answer_from(self.model, s, ctx[s["sample_id"]][cond], s["target"], cache, self.sem, f"e6-full-{cond}")
            return {"sample_id": s["sample_id"], **ico(s), "source": "full_context", "cond": cond, "text": text}

        jobs = [one(s, "context", b, m, c) for s in self.samples for b in BUDGETS
                for m in ("aware", "blind") for c in ("single", "multi")]
        jobs += [one(s, "span", b, m, "multi") for s in self.samples for b in BUDGETS for m in ("aware", "blind")]
        n_chain = len(jobs)
        jobs += [full(s, c) for s in self.samples for c in ("single", "multi")]
        await self.gather(jobs)
        ch = [r for r in self.rows if "failed" in r]
        assert len(ch) == n_chain
        ch.sort(key=lambda r: (r["arm"], r["budget"], r["mode"], r["cond"]))
        dump(f"results/e6_{self.model}{self.tag}.jsonl", ch)
        ok = [r for r in ch if not r["failed"]]
        dump(f"results/e6_{self.model}_ok{self.tag}.jsonl", [{k: v for k, v in r.items() if k != "memory"} for r in ok])
        dump(f"results/e6_{self.model}_mem{self.tag}.jsonl", mem_rows(ok))
        dump(f"results/e6_answers_{self.model}{self.tag}.jsonl", [r for r in self.rows if "failed" not in r])
        for arm in ("context", "span"):
            for b in BUDGETS:
                for m in ("aware", "blind"):
                    for c in ("single", "multi"):
                        g = [r for r in ch if r["arm"] == arm and r["budget"] == b and r["mode"] == m and r["cond"] == c]
                        if g:
                            print(f"  {arm} B={b} {m}/{c}: failed {sum(r['failed'] for r in g) / len(g):.1%}", flush=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen"])
    ap.add_argument("--model", default="qwen3-14b", choices=MODELS)
    ap.add_argument("--concurrency", type=int, default=48)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    await E6(args).gen()
    print(f"E6_DONE gen {args.model}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
