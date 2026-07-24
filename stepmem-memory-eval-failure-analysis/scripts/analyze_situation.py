#!/usr/bin/env python3
"""记忆系统评测：失败四类归因（A/B/C/D）+ 语义分档 + 结论列。

对 correctness_score==0 的每条 GT，用 embedding 对全量记忆库(所有状态)检索最相似 M*：
  A 召回错位/答错   —— GT 已被 eval match_details 命中，但整题 correctness=0
  B 欠召回          —— 未命中，sim(GT,M*)>=PRESENT_TH 且 M*.status=active
  C 状态不可召回     —— 未命中，sim>=PRESENT_TH 但 M* 状态非 active
  D 真缺失          —— 未命中，sim<PRESENT_TH（追加 log 诊断）

三套数据按 user_id 关联：eval.user_id == 记忆库文件名stem == 日志文件名stem。

🚨 PRESENT_TH 须按 embedding 模型重标定：先用默认跑一遍，再用"命中GT"的 sim p5 设阈值
（见 --calibrate 会打印 p5 建议值）。bge-small-zh 中文≈0.72；Qwen3-0.6B 英文≈0.66。

用法:
  python analyze_situation.py --eval-dir DIR --memories-dir DIR --log-dir DIR \
    --out-prefix PREFIX --model /path/to/embedding [--present-th 0.66] [--all-qa] [--calibrate]
产出: {out_prefix}_situation.csv + {out_prefix}_situation.md
"""
from __future__ import annotations
import argparse, csv, json, os, re, collections
from pathlib import Path
os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
import numpy as np
from sentence_transformers import SentenceTransformer

RECALLABLE = {"active"}


def _safe(u): return re.sub(r"\s+", "_", re.sub(r'[<>:"/\\|?*]', "_", u.strip())) or "unknown"
def _txt(m): return (m.get("content") or m.get("summary") or "").strip()
def _load(p):
    try:
        with open(p, encoding="utf-8") as f: return json.load(f)
    except (json.JSONDecodeError, OSError): return None


def diagnose_log(path):
    if not path or not os.path.isfile(path): return "无对应 log 文件"
    caps = ev = sig = 0; errs = 0
    for line in open(path, encoding="utf-8"):
        p = line.rstrip("\n").split("\t", 2)
        if len(p) < 3: continue
        try: o = json.loads(p[2])
        except json.JSONDecodeError: continue
        if o.get("status") in ("error", "failed"): errs += 1
        if o.get("endpoint") == "/auto_capture_v1":
            caps += 1
            for s in o.get("stages", []):
                f = s.get("fields") or {}
                if s.get("event") == "dream_capture.capture_committed":
                    ev += int(f.get("evidence_count") or 0); sig += int(f.get("signal_count") or 0)
    if caps == 0: return "未见 capture 调用（录入/捕获缺失）"
    msg = f"capture {caps}次 evidence={ev} signal={sig}"
    if sig == 0: msg += "；signal=0 → 抽取未产出结构化记忆"
    if errs: msg += f"；{errs}处error"
    return msg


