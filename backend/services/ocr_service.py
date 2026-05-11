"""OCR 서비스: Upstage document-digitization + solar-pro3 JSON 구조화"""

# Phase 2에서 구현
# 흐름: POST /v1/document-digitization (model=ocr) → 텍스트 추출
#       → ChatUpstage(solar-pro3) + JsonOutputParser → 구조화 JSON
