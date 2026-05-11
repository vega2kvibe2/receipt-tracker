# CLAUDE.md

이 파일은 Claude Code(claude.ai/code)가 이 저장소에서 작업할 때 참고하는 가이드입니다.

## 프로젝트 개요

**영수증 지출 관리 앱(Receipt Expense Tracker)** — 사용자가 영수증 이미지/PDF를 업로드하면 Upstage Vision LLM이 자동으로 지출 데이터를 추출하는 경량 웹 애플리케이션. DB 미사용; 데이터는 `backend/data/expenses.json`에 저장하며, Vercel의 에페머럴 파일시스템 문제에 대비해 `localStorage`를 클라이언트 측 보조 저장소로 병행 사용한다.

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| 프론트엔드 | React 18 + Vite 5 + TailwindCSS 3 + Axios + React Router |
| 백엔드 | Python FastAPI 0.115 + LangChain 1.2.18 + langchain-upstage 0.7.7 |
| OCR | Upstage `POST /v1/document-digitization` (model=`ocr`) → 텍스트 추출 |
| JSON 구조화 | `ChatUpstage(model="solar-pro3")` + `JsonOutputParser` (2단계 파이프라인) |
| 이미지 처리 | Pillow + pdf2image 1.17 (썸네일용; OCR은 PDF 직접 지원으로 Poppler 불필요) |
| 배포 | Vercel (프론트엔드 정적 빌드 + 백엔드 Python 서버리스, Mangum 래핑) |

## 실행 명령어

### 백엔드
```bash
# 가상환경 생성 및 패키지 설치
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r backend/requirements.txt

# 개발 서버 실행
uvicorn backend.main:app --reload
# Swagger UI: http://localhost:8000/docs
```

### 프론트엔드
```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # 프로덕션 빌드
```

### 환경변수
`.env.example` → `.env`로 복사 후 아래 값을 채운다:
- `UPSTAGE_API_KEY` — Upstage API 키
- `VITE_API_BASE_URL` — 백엔드 URL (로컬 기본값 `http://localhost:8000`; Vercel 배포 시 `""`로 설정하여 같은 도메인 상대 경로 사용)
- `DATA_FILE_PATH` — `VERCEL=1` 환경 감지 시 자동으로 `/tmp/expenses.json` 사용

## 디렉토리 구조 (목표)

```
receipt-tracker/
├── frontend/
│   └── src/
│       ├── pages/          # Dashboard.jsx, UploadPage.jsx, ExpenseDetail.jsx
│       ├── components/     # DropZone, ParsePreview, ExpenseCard, SummaryCard,
│       │                   # FilterBar, Badge, Modal, Toast, Header, ProgressBar
│       └── api/axios.js    # Axios 인스턴스 (VITE_API_BASE_URL 기반)
├── backend/
│   ├── main.py             # FastAPI 앱: CORS 설정, 라우터 등록
│   ├── routers/
│   │   ├── upload.py       # POST /api/upload
│   │   ├── expenses.py     # GET/DELETE/PUT /api/expenses
│   │   └── summary.py      # GET /api/summary
│   ├── services/
│   │   ├── ocr_service.py      # LangChain + ChatUpstage 체인
│   │   └── storage_service.py  # expenses.json 읽기/쓰기
│   ├── data/expenses.json
│   └── requirements.txt
└── vercel.json
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|----- |
| POST | `/api/upload` | `multipart/form-data` 파일 수신 → OCR 파싱 → JSON 반환 (저장은 별도) |
| GET | `/api/expenses` | 전체 지출 조회; `?from=YYYY-MM-DD&to=YYYY-MM-DD` 날짜 필터 |
| DELETE | `/api/expenses/{id}` | UUID로 항목 삭제; 없으면 404 |
| PUT | `/api/expenses/{id}` | UUID로 항목 부분 수정 |
| GET | `/api/summary` | 총합계 + 카테고리별 통계; `?month=YYYY-MM` 필터 |

## 데이터 스키마

```json
{
  "id": "uuid-v4",
  "created_at": "ISO-8601-UTC",
  "store_name": "string",
  "receipt_date": "YYYY-MM-DD",
  "receipt_time": "HH:MM | null",
  "category": "식료품|외식|교통|쇼핑|의료|기타",
  "items": [{ "name": "", "quantity": 1, "unit_price": 0, "total_price": 0 }],
  "subtotal": 0, "discount": 0, "tax": 0, "total_amount": 0,
  "payment_method": "string | null",
  "raw_image_path": "uploads/..."
}
```

## 아키텍처 핵심 사항

- **OCR 흐름 (2단계)**:
  1. `POST https://api.upstage.ai/v1/document-digitization` (multipart, `model=ocr`) → 텍스트 추출 (신뢰도 0.94+)
  2. `ChatUpstage(model="solar-pro3")` + `JsonOutputParser` → 구조화된 지출 JSON 반환
