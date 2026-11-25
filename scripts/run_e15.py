"""Phase-6 E15 matched-prompt control, generation (docs/phase6_prereg.md, 2026-11-23).
Aware / Blind x Single / Filler / Multi under ONE shared prompt (modes aware_m / blind_m; the Aware arm only adds
the question line), truncation-free, the 279 E14 articles. All six cells are regenerated.
Outputs: results/e15b{B}_{model}.jsonl (all chains), _ok.jsonl (finals), _mem.jsonl (memories)."""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_longsource import render  # noqa: E402
from run_phase4 import MODELS, material_text, spans_original  # noqa: E402
from run_phase5 import notrunc_chain  # noqa: E402
from run_rev import Runner, dump, ico, mem_rows  # noqa: E402
from supdrift.llm import LLMCache  # noqa: E402

CONDS = ("single", "filler", "multi")
MODES = ("aware_m", "blind_m")


class E15(Runner):
    async def gen(self, budget):
        cache = LLMCache(f"cache/e15_{self.model}.jsonl")
        F = {json.loads(l)["sample_id"]: json.loads(l) for l in open("data/longsource/longfiller_v1.jsonl")}
        L = {json.loads(l)["sample_id"]: json.loads(l) for l in open("data/longsource/longsource_v1.jsonl")}
        use = [s for s in self.samples if F[s["sample_id"]]["constructible"]]
        print(f"articles: {len(use)}; budget {budget}", flush=True)

        def m0(s, cond):
            if cond == "single":
                sp = spans_original(s, "single"); return sp, None, material_text(s["pmcid"], sp)
            B = (F if cond == "filler" else L)[s["sample_id"]]["blocks"]
            mat = render(B)
            return [x for b in B for x in b["spans"]], mat, mat

        async def one(s, mode, cond):
            spans, override, mat = m0(s, cond)
            r = await notrunc_chain(self.model, s, spans, mode, cond, budget, cache, self.sem, self.enc, material_override=override)
            r.update(ico(s)); r.update(exp="e15_matched", source_tokens=len(self.enc(self.model, mat)))
            if r.get("memory"):
                r["memory_tokens"] = len(self.enc(self.model, r["memory"]))
            return r
        await self.gather([one(s, m, c) for s in use for m in MODES for c in CONDS])
        stem = f"results/e15b{budget}_{self.model}"
        dump(f"{stem}{self.tag}.jsonl", self.rows)
        ok = [r for r in self.rows if not r["failed"]]
        dump(f"{stem}_ok{self.tag}.jsonl", [{k: v for k, v in r.items() if k != "memory"} for r in ok])
        dump(f"{stem}_mem{self.tag}.jsonl", mem_rows(ok))
        for m in MODES:
            for c in CONDS:
                g = [r for r in self.rows if r["mode"] == m and r["cond"] == c]
                print(f"  B={budget} {m}/{c}: failed {sum(r['failed'] for r in g) / len(g):.1%}", flush=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=MODELS)
    ap.add_argument("--budget", type=int, default=200)
    ap.add_argument("--concurrency", type=int, default=48)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    await E15(args).gen(args.budget)
    print(f"E15_DONE {args.model} B={args.budget}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
