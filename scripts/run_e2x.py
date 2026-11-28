"""Phase-6 E20 / E21 / E23, generation (docs/phase6_prereg.md, 2026-11-27).

  e20 --model M   final answer straight from the uncompressed Single and Filler source (279 articles)
                  -> results/e20_answers_{model}.jsonl
  e21 --model M   Aware / Blind x competing-first sources at 200 / 500 / 1,000 tokens, B = 200, truncation-free,
                  original and matched prompts -> results/e21_{model}.jsonl (+ _ok, _mem)
  e23 --model M   Aware / Blind x Single / Filler / Multi, B = 200, truncation-free, base seeds 143 / 244 / 345 / 446
                  -> results/e23_{model}.jsonl (+ _ok, _mem)

Every row carries the target ICO and gold label (score_generic.py --self-ico)."""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_longsource import render  # noqa: E402
from run_phase4 import MODELS, material_text, spans_original  # noqa: E402
from run_phase5 import answer_from, notrunc_chain  # noqa: E402
from run_rev import Runner, dump, ico, mem_rows  # noqa: E402
from supdrift.llm import LLMCache  # noqa: E402

FAM = {"original": {"aware": "aware", "blind": "blind"}, "matched": {"aware": "aware_m", "blind": "blind_m"}}
SEEDS = [143, 244, 345, 446]
BUDGET = 200


def jl(p):
    return [json.loads(l) for l in open(p)]


class E2x(Runner):
    def filler(self):
        return {r["sample_id"]: r for r in jl("data/longsource/longfiller_v1.jsonl") if r["constructible"]}

    def finish(self, stem):
        dump(f"{stem}{self.tag}.jsonl", self.rows)
        ok = [r for r in self.rows if not r["failed"]]
        dump(f"{stem}_ok{self.tag}.jsonl", [{k: v for k, v in r.items() if k != "memory"} for r in ok])
        dump(f"{stem}_mem{self.tag}.jsonl", mem_rows(ok))
        print(f"  failed: {sum(r['failed'] for r in self.rows)} / {len(self.rows)}", flush=True)

    # ------------------------------------------------------------------ E20
    async def e20(self):
        cache = LLMCache(f"cache/e20_{self.model}.jsonl")
        F = self.filler()
        use = [s for s in self.samples if s["sample_id"] in F]

        async def one(s, source, mat):
            text = await answer_from(self.model, s, mat, s["target"], cache, self.sem, f"e20-{source}")
            return {"sample_id": s["sample_id"], **ico(s), "source": source,
                    "source_tokens": len(self.enc(self.model, mat)), "text": text}
        jobs = []
        for s in use:
            jobs.append(one(s, "full_single", material_text(s["pmcid"], spans_original(s, "single"))))
            jobs.append(one(s, "full_filler", render(F[s["sample_id"]]["blocks"])))
        await self.gather(jobs)
        dump(f"results/e20_answers_{self.model}{self.tag}.jsonl", self.rows)

    # ------------------------------------------------------------------ E21
    async def e21(self):
        cache = LLMCache(f"cache/e21_{self.model}.jsonl")
        by = {s["sample_id"]: s for s in self.samples}
        src = [r for r in jl("data/longsource/e21_sources_v1.jsonl") if r["sample_id"] in by]
        print(f"sources: {len(src)} ({len({r['sample_id'] for r in src})} articles)", flush=True)

        async def one(x, fam, mode):
            s = by[x["sample_id"]]; mat = render(x["blocks"])
            r = await notrunc_chain(self.model, s, [sp for b in x["blocks"] for sp in b["spans"]], FAM[fam][mode],
                                    f"comp_first{x['level']}", BUDGET, cache, self.sem, self.enc, material_override=mat)
            r.update(ico(s)); r.update(exp="e21_lencomp", family=fam, mode=mode, arm="competing_first", level=x["level"],
                                       constructible=x["constructible"], source_tokens=len(self.enc(self.model, mat)))
            if r.get("memory"):
                r["memory_tokens"] = len(self.enc(self.model, r["memory"]))
            return r
        await self.gather([one(x, f, m) for x in src for f in FAM for m in ("aware", "blind")])
        self.finish(f"results/e21_{self.model}")

    # ------------------------------------------------------------------ E23
    async def e23(self):
        cache = LLMCache(f"cache/e23_{self.model}.jsonl")
        F = self.filler()
        L = {r["sample_id"]: r for r in jl("data/longsource/longsource_v1.jsonl")}
        use = [s for s in self.samples if s["sample_id"] in F]
        print(f"articles: {len(use)}; seeds {SEEDS}", flush=True)

        def m0(s, cond):
            if cond == "single":
                sp = spans_original(s, "single"); return sp, None, material_text(s["pmcid"], sp)
            blocks = (F if cond == "filler" else L)[s["sample_id"]]["blocks"]
            mat = render(blocks); return [x for b in blocks for x in b["spans"]], mat, mat

        async def one(s, seed, mode, cond):
            spans, override, mat = m0(s, cond)
            r = await notrunc_chain(self.model, s, spans, mode, cond, BUDGET, cache, self.sem, self.enc,
                                    material_override=override, base_seed=seed)
            r.update(ico(s)); r.update(exp="e23_seeds", seed=seed, source_tokens=len(self.enc(self.model, mat)))
            if r.get("memory"):
                r["memory_tokens"] = len(self.enc(self.model, r["memory"]))
            return r
        await self.gather([one(s, sd, m, c) for s in use for sd in SEEDS for m in ("aware", "blind")
                           for c in ("single", "filler", "long")])
        self.rows.sort(key=lambda r: r["seed"])            # stable: keeps the article / cell order within a seed
        self.finish(f"results/e23_{self.model}")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["e20", "e21", "e23"])
    ap.add_argument("--model", required=True, choices=MODELS)
    ap.add_argument("--concurrency", type=int, default=96)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    await getattr(E2x(args), args.cmd)()
    print(f"E2X_DONE {args.cmd} {args.model}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
