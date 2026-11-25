"""E6 Contextual Evidence Robustness (docs/phase6_prereg.md, 2026-11-22): build the context-rich inputs.

For every candidate finding (target + the original distractors) of the 294 cohort articles:
  * locate the annotated evidence span in the article's full text (first occurrence in a BODY section,
    else the abstract; a span that cannot be located keeps its span-only text and is flagged),
  * local context = the rest of the span's own sentence plus up to 2 whole sentences before and 2 after,
    inside the same section, at most 100 reference tokens of whole sentences per side (nearest first),
  * provenance = article id, section path, and the intervention / comparator / outcome the span was
    annotated for (no direction, no significance, no marker of which candidate is the target).
Single = the target passage only. Multi = the identical target passage + the original distractor passages,
in the original per-article order. Nothing is removed for contamination: flags are recorded.

Outputs
  data/e6/e6_context_v1.jsonl          one row per article: ordered passages + rendered Single / Multi inputs
  results/e6/e6_context_manifest.csv   one row per candidate (location, context size, contamination flags)
  results/e6/e6_input_audit.csv        one row per article x condition (token lengths, counts, flags)
"""
import html
import json
import re
import sys
from pathlib import Path

import pandas as pd
import tiktoken

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_phase4 import load_materials, load_samples, spans_meta, tokenizers  # noqa: E402

ENC = tiktoken.get_encoding("o200k_base")
K_SENT, SIDE_CAP = 2, 100
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")
HEAD = re.compile(r"^\s*([A-Z][A-Z .&/,()–-]+):\s*$")
STAT = re.compile(r"\bp\s*[<>=≤]\s*0?\.\d|significan|confidence interval|\b95\s*%\s*CI\b|odds ratio|hazard ratio|"
                  r"relative risk", re.I)
OUT = Path("data/e6/e6_context_v1.jsonl")
RES = Path("results/e6")


def ntok(t):
    return len(ENC.encode(t, disallowed_special=()))


def norm(t):
    return re.sub(r"\s+", " ", html.unescape(html.unescape(t))).strip()


def sections(pmcid):
    """[(section path, normalized text)] in document order."""
    out, name = [], "FRONT"
    for line in open(f"data/fulltext/PMC{pmcid}.txt", encoding="utf-8", errors="ignore"):
        m = HEAD.match(line)
        if m:
            name = m.group(1).strip(); continue
        t = norm(line)
        if t:
            out.append((name, t))
    return out


def locate(secs, ev):
    """(section index, start, end) of the first occurrence in a BODY section, else anywhere; None if absent."""
    hits = [(i, t.find(ev)) for i, (_, t) in enumerate(secs) if ev in t]
    if not hits:
        return None
    body = [h for h in hits if secs[h[0]][0].startswith("BODY")]
    i, a = (body or hits)[0]
    return i, a, a + len(ev)


def window(text, a, b):
    """Context kept before / after the span [a, b): (pre, post, a0, b1, dropped_long)."""
    pre, post, dropped = text[:a], text[b:], False
    ps = SENT.split(pre) if pre.strip() else []
    frag_pre = ""
    if ps and not re.search(r"[.!?]\s*$", pre):
        frag_pre = ps.pop()                                   # lead-in of the span's own sentence
    qs = SENT.split(post) if post.strip() else []
    frag_post = ""
    if qs and not (re.search(r"[.!?]$", text[a:b].rstrip()) and re.match(r"\s+[A-Z(\[]", post)):
        frag_post = qs.pop(0)                                 # tail of the span's own sentence
    if ntok(frag_pre) > SIDE_CAP:
        frag_pre, ps, dropped = "", [], True
    if ntok(frag_post) > SIDE_CAP:
        frag_post, qs, dropped = "", [], True

    def take(sents):                                          # nearest first, <= K_SENT, <= SIDE_CAP tokens
        kept, tot = [], 0
        for s in sents[:K_SENT]:
            if tot + ntok(s) > SIDE_CAP:
                break
            kept.append(s); tot += ntok(s)
        return kept
    kp = list(reversed(take(list(reversed([s for s in ps if s.strip()])))))
    kq = take([s for s in qs if s.strip()])
    pre_txt = " ".join(kp + ([frag_pre] if frag_pre.strip() else [])).strip()
    post_txt = " ".join(([frag_post] if frag_post.strip() else []) + kq).strip()
    a0 = a - len(pre_txt) - (1 if pre_txt else 0)
    b1 = b + len(post_txt) + (1 if post_txt else 0)
    return pre_txt, post_txt, max(a0, 0), b1, dropped


