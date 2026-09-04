# ProductChat — TTA 구매 안내 챗봇

직원이 구매·발주·계약·검수·대금 절차를 물으면, **검증된 엑셀 FAQ**에서만 답을 찾아 보여 주는 웹 챗봇입니다.  
저장소: [Mukjin/ProductChat](https://github.com/Mukjin/ProductChat)

## 무엇을 하나요

| 화면 | 주소 | 역할 |
|------|------|------|
| 직원 | `/` | 질문, 양식 내려받기, 경영정보 화면 안내, 파일 첨부 |
| 관리자 | `/admin` | 문의 기록 조회·필터, 답·양식·캡처 편집 |

### 답변 원칙

1. **검색** — 로컬 임베딩(Ollama) 또는 글자 겹침으로 FAQ를 고릅니다.
2. **검증 답** — 엑셀에 적힌 절차만 사용합니다. 개별 금액·적격은 추측하지 않습니다.
3. **문장 다듬기** — Gemini가 같은 검증 답을 읽기 쉽게 정리한 뒤, 타이핑 효과로 보여 줍니다.
4. **양식·화면** — 연결된 양식만 버튼을 띄우고, 경영정보 캡처는 단계별 토글로 엽니다.

### 최근 구현 요약

- Gemini 연동 (라우팅·다듬기, 한도 시 모델 폴백)
- 채팅 검색·선택 삭제, 파일/이미지 첨부
- 답변 속도 개선 (임베딩 예열, 글자 검색 폴백, 다듬기 캐시)
- 절차 안내 타이핑 연출, 양식 없는 칸 숨김
- 관리자 문의 기록: 목록 + 상세, 검색·상태 필터, 안내 편집 바로가기

## 로컬 실행

### 준비

- Python 3.10+
- (권장) [Ollama](https://ollama.com) + `qwen3-embedding:0.6b` — 의미 검색용  
  없어도 글자 검색으로 동작합니다.
- Gemini API 키 — 답 문장 다듬기용

```bash
pip install -r requirements.txt
cp web/.env.example web/.env
# web/.env 에 GEMINI_API_KEY=... 입력
```

색인 파일이 없으면 한 번 만듭니다.

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

## 배포 (Render)

이 저장소에 `render.yaml` Blueprint가 있습니다.

1. [Render](https://dashboard.render.com) → **New** → **Blueprint**
2. GitHub 저장소 `Mukjin/ProductChat` 연결
3. Environment에 `GEMINI_API_KEY` 입력 (필수)
4. Deploy

또는 대시보드에서 Web Service를 직접 만들고:

| 항목 | 값 |
|------|-----|
| Runtime | Python |
| Build | `pip install -r requirements.txt` |
| Start | `python -u web/server.py` |
| Health Check | `/api/health` |

Render는 `PORT`를 자동으로 넣습니다. 서버는 `HOST=0.0.0.0`으로 수신합니다.

> 무료 플랜은 잠시 쉬면 잠들었다가 첫 요청에 깨어납니다.  
> 클라우드에는 Ollama가 없으므로 **글자 검색 + Gemini 다듬기**로 동작합니다. 의미 검색까지 쓰려면 Ollama가 있는 환경에 올리면 됩니다.

## 주요 파일

```
web/server.py              # HTTP API · 검색 · Gemini
web/static/index.html      # 직원 화면
web/static/admin.html      # 관리자 화면
web/forms/                 # 내려받기 양식
web/captures/              # 경영정보 화면 캡처
TTA_구매챗봇_학습데이터_통합_0901.xlsx
테스트_embedding_index.json
requirements.txt
render.yaml
```

## API (요약)

- `GET /api/health` — 상태
- `POST /api/ask` — 질문 (`query`, `user`, `history`, `files`)
- `POST /api/guide` — 안내 번호로 열기
- `POST /api/upload` — 직원 첨부 업로드
- `GET /api/admin/logs` — 문의 기록
- `GET/POST /api/admin/*` — 카탈로그·저장·양식/캡처 업로드

## 보안

- `web/.env` 와 `.env`는 Git에 올리지 않습니다.
- 직원 첨부는 `web/uploads/`에 저장되며 커밋하지 않습니다.
- 답은 엑셀·오버레이에 검증된 내용만 사용합니다.