def list_eval_files(ed):
    return sorted(os.path.join(ed, n) for n in os.listdir(ed)
                  if n.startswith("eval_") and n.endswith(".json") and not n.startswith("eval_summary_"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-dir", required=True)
    ap.add_argument("--memories-dir", required=True)
    ap.add_argument("--log-dir", default="")
    ap.add_argument("--out-prefix", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--present-th", type=float, default=0.72)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--all-qa", action="store_true", help="分析全部QA而非仅失败")
    ap.add_argument("--calibrate", action="store_true", help="打印命中GT的sim分位，用于标定阈值")
    a = ap.parse_args()
    TH = a.present_th

    print(f"加载 {a.model} …")
    model = SentenceTransformer(a.model, device="cuda")
    dim = model.get_sentence_embedding_dimension()
    def emb(ts):
        if not ts: return np.zeros((0, dim), dtype=np.float32)
        return model.encode(ts, batch_size=a.batch_size, normalize_embeddings=True,
                            convert_to_numpy=True, show_progress_bar=False).astype(np.float32)

    ed, md, ld = a.eval_dir, a.memories_dir, a.log_dir
    logpaths = {n[:-7]: os.path.join(ld, n) for n in os.listdir(ld) if n.endswith(".ndjson")} if ld and os.path.isdir(ld) else {}
    files = list_eval_files(ed)
    print(f"扫描 {len(files)} eval 文件… log索引 {len(logpaths)}")

    rows = []; cat = collections.Counter(); dump = {}; logdiag = {}; hit_sims = []
    for fi, path in enumerate(files, 1):
        d = _load(path)
        if not d: continue
        uid = str(d.get("user_id") or "").strip()
        if uid not in dump:
            dp = os.path.join(md, f"{_safe(uid)}.json")
            dd = _load(dp) if os.path.isfile(dp) else None
            mems = [m for m in (dd.get("memories") or []) if _txt(m)] if dd else []
            dump[uid] = (mems, emb([_txt(m) for m in mems]))
        mems, mvec = dump[uid]
        for qa in d.get("qa_eval_results") or []:
            correct = qa.get("correctness_score")
            if not a.all_qa and correct != 0: continue
            re_ = qa.get("recall_eval") or {}
            matched = {m.get("gt_index") for m in (re_.get("match_details") or [])}
            recalled = qa.get("recalled_memories") or []
            rtexts = [_txt(m) for m in recalled]; rvec = emb(rtexts)
            recalled_all = "\n".join(f"{j+1}. [{m.get('memory_type')}|{m.get('status')}]{_txt(m)}" for j, m in enumerate(recalled))
            gts = qa.get("expected_recall_memories") or []
            gtexts = [(g.get("memory_content") or g.get("content") or "") for g in gts]
            gvec = emb(gtexts)
            for i, gt in enumerate(gts):
                sem, mstar = 0.0, None
                if mvec.shape[0]:
                    sims = mvec @ gvec[i]; bi = int(sims.argmax()); sem = float(sims[bi]); mstar = mems[bi]
                sem_rec, rrec = 0.0, None
                if rvec.shape[0]:
                    s2 = rvec @ gvec[i]; bj = int(s2.argmax()); sem_rec = float(s2[bj]); rrec = recalled[bj]
                hit = i in matched
                st = (mstar.get("status") if mstar else "") or ""
                if hit: hit_sims.append(sem)
                if hit: concl = "A·召回错位/答错"
                elif sem >= TH and st == "active": concl = "B·欠召回"
                elif sem >= TH and st and st != "active": concl = f"C·状态不可召回({st})"
                else: concl = "D·真缺失"
                if hit: tier = "命中(召回成功)"
                elif sem >= 0.9: tier = "未命中·库里基本有同款(≥0.90)"
                elif sem >= 0.8: tier = "未命中·库里有强相关(0.80-0.90)"
                elif sem >= TH: tier = f"未命中·库里有相关(≥{TH})"
                else: tier = f"未命中·真缺失(<{TH})"
                ldiag = ""
                if concl.startswith("D"):
                    if uid not in logdiag: logdiag[uid] = diagnose_log(logpaths.get(uid))
                    ldiag = logdiag[uid]
                cat[concl.split("(")[0]] += 1
                rows.append({"user_id": uid, "eval_file": os.path.basename(path), "qa_index": qa.get("qa_index"),
                    "tag": qa.get("tag"), "difficulty": qa.get("difficulty"), "should_recall": qa.get("should_recall"),
                    "correctness_score": correct, "recall_memory_score": qa.get("recall_memory_score"),
                    "recall_rate_at_n4": re_.get("recall_rate_at_n4"), "gt_pos": i,
                    "gt_memory_type": gt.get("memory_type", "?"), "命中": hit, "失败归因": concl, "语义档": tier,
                    "库内语义相似度": round(sem, 3), "召回内语义相似度": round(sem_rec, 3),
                    "库内最相似类型": mstar.get("memory_type") if mstar else "", "库内最相似状态": st,
                    "真缺失_log诊断": ldiag, "query": qa.get("query") or "", "ground_truth": qa.get("ground_truth") or "",
                    "gpt_answer": qa.get("gpt_answer") or "", "gt_content": f"[{gt.get('memory_type','?')}]{gtexts[i]}",
                    "库内最相似记忆": _txt(mstar) if mstar else "",
                    "召回内最相似": (f"[{rrec.get('memory_type')}|{rrec.get('status')}]{_txt(rrec)}" if rrec else ""),
                    "recalled_count": len(recalled), "recalled_all": recalled_all})
        if fi % 20 == 0: print(f"  {fi}/{len(files)}  行{len(rows)}")

    if not rows: print("无匹配行"); return 0
    cp = Path(f"{a.out_prefix}_situation.csv"); cp.parent.mkdir(parents=True, exist_ok=True)
    with open(cp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    tot = len(rows); ORDER = ["A·召回错位/答错", "B·欠召回", "C·状态不可召回", "D·真缺失"]
    mdl = [f"# 失败归因（{'全部QA' if a.all_qa else 'correctness=0'}）\n",
           f"- Embedding={Path(a.model).name}｜PRESENT_TH={TH}｜仅 active 可召回｜命中以 eval match_details 为准",
           f"- 失败 GT 总数 **{tot}**\n", "## 四类归因\n| 归因 | 条数 | 占比 |\n|---|---|---|"]
    for k in ORDER: mdl.append(f"| {k} | {cat.get(k,0)} | {cat.get(k,0)/tot*100:.1f}% |")
    Path(f"{a.out_prefix}_situation.md").write_text("\n".join(mdl), encoding="utf-8")

    print("\n=== 四类归因 ===")
    for k in ORDER: print(f"  {k}: {cat.get(k,0)} ({cat.get(k,0)/tot*100:.1f}%)")
    if a.calibrate and hit_sims:
        h = np.array(hit_sims)
        print(f"\n[标定] 命中GT sim: min={h.min():.3f} p5={np.percentile(h,5):.3f} "
              f"p10={np.percentile(h,10):.3f} med={np.median(h):.3f}  → 建议 PRESENT_TH≈p5={np.percentile(h,5):.2f}")
    print(f"CSV -> {cp}")


if __name__ == "__main__": raise SystemExit(main())
