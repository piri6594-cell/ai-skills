---
skill: _global
type: rule
topic: agent-collaboration
created: 2026-04-08
---

# 에이전트 협업 규칙

## 역할 정의
- **Claude (사수)**: 사용자와 대화, 작업 분해, Codex 위임, 결과 검수, 최종 저장
- **Codex (조수)**: 구현 전담, 파일 생성, 데이터 처리

## 협업 디렉토리
```
C:/Users/piri6/agent-collab/
├── inbox/   ← Claude가 작성하는 지시문 (YYYYMMDD_작업명.md)
├── outbox/  ← Codex가 결과물 저장 + DONE.txt / FAIL.txt
├── review/  ← Claude의 검토 결과
└── logs/    ← codex exec 실행 로그
```

## 작업 흐름
1. Claude가 `inbox/YYYYMMDD_작업명.md` 작성
2. `codex exec --skip-git-repo-check "$(cat inbox/작업명.md)"` 실행
3. `outbox/작업명/DONE.txt` 존재 확인 → 결과 검토
4. 검토 통과 → 바탕화면 프로젝트 폴더로 복사
5. 실패 시 최대 2회 재시도, 이후 Claude가 직접 처리

## 발견된 패턴

### 2026-04-08: stdin 파이핑
- `$prompt | codex exec - ` 방식으로 긴 지시문 전달 가능
- 결과를 파일로 저장할 때 한글 경로는 Codex가 쓰지 못함 → PowerShell이 받아서 저장
- codex exec 실행 시 반드시 `--skip-git-repo-check` 옵션 필요 (git repo 외부 경로)

### 2026-04-08: 샌드박스
- Codex 기본 sandbox는 read-only지만 PowerShell exec으로 파일 생성 가능
- 민감한 경로 접근 필요 시 `sandbox_permissions` 옵션 추가
