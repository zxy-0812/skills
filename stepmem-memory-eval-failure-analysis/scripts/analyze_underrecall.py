#!/usr/bin/env python3
"""B 类（欠召回）病因深挖：库里有 active 记忆却没被判命中，卡在哪一环。

判别树（对每条 未命中 且 M*(库内最佳active匹配,sim>=PRESENT_TH) 的 GT）：
  病因3  M*.committed > 该QA召回时刻            —— 时序（召回早于写入）
  4d     need_recall=False                      —— 决策拒召（整题未检索）
  4c     M*.id ∈ recalled_memories              —— eval未对齐（其实召回了，评测口径）
  4a     retrieved_total >= rerank_top_n        —— 疑 top-k 截断
  4b     retrieved_total < rerank_top_n         —— 检索未命中（关键词/向量 miss）

需 recall 日志（按 query 文本 join）。产出 {out_prefix}_underrecall.csv + 终端病因分布。
"""
from __future__ import annotations
import argparse, csv, json, os, re, collections
from datetime import datetime
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
def _ts(s):
    if not s: return None
    s = str(s).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try: return datetime.strptime(s, fmt)
        except ValueError: continue
    return None


def index_recall_log(path):
    out = {}
    if not path or not os.path.isfile(path): return out
    for line in open(path, encoding="utf-8"):
        p = line.rstrip("\n").split("\t", 2)
        if len(p) < 3: continue
        try: o = json.loads(p[2])
        except json.JSONDecodeError: continue
        if o.get("endpoint") != "/auto_recall": continue
        ins = o.get("input_summary") or {}; mf = ins.get("messages_full") or []
        q = (mf[0].get("content") if mf else "").strip()
        rec = {"need_recall": None, "retrieved_total": None, "rerank_top_n": None, "by_type": {}, "keywords": []}
        for s in o.get("stages", []):
            f = s.get("fields") or {}
            if s.get("event") == "memory.auto_recall_decision": rec["need_recall"] = f.get("need_recall")
            if s.get("event") == "memory.auto_recall_retrieval_result":
                snap = f.get("retrieval_result_snapshot") or {}
                rec["retrieved_total"] = f.get("retrieved_total"); rec["rerank_top_n"] = f.get("rerank_top_n")
                rec["by_type"] = snap.get("retrieved_by_type_counts") or {}; rec["keywords"] = snap.get("keywords") or []
        out[q] = rec
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-dir", required=True); ap.add_argument("--memories-dir", required=True)
    ap.add_argument("--log-dir", required=True); ap.add_argument("--out-prefix", required=True)
    ap.add_argument("--model", required=True); ap.add_argument("--present-th", type=float, default=0.72)
    ap.add_argument("--batch-size", type=int, default=64)
    a = ap.parse_args(); TH = a.present_th
    print(f"加载 {a.model} …"); model = SentenceTransformer(a.model, device="cuda")
    dim = model.get_sentence_embedding_dimension()
    def emb(ts):
        if not ts: return np.zeros((0, dim), dtype=np.float32)
        return model.encode(ts, batch_size=a.batch_size, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).astype(np.float32)
    ed, md, ld = a.eval_dir, a.memories_dir, a.log_dir
    logpaths = {n[:-7]: os.path.join(ld, n) for n in os.listdir(ld) if n.endswith(".ndjson")}
    files = sorted(os.path.join(ed, n) for n in os.listdir(ed) if n.startswith("eval_") and n.endswith(".json") and not n.startswith("eval_summary_"))
    print(f"扫描 {len(files)} eval 文件…")
    rows = []; cause = collections.Counter(); dump = {}; logc = {}
    for fi, path in enumerate(files, 1):
        d = _load(path)
        if not d: continue
        uid = str(d.get("user_id") or "").strip()
        if uid not in dump:
            dp = os.path.join(md, f"{_safe(uid)}.json"); dd = _load(dp) if os.path.isfile(dp) else None
            mems = [m for m in (dd.get("memories") or []) if _txt(m)] if dd else []
            dump[uid] = (mems, emb([_txt(m) for m in mems]))
        mems, mvec = dump[uid]
        if uid not in logc: logc[uid] = index_recall_log(logpaths.get(uid))
        rlog = logc[uid]
        for qa in d.get("qa_eval_results") or []:
            if qa.get("correctness_score") != 0: continue
            re_ = qa.get("recall_eval") or {}
            matched = {m.get("gt_index") for m in (re_.get("match_details") or [])}
            recalled = qa.get("recalled_memories") or []
            rec_ids = {m.get("record_id") or m.get("memory_id") for m in recalled}
            rec_type_cnt = collections.Counter(m.get("memory_type") for m in recalled)
            q = (qa.get("query") or "").strip(); lg = rlog.get(q, {})
            qstart = _ts((qa.get("qa_timing") or {}).get("started_at"))
            rerank_cap = lg.get("rerank_top_n") or 10
            gts = qa.get("expected_recall_memories") or []
            gtexts = [(g.get("memory_content") or g.get("content") or "") for g in gts]; gvec = emb(gtexts)
            for i, gt in enumerate(gts):
                if i in matched: continue
                if not mvec.shape[0]: continue
                sims = mvec @ gvec[i]; bi = int(sims.argmax()); sem = float(sims[bi]); mstar = mems[bi]
                if sem < TH or (mstar.get("status") or "") not in RECALLABLE: continue  # 只看 B 类
                mid = mstar.get("memory_id") or mstar.get("record_id"); mt = mstar.get("memory_type", "?")
                committed = _ts(mstar.get("committed_at_ms")); need = lg.get("need_recall"); rtot = lg.get("retrieved_total")
                if committed and qstart and committed > qstart: c = "病因3·召回时M*尚未写入"
                elif need is False: c = "4d·recall决策判无需召回"
                elif mid in rec_ids: c = "4c·M*已召回但eval未判命中(对齐)"
                elif rtot is not None and rtot >= rerank_cap: c = "4a·检索未捞到·疑top-k截断"
                elif rtot is not None and rtot < rerank_cap: c = "4b·检索未捞到·关键词/向量miss"
                else: c = "4x·无recall日志"
                cause[c] += 1
                rows.append({"user_id": uid, "eval_file": os.path.basename(path), "qa_index": qa.get("qa_index"),
                    "gt_pos": i, "gt_memory_type": gt.get("memory_type", "?"), "M*_type": mt, "M*_status": mstar.get("status"),
                    "库内语义相似度": round(sem, 3), "欠召回病因": c, "need_recall": need, "retrieved_total": rtot,
                    "rerank_top_n": rerank_cap, "M*_in_recalled": mid in rec_ids,
                    "该类型_rerank前候选数": int((lg.get("by_type") or {}).get(mt, 0)), "该类型_最终召回数": int(rec_type_cnt.get(mt, 0)),
                    "recall_keywords": " / ".join(lg.get("keywords", [])), "query": q,
                    "gt_content": f"[{gt.get('memory_type','?')}]{gtexts[i]}", "M*_content": _txt(mstar), "recalled_count": len(recalled)})
        if fi % 20 == 0: print(f"  {fi}/{len(files)}  B行{len(rows)}")
    if not rows: print("无 B 类行"); return 0
    cp = Path(f"{a.out_prefix}_underrecall.csv"); cp.parent.mkdir(parents=True, exist_ok=True)
    with open(cp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    tot = len(rows)
    print(f"\n=== B类病因分布（共 {tot}）===")
    for k, v in cause.most_common(): print(f"  {k}: {v} ({v/tot*100:.1f}%)")
    print(f"CSV -> {cp}")


if __name__ == "__main__": raise SystemExit(main())
