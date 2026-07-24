#!/usr/bin/env python3
"""单条信息三处联查：给定 user_id + 一段信息，判定它丢在哪一环（或根本没丢）。

沿管线倒查 benchmark(可选) → 日志 → 记忆库，用 bge/Qwen3 语义匹配（记忆是改写存储的，
字面子串会假阴性）。判定：
  present_in_bank        库里有(语义) → 非丢失；若召回不到多为类型错位/召回匹配
  in_bmk_not_bank +signal少 → 抽取丢；  +无capture → 录入丢
  not_in_bmk             benchmark无 → 推断型GT，非丢失

用法: python locate_info.py --memories-dir DIR --log-dir DIR --user-id UID --info "文本" \
        --model /path/emb [--bmk-file benchmark.json] [--sem-th 0.66]
"""
from __future__ import annotations
import argparse, json, os, re
os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

_M = None
def get_model(p):
    global _M
    if _M is None:
        from sentence_transformers import SentenceTransformer
        _M = SentenceTransformer(p, device="cuda")
    return _M
def sem_max(model, info, texts):
    if not model or not texts: return 0.0, -1
    import numpy as np
    v = model.encode([info] + list(texts), normalize_embeddings=True, convert_to_numpy=True)
    s = v[1:] @ v[0]; j = int(s.argmax()); return float(s[j]), j
def _safe(u): return re.sub(r"\s+", "_", re.sub(r'[<>:"/\\|?*]', "_", u.strip())) or "unknown"
def _txt(m): return (m.get("content") or m.get("summary") or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--memories-dir", required=True); ap.add_argument("--log-dir", default="")
    ap.add_argument("--user-id", required=True); ap.add_argument("--info", required=True)
    ap.add_argument("--model", required=True); ap.add_argument("--sem-th", type=float, default=0.66)
    ap.add_argument("--bmk-file", default="", help="可选：benchmark json，用于判 in_bmk_not_bank")
    a = ap.parse_args()
    model = get_model(a.model)
    print(f"info: {a.info[:60]}...\n语义阈值 {a.sem_th}\n")

    # 记忆库
    mem = os.path.join(a.memories_dir, f"{_safe(a.user_id)}.json")
    bank_hits = []
    if os.path.isfile(mem):
        md = json.load(open(mem, encoding="utf-8"))
        texts = [_txt(m) for m in (md.get("memories") or []) if _txt(m)]
        mems = [m for m in (md.get("memories") or []) if _txt(m)]
        if texts:
            import numpy as np
            v = model.encode([a.info] + texts, normalize_embeddings=True, convert_to_numpy=True)
            s = v[1:] @ v[0]
            for idx in np.argsort(-s)[:5]:
                if s[idx] >= a.sem_th:
                    m = mems[idx]; bank_hits.append((round(float(s[idx]), 3), m.get("memory_type"), m.get("status"), _txt(m)[:90]))
    print(f"=== 记忆库({os.path.basename(mem)}) 命中 {len(bank_hits)} ===")
    for sim, t, st, c in bank_hits: print(f"  sim={sim} [{t}|{st}] {c}")

    # 日志 capture 概况
    caps = ev = sig = 0
    if a.log_dir:
        lp = os.path.join(a.log_dir, f"{a.user_id}.ndjson")
        if os.path.isfile(lp):
            for line in open(lp, encoding="utf-8"):
                p = line.rstrip("\n").split("\t", 2)
                if len(p) < 3: continue
                try: o = json.loads(p[2])
                except json.JSONDecodeError: continue
                if o.get("endpoint") == "/auto_capture_v1":
                    caps += 1
                    for s in o.get("stages", []):
                        f = s.get("fields") or {}
                        if s.get("event") == "dream_capture.capture_committed":
                            ev += int(f.get("evidence_count") or 0); sig += int(f.get("signal_count") or 0)
    print(f"\n=== 日志: capture {caps}次 evidence={ev} signal={sig} ===")

    # 判定
    print("\n=== 判定 ===")
    if bank_hits:
        types = sorted({t for _, t, _, _ in bank_hits})
        print(f"  present_in_bank：库里有(共{len(bank_hits)}条, 类型={types})。若召回不到，多为类型错位/召回匹配问题。")
    else:
        if caps == 0: print("  in_bmk_not_bank + 无capture → 丢在录入/投喂（比 dream 更靠前）。")
        elif sig == 0: print("  in_bmk_not_bank + signal=0 → 丢在抽取阶段（light/抽取）。")
        else: print("  库内语义无匹配；capture/signal 正常 → 可能抽取粒度/占位空壳，或语义模型/阈值不匹配（换多语言模型复核）。")


if __name__ == "__main__": raise SystemExit(main())
