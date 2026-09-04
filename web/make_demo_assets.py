# -*- coding: utf-8 -*-
"""시연용 양식 PDF · 경영정보 캡처 이미지를 만듭니다. 실제 서식·실제 화면이 아닙니다."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

WEB = Path(__file__).resolve().parent
ROOT = WEB.parent
EXCEL = ROOT / "TTA_구매챗봇_학습데이터_통합_0901.xlsx"
FORMS = WEB / "forms"
CAPTURES = WEB / "captures"
FONT = r"C:\Windows\Fonts\malgun.ttf"
FONTB = r"C:\Windows\Fonts\malgunbd.ttf"

STEPS = [
    ("01", "경영정보 로그인", "로그인 후 구매 관련 메뉴를 엽니다."),
    ("02", "해당 화면 작성", "안내에 해당하는 항목을 작성합니다."),
    ("03", "결재 상신", "결재선을 확인하고 상신합니다."),
]


def cell(v) -> str:
    if v is None or pd.isna(v):
        return ""
    t = str(v).strip()
    return "" if t == "nan" else t


def split_list(value: str) -> list[str]:
    if not value:
        return []
    return [p.strip() for p in value.replace("\n", ",").split(",") if p.strip()]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONTB if bold else FONT, size)


def load_rows() -> tuple[list[dict], list[str]]:
    df = pd.read_excel(EXCEL, sheet_name=0, header=2, dtype=str)
    rows = []
    forms: set[str] = set()
    for _, r in df.iterrows():
        qid = cell(r.iloc[0])
        q = cell(r.iloc[2])
        if not qid or qid.startswith("▶") or not q:
            continue
        names = split_list(cell(r.iloc[6]))
        forms.update(names)
        rows.append({"qid": qid, "cat": cell(r.iloc[1]), "q": q, "forms": names})
    return rows, sorted(forms)


def make_form_pdf(name: str) -> None:
    FORMS.mkdir(exist_ok=True)
    img = Image.new("RGB", (1240, 1754), "#f7f4ee")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 1240, 90), fill="#0b1c33")
    d.text((48, 28), "TTA 구매 안내  ·  시연용 양식", fill="#ffffff", font=font(28, True))
    d.rectangle((48, 140, 1192, 260), outline="#0b1c33", width=3)
    d.text((70, 165), name, fill="#0b1c33", font=font(36, True))
    d.text((70, 215), "실제 시행 서식이 아닙니다. 화면 연결 확인용입니다.", fill="#5a5044", font=font(20))
    y = 320
    labels = ["문서 제목", "작성 부서", "작성일", "관련 안내", "비고"]
    for label in labels:
        d.rectangle((48, y, 1192, y + 70), outline="#c9c0b4", width=1)
        d.rectangle((48, y, 280, y + 70), fill="#ece6dc")
        d.text((64, y + 20), label, fill="#3a3a3a", font=font(20))
        d.text((300, y + 20), "(시연) 기재란", fill="#9a9084", font=font(20))
        y += 70
    d.text((48, 1640), "이 파일은 데모용입니다. 실제 기안·계약에 사용하지 마세요.", fill="#8a2f2f", font=font(18))
    img.save(FORMS / f"{name}.pdf", "PDF", resolution=72.0)


def make_capture(qid: str, cat: str, question: str, step: str, title: str, desc: str) -> None:
    folder = CAPTURES / qid
    folder.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1280, 720), "#e8edf4")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 1280, 56), fill="#0b1c33")
    d.text((24, 16), "TTA 경영정보시스템", fill="#ffffff", font=font(22, True))
    d.text((980, 18), "시연 화면 · 실제 아님", fill="#e6c07b", font=font(16))
    d.rectangle((0, 56, 220, 720), fill="#143156")
    for i, m in enumerate(["홈", "전자결재", "구매요청", "검수", "계약", "대금지급"]):
        color = "#ffffff" if i == 2 else "#b7c4d6"
        d.text((28, 90 + i * 44), m, fill=color, font=font(18, i == 2))
    d.rectangle((236, 80, 1256, 700), fill="#ffffff")
    d.text((256, 100), f"{qid}  ·  {cat or '구매 안내'}", fill="#1d5fad", font=font(16, True))
    d.text((256, 132), f"화면 {step}  —  {title}", fill="#0b1c33", font=font(28, True))
    d.text((256, 178), desc, fill="#5b6776", font=font(18))
    qshow = question if len(question) < 42 else question[:40] + "…"
    d.text((256, 214), qshow, fill="#8a8a8a", font=font(16))
    box_y = 260
    for i, field in enumerate(["메뉴 경로", "작성 항목", "첨부", "결재선"]):
        d.rectangle((256, box_y, 1232, box_y + 70), outline="#d0d7e4", width=1)
        d.rectangle((256, box_y, 430, box_y + 70), fill="#f3f6fa")
        d.text((272, box_y + 22), field, fill="#3a4a5c", font=font(18))
        d.text((450, box_y + 22), "••••  (개인정보·문서번호 가림)", fill="#9aa7b5", font=font(18))
        box_y += 78
    d.rectangle((256, 640, 430, 684), fill="#1d5fad")
    d.text((292, 650), "다음", fill="#ffffff", font=font(18, True))
    img.save(folder / f"{step}_{title.replace(' ', '')}.png", "PNG", optimize=True)


def main() -> None:
    rows, forms = load_rows()
    print(f"양식 {len(forms)}개, 안내 {len(rows)}건")
    for name in forms:
        make_form_pdf(name)
        print("form", name)
    for i, row in enumerate(rows):
        for step, title, desc in STEPS:
            make_capture(row["qid"], row["cat"], row["q"], step, title, desc)
        if (i + 1) % 40 == 0:
            print(f"captures {i + 1}/{len(rows)}")
    print("완료")


if __name__ == "__main__":
    main()
