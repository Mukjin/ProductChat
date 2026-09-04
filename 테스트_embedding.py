# -*- coding: utf-8 -*-
"""qwen3-embedding:0.6b 로 학습데이터 질문 매칭 테스트.

사용:
  python 테스트_embedding.py
  첫 실행은 색인에 1~3분. 이후는 질문을 입력하면 바로 결과가 나옵니다.
  끝내려면 빈 줄 또는 q
"""
import json
import math
import sys
import urllib.request
from pathlib import Path

import pandas as pd

MODEL = "qwen3-embedding:0.6b"
EXCEL = Path(r"C:\Users\mm704\OneDrive\Desktop\구매챗봇\TTA_구매챗봇_학습데이터_통합_0901.xlsx")
CACHE = Path(r"C:\Users\mm704\OneDrive\Desktop\구매챗봇\테스트_embedding_index.json")
QUERY_PREFIX = (
    "Instruct: Given a Korean procurement FAQ query, retrieve the matching stored question.\nQuery: "
)
REFUSE_BELOW = 0.55


def embed(text: str) -> list[float]:
    body = json.dumps({"model": MODEL, "input": text}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/embed",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["embeddings"][0]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def load_rows() -> list[dict]:
    df = pd.read_excel(EXCEL, sheet_name=0, header=2, dtype=str)
    rows = []
    for _, r in df.iterrows():
        qid = str(r.iloc[0]).strip() if pd.notna(r.iloc[0]) else ""
        cat = str(r.iloc[1]).strip() if pd.notna(r.iloc[1]) else ""
        q = str(r.iloc[2]).strip() if pd.notna(r.iloc[2]) else ""
        if not qid or qid.startswith("▶") or not q or q == "nan":
            continue
        rows.append({"qid": qid, "cat": cat, "q": q})
    return rows


def build_index(rows: list[dict]) -> list[dict]:
    if CACHE.exists():
        cached = json.loads(CACHE.read_text(encoding="utf-8"))
        if cached.get("model") == MODEL and len(cached.get("rows", [])) == len(rows):
            print("저장된 색인을 씁니다.")
            return cached["rows"]
    print("질문을 색인합니다. 1~3분 걸릴 수 있습니다...")
    for i, row in enumerate(rows):
        row["vec"] = embed(row["q"])
        if (i + 1) % 40 == 0:
            print(f"  {i + 1}/{len(rows)}")
    CACHE.write_text(
        json.dumps({"model": MODEL, "rows": rows}, ensure_ascii=False),
        encoding="utf-8",
    )
    print("색인 저장 완료.")
    return rows


def search(query: str, rows: list[dict], k: int = 3) -> list[tuple[float, dict]]:
    qv = embed(QUERY_PREFIX + query)
    ranked = sorted(
        ((cosine(qv, r["vec"]), r) for r in rows),
        key=lambda x: x[0],
        reverse=True,
    )
    return ranked[:k]


def show(query: str, rows: list[dict]) -> None:
    ranked = search(query, rows)
    top_s, top = ranked[0]
    if top_s < REFUSE_BELOW:
        print(f"\n거절 (점수 {top_s:.3f} < {REFUSE_BELOW})")
        print("자료에 없는 내용으로 보고 구매팀에 문의하는 쪽입니다.\n")
    else:
        print(f"\n매칭: {top['qid']}  ({top['cat']})")
        print(f"질문: {top['q']}")
        print(f"점수: {top_s:.3f}")
        print("이 QID의 DB 답 + PDF + 캡처를 보여 주면 됩니다.\n")
    print("가까운 후보:")
    for s, r in ranked:
        print(f"  {s:.3f}  {r['qid']}  {r['q']}")
    print()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    try:
        embed("ping")
    except Exception as e:
        print("Ollama가 안 켜져 있습니다. 트레이의 Ollama를 실행한 뒤 다시 시도하세요.")
        print(e)
        return
    rows = build_index(load_rows())
    print()
    print("구매 관련 질문을 입력하세요. 끝내려면 q 또는 빈 줄.")
    print("예: 검수는 경영정보 어디서 해요")
    print()
    while True:
        try:
            q = input("질문> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q or q.lower() == "q":
            break
        show(q, rows)


if __name__ == "__main__":
    main()
