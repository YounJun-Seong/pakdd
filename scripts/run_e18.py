"""Phase-6 E18 one-pass vs recursive memory, generation (docs/phase6_prereg.md, 2026-11-23).
The truncation-free chain stopped after the FIRST write (M1), reader answers from M1. The first write reuses the
cache key of the four-pass chain, so M1 is the same generation. Families: original prompts (E13 / E14 chains) and
the E15 matched prompt. Outputs: results/e18_{model}.jsonl, _ok.jsonl (answers), _mem.jsonl (M1)."""
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
# family -> (cache file stem, mode names, chain-cond name per source: must equal the four-pass chain's for the cache hit)
FAM = {"original": ("ratio", {"aware": "aware", "blind": "blind"}, {"single": "single", "filler": "filler", "multi": "long"}),
       "matched": ("e15", {"aware": "aware_m", "blind": "blind_m"}, {"single": "single", "filler": "filler", "multi": "multi"})}


class E18(Runner):
    async def gen(self, budget):
        caches = {f: LLMCache(f"cache/{FAM[f][0]}_{self.model}.jsonl") for f in FAM}
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

        async def one(s, fam, mode, cond):
            spans, override, mat = m0(s, cond)
            r = await notrunc_chain(self.model, s, spans, FAM[fam][1][mode], FAM[fam][2][cond], budget, caches[fam], self.sem, self.enc,
                                    material_override=override, n_writes=1)
            r.update(ico(s)); r.update(exp="e18_onepass", family=fam, mode=mode, cond=cond, source_tokens=len(self.enc(self.model, mat)))
            if r.get("memory"):
                r["memory_tokens"] = len(self.enc(self.model, r["memory"]))
            return r
        await self.gather([one(s, f, m, c) for s in use for f in FAM for m in ("aware", "blind") for c in CONDS])
        stem = f"results/e18_{self.model}"
        dump(f"{stem}{self.tag}.jsonl", self.rows)
        ok = [r for r in self.rows if not r["failed"]]
        dump(f"{stem}_ok{self.tag}.jsonl", [{k: v for k, v in r.items() if k != "memory"} for r in ok])
        dump(f"{stem}_mem{self.tag}.jsonl", mem_rows(ok))
        print(f"  failed: {sum(r['failed'] for r in self.rows)} / {len(self.rows)}", flush=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=MODELS)
    ap.add_argument("--budget", type=int, default=200)
    ap.add_argument("--concurrency", type=int, default=48)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    await E18(args).gen(args.budget)
    print(f"E18_DONE {args.model}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
