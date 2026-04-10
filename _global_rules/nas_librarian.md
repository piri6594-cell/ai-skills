# NAS 사서 에이전트 연동 규칙

## API 엔드포인트
- 기본 URL: `http://192.168.55.226:8200`
- 상태: `/status`
- 검색: `POST /search` — `{"query":"검색어", "top_k":5}`
- 질의응답: `POST /ask` — `{"query":"질문"}`
- 분류: `POST /classify` — `{"text":"문서내용"}`
- 요약: `POST /summarize` — `{"text":"문서내용"}`
- 업로드: `POST /upload` — multipart file
- 카탈로그: `GET /catalog`
- NAS 인덱싱: `POST /index-nas`

## 자동 참조 규칙
- 수량산출, 설계, 보고서 작업 시 → NAS 사서에 관련 문서 검색 먼저 수행
- 검색 결과가 있으면 참고자료로 활용, 출처 명시
- 결과물 완성 후 → NAS에 업로드하여 지식 축적

## 파이프라인 연동
```
① Opus(계획) — NAS 검색으로 참고자료 확보
② Sonnet(생성) — 참고자료 기반 결과물 생성
③ Codex+Gemini(검증) — NAS 기존 자료와 교차검증
④ Sonnet(보완) — 검증 피드백 반영
⑤ Opus(최종) — 최종 검증 + NAS 저장
⑥ 제출
```

## 사용 예시
```bash
# 관련 문서 검색
curl -s -X POST http://192.168.55.226:8200/search -H "Content-Type: application/json" -d '{"query":"소하천 설계홍수량"}'

# RAG 질의
curl -s -X POST http://192.168.55.226:8200/ask -H "Content-Type: application/json" -d '{"query":"용산천 계획하폭은?"}'

# 결과물 업로드
curl -s -X POST http://192.168.55.226:8200/upload -F "file=@결과물.xlsx"
```
