"""Phase-6 E13 compression-ratio experiment, generation (docs/phase6_prereg.md, 2026-11-22).

Source fixed at ~1,000 tokens (data/longsource/longsource_v1.jsonl), budgets 100 / 200 / 400 / 800.

  enforced --model M   Aware/Blind x Single/Long at every budget, enforced protocol (+ blind_plural, Long,
                       B=200; + the final answer straight from the untruncated long source)
  notrunc  --model M   the same cells, truncation-free protocol (E3b)
  labels   --model M   judge-free direct label from every memory written above (E4 protocol)

Outputs: results/ratio_{model}.jsonl (+ _mem), ratio_answers_{model}.jsonl,
         ratio_notrunc_{model}.jsonl (+ _ok, _mem), ratio_labels_{model}.jsonl
Every row carries the target ICO and gold label (score_generic.py --self-ico).
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_longsource import render  # noqa: E402
from run_phase4 import MODELS, chain, spans_original  # noqa: E402
from run_phase5 import answer_from, notrunc_chain  # noqa: E402
from run_rev import LABEL_SYSTEM, LABEL_USER, Runner, dump, ico, mem_rows, parse_label  # noqa: E402
from supdrift.llm import LLMCache, chat, full_cache_key  # noqa: E402

BUDGETS = [100, 200, 400, 800]
CELLS = [(m, c) for m in ("aware", "blind") for c in ("single", "long")]
PLURAL_BUDGET = 200


def load_long():
    return {json.loads(l)["sample_id"]: json.loads(l) for l in open("data/longsource/longsource_v1.jsonl")}


class Ratio(Runner):
    def __init__(self, args):
        super().__init__(args)
        self.long = load_long()
        self.cache = LLMCache(f"cache/ratio_{self.model}.jsonl")

    def m0(self, s, cond):
        """(spans, material_override): Single is the unchanged target-only source."""
        if cond == "single":
            return spans_original(s, "single"), None
        L = self.long[s["sample_id"]]
        return [sp for b in L["blocks"] for sp in b["spans"]], render(L["blocks"])

    def extra(self, s, cond, material):
        L = self.long[s["sample_id"]]
        return {**ico(s), "source_tokens": len(self.enc(self.model, material)),
                **({"n_findings": L["n_findings"], "target_pos": L["target_span_start"]} if cond == "long" else {})}

    # ------------------------------------------------------------ enforced
    async def enforced(self):
        from run_phase4 import material_text

        async def one(s, b, mode, cond):
            spans, mat = self.m0(s, cond)
            r = await chain(self.model, s, spans, mode=mode, budget=b, depth=5, cache=self.cache, sem=self.sem,
                            enc=self.enc, dec=self.dec, exp="ratio", cond=cond, material_override=mat)
            r.update(self.extra(s, cond, mat or material_text(s["pmcid"], spans)))
            return r

        async def full(s):
            mat = render(self.long[s["sample_id"]]["blocks"])
            text = await answer_from(self.model, s, mat, s["target"], self.cache, self.sem, "ratio-full_long")
            return {"sample_id": s["sample_id"], **ico(s), "source": "full_long", "text": text}

        jobs = [one(s, b, m, c) for s in self.samples for b in BUDGETS for m, c in CELLS]
        jobs += [one(s, PLURAL_BUDGET, "blind_plural", "long") for s in self.samples]
        n_chain = len(jobs)
        jobs += [full(s) for s in self.samples]
        await self.gather(jobs)
        ch = [r for r in self.rows if "steps" in r]
        assert len(ch) == n_chain
        dump(f"results/ratio_{self.model}{self.tag}.jsonl", ch)
        dump(f"results/ratio_{self.model}_mem{self.tag}.jsonl", mem_rows(ch))
        dump(f"results/ratio_answers_{self.model}{self.tag}.jsonl", [r for r in self.rows if "steps" not in r])
        for b in BUDGETS:
            for m, c in CELLS:
                g = [r for r in ch if r["budget"] == b and r["mode"] == m and r["cond"] == c]
                print(f"  B={b} {m}/{c}: forced {sum(r['forced'] for r in g) / len(g):.1%}, M4 raw length "
                      f"{sum(r['steps'][-1]['raw_tokens'] for r in g) / len(g):.0f}", flush=True)

    # ------------------------------------------------------------ truncation-free
    async def notrunc(self):
        from run_phase4 import material_text

        async def one(s, b, mode, cond):
            spans, mat = self.m0(s, cond)
            r = await notrunc_chain(self.model, s, spans, mode, cond, b, self.cache, self.sem, self.enc,
                                    material_override=mat)
            r["exp"] = "ratio_notrunc"
            r.update(self.extra(s, cond, mat or material_text(s["pmcid"], spans)))
            return r
        await self.gather([one(s, b, m, c) for s in self.samples for b in BUDGETS for m, c in CELLS])
        dump(f"results/ratio_notrunc_{self.model}{self.tag}.jsonl", self.rows)
        ok = [r for r in self.rows if not r["failed"]]
        dump(f"results/ratio_notrunc_{self.model}_ok{self.tag}.jsonl", [{k: v for k, v in r.items() if k != "memory"} for r in ok])
        dump(f"results/ratio_notrunc_{self.model}_mem{self.tag}.jsonl", mem_rows(ok))
        for b in BUDGETS:
            for m, c in CELLS:
                g = [r for r in self.rows if r["budget"] == b and r["mode"] == m and r["cond"] == c]
                print(f"  B={b} {m}/{c}: failed {sum(r['failed'] for r in g) / len(g):.1%}", flush=True)

    # ------------------------------------------------------------ judge-free labels
    async def labels(self):
        m = self.model
        ids = {s["sample_id"]: s for s in self.samples}

        async def one(s, source, memory, extra):
            t = s["target"]
            q = {k: t[k] for k in ("intervention", "comparator", "outcome")}
            key = full_cache_key(m, {"task": "rev_label", "sid": s["sample_id"], "pid": t["prompt_id"], "material": memory})
            raw = (await chat(m, [{"role": "system", "content": LABEL_SYSTEM},
                                  {"role": "user", "content": LABEL_USER.format(material=memory, **q)}],
                              cache=self.cache, cache_key=key, sem=self.sem, temperature=0.0, seed=42, max_tokens=8)).strip()
            pred = parse_label(raw)
            return {"sample_id": s["sample_id"], "source": source, **extra, "gold_label": t["gold_label"],
                    "label_raw": raw, "pred_label": pred, "correct": pred == t["gold_label"]}

        jobs = []
        for path, src in ((f"results/ratio_{m}{self.tag}.jsonl", "enforced"), (f"results/ratio_notrunc_{m}{self.tag}.jsonl", "notrunc")):
            if not Path(path).exists():
                print(f"  (skipping {path}: not generated yet)", flush=True); continue
            for r in map(json.loads, open(path)):
                if r["sample_id"] in ids and r.get("memory"):
                    jobs.append(one(ids[r["sample_id"]], src, r["memory"],
                                    {"mode": r["mode"], "cond": r["cond"], "budget": r["budget"]}))
        for s in self.samples:
            jobs.append(one(s, "full_long", render(self.long[s["sample_id"]]["blocks"]), {}))
        await self.gather(jobs)
        dump(f"results/ratio_labels_{m}{self.tag}.jsonl", self.rows)
        up = sum(r["pred_label"] == "UNPARSED" for r in self.rows)
        print(f"  unparsed labels: {up} / {len(self.rows)}", flush=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["enforced", "notrunc", "labels"])
    ap.add_argument("--model", required=True, choices=MODELS)
    ap.add_argument("--concurrency", type=int, default=24)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    r = Ratio(args)
    await getattr(r, args.cmd)()
    print(f"RATIO_DONE {args.cmd} {args.model}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