def section_label(name):
    return " > ".join(p.strip().title() for p in name.replace("BODY.", "").split(".") if p.strip()) or "Unknown"


def passage(p, pre, ev, post, sec):
    body = " ".join(x for x in (pre, ev, post) if x)
    return (f"- [Intervention: {p['intervention']} | Comparator: {p['comparator']} | Outcome: {p['outcome']} | "
            f"Section: {sec}] {body}")


def render(pmcid, passages):
    return f"Excerpts from source article [PMC{pmcid}]:\n" + "\n".join(passages)


def main():
    samples, mats = load_samples(), load_materials()
    enc, _ = tokenizers()
    q14 = lambda t: len(enc("qwen3-14b", t))  # noqa: E731
    rows, manifest, audit = [], [], []
    for s in samples:
        secs = sections(s["pmcid"])
        items = spans_meta(s)                                  # original per-article order
        tid = s["target"]["prompt_id"]
        extra = [k for k in mats[s["sample_id"]]["kpool"]
                 if k["prompt_id"] not in {p["prompt_id"] for p, _ in items}]
        loc = {p["prompt_id"]: locate(secs, norm(ev)) for p, ev in items}
        loc_extra = {k["prompt_id"]: locate(secs, norm(k["evidence"])) for k in extra}
        cands = []
        for pos, (p, ev) in enumerate(items):
            L = loc[p["prompt_id"]]
            if L is None:
                pre = post = ""; sec = "not located"; a0 = b1 = None; dropped = False
            else:
                i, a, b = L
                pre, post, a0, b1, dropped = window(secs[i][1], a, b)
                sec = section_label(secs[i][0])
            ctx = (pre + " " + post).strip()

            def hits(other_loc, other_ev):                     # does this context contain (part of) another span?
                if L is not None and other_loc is not None and other_loc[0] == L[0]:
                    oa, ob = other_loc[1], other_loc[2]
                    return (oa < L[1] and ob > a0) or (ob > L[2] and oa < b1)   # overlaps pre or post range
                return len(other_ev) >= 40 and norm(other_ev)[:40] in ctx
            others = [(q, e) for q, e in items if q["prompt_id"] != p["prompt_id"] and norm(e) != norm(ev)]
            ov_cand = [q["prompt_id"] for q, e in others if hits(loc[q["prompt_id"]], e)]
            ov_extra = [k["prompt_id"] for k in extra if norm(k["evidence"]) != norm(ev)
                        and hits(loc_extra[k["prompt_id"]], k["evidence"])]
            n_stat = sum(bool(STAT.search(x)) for x in SENT.split(ctx)) if ctx else 0
            cands.append({"prompt_id": p["prompt_id"], "role": "target" if p["prompt_id"] == tid else "distractor",
                          "position": pos, "passage": passage(p, pre, ev, post, sec), "evidence": ev,
                          "located": L is not None, "section": sec, "pre": pre, "post": post})
            manifest.append({
                "sample_id": s["sample_id"], "pmcid": s["pmcid"], "prompt_id": p["prompt_id"], "role": cands[-1]["role"],
                "position": pos, "gold_label": p["gold_label"], "located": L is not None, "section": sec,
                "in_body": bool(L and secs[L[0]][0].startswith("BODY")),
                "span_tokens": ntok(ev), "pre_tokens": ntok(pre), "post_tokens": ntok(post),
                "context_tokens": ntok(pre) + ntok(post), "passage_tokens": ntok(cands[-1]["passage"]),
                "context_dropped_long_sentence": dropped,
                "ctx_overlaps_candidate": bool(ov_cand), "ctx_overlaps_candidate_ids": " ".join(map(str, ov_cand)),
                "ctx_overlaps_target": tid in ov_cand,
                "ctx_overlaps_other_annotated": bool(ov_extra), "ctx_overlaps_other_annotated_ids": " ".join(map(str, ov_extra)),
                "ctx_stat_sentences": n_stat,
                "evidence_identical_to_other_candidate": any(norm(e) == norm(ev) and q["prompt_id"] != p["prompt_id"] for q, e in items),
            })
        tgt = next(c for c in cands if c["role"] == "target")
        single = render(s["pmcid"], [tgt["passage"]])
        multi = render(s["pmcid"], [c["passage"] for c in cands])
        assert tgt["passage"] in multi and s["target"]["evidence"] in single
        rows.append({"sample_id": s["sample_id"], "pmcid": s["pmcid"], "candidates": cands, "single": single, "multi": multi})
        mrows = [m for m in manifest if m["sample_id"] == s["sample_id"]]
        tm = next(m for m in mrows if m["role"] == "target")
        dm = [m for m in mrows if m["role"] == "distractor"]
        span_only = {"single": f"Excerpts from source article [PMC{s['pmcid']}]:\n- {s['target']['evidence']}",
                     "multi": f"Excerpts from source article [PMC{s['pmcid']}]:\n" + "\n".join(f"- {e}" for _, e in items)}
        for cond, text in (("single", single), ("multi", multi)):
            use = [tm] if cond == "single" else mrows
            audit.append({
                "sample_id": s["sample_id"], "pmcid": s["pmcid"], "cond": cond, "n_candidates": len(use),
                "n_unique_spans": len({norm(e) for p, e in items if cond == "multi" or p["prompt_id"] == tid}),
                "input_tokens_ref": ntok(text), "input_tokens_qwen14b": q14(text),
                "span_only_tokens_ref": ntok(span_only[cond]), "span_only_tokens_qwen14b": q14(span_only[cond]),
                "context_tokens_ref": sum(m["context_tokens"] for m in use),
                "n_unlocated": sum(not m["located"] for m in use), "target_located": tm["located"],
                "n_identical_evidence": sum(m["evidence_identical_to_other_candidate"] for m in use) if cond == "multi" else 0,
                "n_ctx_overlapping_candidate": sum(m["ctx_overlaps_candidate"] for m in use) if cond == "multi" else 0,
                # contamination of the Single input: a finding other than the target enters through the target context
                "single_contam_annotated": tm["ctx_overlaps_candidate"] or tm["ctx_overlaps_other_annotated"],
                "single_contam_stat_sentence": tm["ctx_stat_sentences"] > 0,
                # Multi only: the target finding is repeated inside a distractor's context
                "target_repeated_in_distractor_ctx": any(m["ctx_overlaps_target"] for m in dm) if cond == "multi" else False,
            })
    OUT.parent.mkdir(parents=True, exist_ok=True); RES.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    M, A = pd.DataFrame(manifest), pd.DataFrame(audit)
    M.to_csv(RES / "e6_context_manifest.csv", index=False); A.to_csv(RES / "e6_input_audit.csv", index=False)
    print(f"wrote {OUT} ({len(rows)} articles), manifest {len(M)} candidates, audit {len(A)} rows")
    print(f"located {M.located.mean():.1%} (targets {M[M.role == 'target'].located.mean():.1%}); in BODY {M.in_body.mean():.1%}; "
          f"context tokens per candidate mean {M.context_tokens.mean():.0f} (zero context {(M.context_tokens == 0).mean():.1%}); "
          f"long-sentence drops {M.context_dropped_long_sentence.mean():.1%}")
    for c in ("single", "multi"):
        a = A[A.cond == c]
        print(f"  {c}: input {a.input_tokens_ref.mean():.0f} ref / {a.input_tokens_qwen14b.mean():.0f} 14B tokens "
              f"(span-only {a.span_only_tokens_ref.mean():.0f} / {a.span_only_tokens_qwen14b.mean():.0f}); "
              f"p10–p90 {a.input_tokens_qwen14b.quantile(.1):.0f}–{a.input_tokens_qwen14b.quantile(.9):.0f}, max {a.input_tokens_qwen14b.max()}; "
              f"candidates {a.n_candidates.mean():.2f}, unique spans {a.n_unique_spans.mean():.2f}")
    a = A[A.cond == "single"]
    print(f"  Single contamination: annotated finding in target context {a.single_contam_annotated.mean():.1%}; "
          f"statistical sentence in target context {a.single_contam_stat_sentence.mean():.1%}; "
          f"either {(a.single_contam_annotated | a.single_contam_stat_sentence).mean():.1%}")
    a = A[A.cond == "multi"]
    print(f"  Multi: articles with identical evidence across candidates {(a.n_identical_evidence > 0).mean():.1%}; "
          f"with a context overlapping another candidate {(a.n_ctx_overlapping_candidate > 0).mean():.1%}; "
          f"target repeated in a distractor context {a.target_repeated_in_distractor_ctx.mean():.1%}; "
          f"articles with an unlocated candidate {(a.n_unlocated > 0).mean():.1%}")


if __name__ == "__main__":
    main()
