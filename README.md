# ProductChat — TTA 구매 안내 챗봇

직원이 구매·발주·계약·검수·대금 절차를 물으면, **검증된 엑셀 FAQ**에서만 답을 찾아 보여 주는 웹 챗봇입니다.  
저장소: [Mukjin/ProductChat](https://github.com/Mukjin/ProductChat)

**GitHub Pages:** https://mukjin.github.io/ProductChat/

## 무엇을 하나요

| 화면 | 주소 | 역할 |
|------|------|------|
| 직원 (Pages) | `/` · Guest | 질문, 양식 내려받기, 경영정보 화면 안내 |
| 관리자 (Pages) | `/admin.html` · 관리자 | 안내·양식·캡처 **보기** (저장·문의기록은 로컬) |
| 직원 (로컬 서버) | `/` | 위와 동일 + 파일 첨부 서버 저장, Gemini 문장 다듬기 |
| 관리자 (로컬) | `/admin` | 문의 기록·답·양식·캡처 **편집** |

화면 왼쪽(Guest) 또는 상단(관리자)의 **Guest / 관리자** 버튼으로 전환합니다.

### 답변 원칙

1. **검색** — Pages는 글자 겹침 검색, 로컬은 Ollama 임베딩(있으면) 또는 글자 검색
2. **검증 답** — 엑셀에 적힌 절차만 사용. 개별 금액·적격은 추측하지 않음
3. **문장 다듬기** — 로컬/백엔드에서만 Gemini가 답을 읽기 쉽게 정리 (Pages는 엑셀 원문)
4. **양식·화면** — 연결된 양식 버튼, 경영정보 캡처는 단계별 토글

## GitHub Pages 배포

정적 사이트는 `docs/` 폴더입니다. FAQ·양식·캡처가 포함되어 브라우저에서만 동작합니다.

1. 이 저장소 **Settings → Pages**
2. Source: **GitHub Actions** (워크플로 `.github/workflows/pages.yml`)
3. `main` 푸시 후 https://mukjin.github.io/ProductChat/ 확인

지식을 바꾼 뒤에는 다시 빌드해 `docs/`를 갱신하세요.

```bash
pip install -r requirements.txt
python scripts/build_pages.py
```

> Pages에는 Python 서버·Ollama·관리자 API가 없습니다.  
> 첨부는 미리보기만 되고, 답 문장 다듬기(Gemini)는 로컬 서버에서만 됩니다.

## 로컬 실행 (전체 기능)

### 준비

- Python 3.10+
- (권장) [Ollama](https://ollama.com) + `qwen3-embedding:0.6b`
- Gemini API 키 — 답 문장 다듬기용

```bash
pip install -r requirements.txt
cp web/.env.example web/.env
# web/.env 에 GEMINI_API_KEY=... 입력
```

색인이 없으면 한 번 만듭니다.

```bash
ollama pull qwen3-embedding:0.6b
python 테스트_embedding.py
```

### 서버

```bash
python -u web/server.py
```

- 직원: http://127.0.0.1:8765  
- 관리: http://127.0.0.1:8765/admin  

## 주요 파일

```
web/server.py              # HTTP API · 검색 · Gemini (로컬)
web/static/index.html      # 직원 화면
web/static/engine.js       # Pages용 글자 검색 엔진
web/static/admin.html      # 관리자 화면 (로컬)
web/forms/ · web/captures/
docs/                      # GitHub Pages 산출물
scripts/build_pages.py     # docs/ 빌드
TTA_구매챗봇_학습데이터_통합_0901.xlsx
테스트_embedding_index.json
```

## API (로컬 서버)

- `GET /api/health` — 상태
- `POST /api/ask` — 질문
- `POST /api/guide` — 안내 번호로 열기
- `POST /api/upload` — 직원 첨부 업로드
- `GET /api/admin/logs` — 문의 기록

## 보안

- `web/.env` 와 `.env`는 Git에 올리지 않습니다.
- 직원 첨부는 `web/uploads/`에 저장되며 커밋하지 않습니다.
- 답은 엑셀·오버레이에 검증된 내용만 사용합니다.