- **PDF 처리**: Upstage OCR API가 PDF를 직접 수신 가능 (최대 50MB, 100페이지). pdf2image + Poppler는 **썸네일 이미지 표시 목적으로만** 필요. Poppler 로컬 설치: `winget install oschwartz10612.Poppler`.
- **저장소**: `storage_service.py`가 `expenses.json` 모든 I/O를 담당. UUID는 업로드/파싱 시점이 아닌, 저장 시점에 서버에서 생성.
- **프론트엔드 상태**: OCR 파싱 결과는 `ParsePreview`에 표시하여 사용자가 수정 가능; "저장" 버튼 클릭 시에만 백엔드에 persist 요청을 보냄. 동시에 `localStorage`에도 저장.
- **오류 처리**: Toast 알림 (`fixed bottom-4 right-4`, 3초 자동 소멸). API 요청 진행 중에는 버튼 비활성화 (`opacity-50 cursor-not-allowed`).

## UI / 스타일

- **색상**: 주요 색상 `indigo-600`, 페이지 배경 `gray-50`, 카드 배경 `white`. 카테고리 뱃지는 `{color}-100` 배경 / `{color}-700` 텍스트.
- **폰트**: Pretendard → Noto Sans KR → system-sans (CDN은 `index.html`에 추가).
- **레이아웃**: `max-w-4xl mx-auto`, 스티키 헤더 `h-16`. ExpenseList 그리드: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`.
- **커스텀 애니메이션** (`tailwind.config.js`에 등록): `slide-up` (Toast), `scale-in` (Modal), `fade-in` (페이지 전환).

## Vercel 배포

`vercel.json`에서 `/api/*` 요청은 Python 서버리스(Mangum으로 감싼 FastAPI)로, 그 외 경로는 프론트엔드 정적 빌드로 라우팅. Vercel 환경변수로 `UPSTAGE_API_KEY` 등록 필수. `.env.production`의 `VITE_API_BASE_URL`은 `""`(빈값)으로 설정하여 같은 도메인 상대 경로를 사용.

## 주요 리스크

- **Vercel 파일시스템**: 서버리스 컨테이너는 에페머럴 — 콜드 스타트 시 `/tmp/expenses.json` 데이터 손실. MVP 대응: `localStorage` 병행 저장. 업그레이드 경로: Railway/Render 또는 Vercel KV.
- **Vercel에서 pdf2image**: Poppler 바이너리 필요 — Phase 2 구현 전 Vercel Python 런타임에서 사용 가능 여부 공식 문서로 확인할 것.
- **ChatPromptTemplate JSON 이스케이프**: system 프롬프트에 JSON 스키마 예시를 포함할 때 `{` → `{{`, `}` → `}}`로 이스케이프하지 않으면 `ValueError: Invalid format specifier` 발생.
- **`langchain-upstage` 버전**: 0.7.7 (Phase 0 테스트 완료). PRD 원안의 0.1.0과 API 다름 — `backend/requirements.txt` 버전을 기준으로 사용.

### Source Code가 변경되거나 라이브러리 버전이 변경되면 반드시 @PRD_영수증_지출관리앱.md 같이 업데이트 하고, 완료 기준의 Check Box에 완료된 사항들도 모두 체크표시 하세요.
