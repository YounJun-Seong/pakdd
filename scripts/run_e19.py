"""Phase-6 E19 length-position control, generation (docs/phase6_prereg.md, 2026-11-23).
Aware / Blind x 3 position arms x 3 source lengths (data/longsource/e19_sources_v1.jsonl), B = 200, truncation-free,
four writes + reader; original prompts and the E15 matched prompt.
Outputs: results/e19_{model}.jsonl (all chains), _ok.jsonl (finals), _mem.jsonl (memories)."""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_longsource import render  # noqa: E402
from run_phase4 import MODELS  # noqa: E402
from run_phase5 import notrunc_chain  # noqa: E402
from run_rev import Runner, dump, ico, mem_rows  # noqa: E402
from supdrift.llm import LLMCache  # noqa: E402

FAM = {"original": {"aware": "aware", "blind": "blind"}, "matched": {"aware": "aware_m", "blind": "blind_m"}}


class E19(Runner):
    async def gen(self, budget, families):
        cache = LLMCache(f"cache/e19_{self.model}.jsonl")
        src = [json.loads(l) for l in open("data/longsource/e19_sources_v1.jsonl")]
        by = {s["sample_id"]: s for s in self.samples}
        src = [r for r in src if r["sample_id"] in by]
        print(f"sources: {len(src)} ({len({r['sample_id'] for r in src})} articles); budget {budget}; families {families}", flush=True)

        async def one(x, fam, mode):
            s = by[x["sample_id"]]; mat = render(x["blocks"])
            r = await notrunc_chain(self.model, s, [sp for b in x["blocks"] for sp in b["spans"]], FAM[fam][mode],
                                    f"{x['arm']}{x['level']}", budget, cache, self.sem, self.enc, material_override=mat)
            r.update(ico(s)); r.update(exp="e19_lenpos", family=fam, mode=mode, arm=x["arm"], level=x["level"],
                                       constructible=x["constructible"], source_tokens=len(self.enc(self.model, mat)))
            if r.get("memory"):
                r["memory_tokens"] = len(self.enc(self.model, r["memory"]))
            return r
        await self.gather([one(x, f, m) for x in src for f in families for m in ("aware", "blind")])
        stem = f"results/e19_{self.model}"
        dump(f"{stem}{self.tag}.jsonl", self.rows)
        ok = [r for r in self.rows if not r["failed"]]
        dump(f"{stem}_ok{self.tag}.jsonl", [{k: v for k, v in r.items() if k != "memory"} for r in ok])
        dump(f"{stem}_mem{self.tag}.jsonl", mem_rows(ok))
        print(f"  failed: {sum(r['failed'] for r in self.rows)} / {len(self.rows)}", flush=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=MODELS)
    ap.add_argument("--budget", type=int, default=200)
    ap.add_argument("--families", nargs="+", default=list(FAM), choices=list(FAM))
    ap.add_argument("--concurrency", type=int, default=96)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    await E19(args).gen(args.budget, args.families)
    print(f"E19_DONE {args.model}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
