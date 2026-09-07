# -*- coding: utf-8 -*-
"""GitHub Pages용 정적 사이트(docs/)를 만든다. 벡터·서버 없이 글자 검색용 FAQ JSON."""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "web"))

from server import (  # noqa: E402
    BY_QID,
    CACHE,
    CAPTURES_DIR,
    FORMS_DIR,
    INDEX,
    META,
    bigrams,
    capture_steps,
    form_files,
    load_index,
    load_meta,
)


def main() -> None:
    global INDEX, META, BY_QID
    docs = ROOT / "docs"
    if docs.exists():
        shutil.rmtree(docs)
    docs.mkdir(parents=True)
    (docs / "data").mkdir()
    (docs / "forms").mkdir()
    (docs / "captures").mkdir()

    INDEX[:] = load_index()
    META.clear()
    META.update(load_meta())
    BY_QID.clear()
    BY_QID.update({row["qid"]: row for row in INDEX})

    rows = []
    for row in INDEX:
        extra = META.get(row["qid"], {})
        forms = form_files(extra.get("forms") or [])
        for f in forms:
            if f.get("url"):
                f["url"] = f"./forms/{f['file']}"
        caps = capture_steps(row["qid"], extra.get("capture_notes") or [])
        for c in caps:
            if c.get("url"):
                c["url"] = f"./captures/{row['qid']}/{c['file']}"
        bi = sorted(bigrams(row["q"]))
        rows.append(
            {
                "qid": row["qid"],
                "cat": row.get("cat") or "",
                "q": row["q"],
                "bi": bi,
                "answer": extra.get("answer") or "",
                "forms": forms,
                "captures": caps,
                "capture_notes": extra.get("capture_notes") or [],
                "similar": extra.get("similar") or [],
                "rule": extra.get("rule") or "",
                "law": extra.get("law") or "",
            }
        )

    payload = {
        "model": "keyword-only",
        "source": CACHE.name,
        "count": len(rows),
        "rows": rows,
    }
    (docs / "data" / "faq.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )

    if FORMS_DIR.exists():
        for path in FORMS_DIR.iterdir():
            if path.is_file():
                shutil.copy2(path, docs / "forms" / path.name)
    if CAPTURES_DIR.exists():
        for folder in CAPTURES_DIR.iterdir():
            if not folder.is_dir():
                continue
            dest = docs / "captures" / folder.name
            dest.mkdir(parents=True, exist_ok=True)
            for img in folder.iterdir():
                if img.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                    shutil.copy2(img, dest / img.name)

    static = ROOT / "web" / "static"
    shutil.copy2(static / "index.html", docs / "index.html")
    shutil.copy2(static / "admin.html", docs / "admin.html")
    shutil.copy2(static / "engine.js", docs / "engine.js")
    (docs / ".nojekyll").write_text("", encoding="utf-8")

    # index에 engine이 없으면 넣고, 관리자 링크 문구는 소스에 이미 반영됨
    for name in ("index.html", "admin.html"):
        path = docs / name
        html = path.read_text(encoding="utf-8")
        if 'src="./engine.js"' not in html and "engine.js" not in html:
            html = html.replace(
                "  <script>",
                '  <script src="./engine.js"></script>\n  <script>',
                1,
            )
            path.write_text(html, encoding="utf-8")

    size = sum(p.stat().st_size for p in docs.rglob("*") if p.is_file())
    print(f"docs/ 생성 완료: FAQ {len(rows)}건, {size / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
