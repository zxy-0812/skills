#!/usr/bin/env python3
"""recall@1：召回列表里得分最高的一条(top-1)能直接命中 GT 的比例。

recalled_memories 已按 rerank_score 降序，top-1=下标0。命中以 eval match_details 为权威
（存在 sys_index==0 的匹配即 top-1 命中某 GT）。不需要 embedding，纯 eval 统计。

用法: python analyze_top1hit.py --eval-dir DIR --out-prefix PREFIX
产出: {out_prefix}_top1hit.csv + 终端比例（总体 / 按 correctness / 按 top-1 类型）
"""
from __future__ import annotations
import argparse, csv, json, os, collections
from pathlib import Path


def _txt(m): return (m.get("content") or m.get("summary") or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-dir", required=True); ap.add_argument("--out-prefix", required=True)
    a = ap.parse_args()
    files = sorted(os.path.join(a.eval_dir, n) for n in os.listdir(a.eval_dir)
                   if n.startswith("eval_") and n.endswith(".json") and not n.startswith("eval_summary_"))
    rows = []; tot = hit = 0; stat = collections.defaultdict(lambda: [0, 0])
    t_tot = collections.Counter(); t_hit = collections.Counter()
    for path in files:
        try:
            with open(path, encoding="utf-8") as fh: d = json.load(fh)
        except (json.JSONDecodeError, OSError): continue
        uid = str(d.get("user_id") or "").strip()
        for qa in d.get("qa_eval_results") or []:
            recalled = qa.get("recalled_memories") or []; gts = qa.get("expected_recall_memories") or []
            if not recalled or not gts: continue
            mds = (qa.get("recall_eval") or {}).get("match_details") or []
            top1 = recalled[0]; top1_md = next((m for m in mds if m.get("sys_index") == 0), None)
            hit1 = top1_md is not None; correct = qa.get("correctness_score")
            tot += 1; hit += int(hit1); stat[correct][0] += 1; stat[correct][1] += int(hit1)
            t_tot[top1.get("memory_type")] += 1
            if hit1: t_hit[top1.get("memory_type")] += 1
            rows.append({"user_id": uid, "eval_file": os.path.basename(path), "qa_index": qa.get("qa_index"),
                "correctness_score": correct, "recalled_count": len(recalled), "gt_count": len(gts),
                "top1_type": top1.get("memory_type"), "top1_status": top1.get("status"),
                "top1_rerank_score": round(top1.get("rerank_score") or 0.0, 4), "top1直接命中GT": hit1,
                "top1命中的gt_index": (top1_md.get("gt_index") if top1_md else ""),
                "query": qa.get("query") or "", "top1_content": _txt(top1)})
    cp = Path(f"{a.out_prefix}_top1hit.csv"); cp.parent.mkdir(parents=True, exist_ok=True)
    with open(cp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"有效QA(有GT且有召回): {tot}")
    print(f"top-1 直接命中 GT: {hit} → {hit/tot*100:.1f}%")
    print("\n按 correctness:")
    for c in sorted(stat, key=lambda x: (x is None, str(x))):
        t, h = stat[c]; print(f"  correctness={c}: {h}/{t} = {h/t*100:.1f}%")
    print("\n按 top-1 memory_type:")
    for mt, t in t_tot.most_common(): print(f"  {mt}: {t_hit.get(mt,0)}/{t} = {t_hit.get(mt,0)/t*100:.1f}%")
    print(f"CSV -> {cp}")


if __name__ == "__main__": raise SystemExit(main())
