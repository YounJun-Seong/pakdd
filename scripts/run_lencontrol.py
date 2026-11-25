"""Phase-6 E14 length-matched control, generation (docs/phase6_prereg.md, 2026-11-22).
Aware / Blind x Filler-long, budgets 100/200/400/800, truncation-free; constructible sources only.
Outputs: results/lenctrl_{model}.jsonl (all chains), _ok.jsonl (finals), _mem.jsonl (memories)."""
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

BUDGETS = [100, 200, 400, 800]


class LenCtrl(Runner):
    async def gen(self):
        cache = LLMCache(f"cache/ratio_{self.model}.jsonl")
        F = {json.loads(l)["sample_id"]: json.loads(l) for l in open("data/longsource/longfiller_v1.jsonl")}
        use = [s for s in self.samples if F[s["sample_id"]]["constructible"]]
        print(f"constructible sources: {len(use)}", flush=True)

        async def one(s, b, mode):
            L = F[s["sample_id"]]
            mat = render(L["blocks"])
            r = await notrunc_chain(self.model, s, [sp for bl in L["blocks"] for sp in bl["spans"]], mode, "filler", b,
                                    cache, self.sem, self.enc, material_override=mat)
            r.update(ico(s)); r.update(exp="lenctrl", source_tokens=len(self.enc(self.model, mat)))
            if r.get("memory"):
                r["memory_tokens"] = len(self.enc(self.model, r["memory"]))
            return r
        await self.gather([one(s, b, m) for s in use for b in BUDGETS for m in ("aware", "blind")])
        dump(f"results/lenctrl_{self.model}{self.tag}.jsonl", self.rows)
        ok = [r for r in self.rows if not r["failed"]]
        dump(f"results/lenctrl_{self.model}_ok{self.tag}.jsonl", [{k: v for k, v in r.items() if k != "memory"} for r in ok])
        dump(f"results/lenctrl_{self.model}_mem{self.tag}.jsonl", mem_rows(ok))
        for b in BUDGETS:
            for m in ("aware", "blind"):
                g = [r for r in self.rows if r["budget"] == b and r["mode"] == m]
                print(f"  B={b} {m}/filler: failed {sum(r['failed'] for r in g) / len(g):.1%}", flush=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=MODELS)
    ap.add_argument("--concurrency", type=int, default=48)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    await LenCtrl(args).gen()
    print(f"LENCTRL_DONE {args.model}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
