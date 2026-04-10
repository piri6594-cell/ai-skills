---
skill: _global
type: rule
topic: excel-safety
created: 2026-04-08
---

# Excel 안전 작업 규칙

## 기본 원칙
- 원본 파일 절대 수정 금지 — 복사본 생성 후 작업
- win32com 우선 사용 (한글 Excel, xlrd는 인코딩 오류)
- 결과 파일 자동 열기 금지 — 경로만 안내

## 도구 선택
| 상황 | 도구 |
|------|------|
| 한글 xls, Excel 재계산 필요 | win32com |
| xlsx 구조 편집, 서식 | openpyxl |
| 데이터 분석, 집계 | pandas |

## 서식 기준
- 폰트: 맑은 고딕, 본문 10pt, 제목 12~14pt
- 헤더: 회색 Bold (D9D9D9)
- 소수점 2자리 / 천단위 콤마
- 불일치: FF4444 / 확인 필요: FFFF00 / 정상: CCFFCC
