---
name: dxf-cross-section-table
description: |
  소하천 실시설계 횡단면도 DXF에서 각 측점의 지반고·계획하상고·현황제방고·홍수위·계획제방고를 추출해 개수후(실시설계) 엑셀 표를 자동 생성한다.
  트리거: "종단만들기", "횡단 엑셀 만들어줘", "DXF에서 표 뽑아줘", "횡단면도 엑셀", "개수후 실시설계 시트 채워줘", "수위현황표 만들어줘", "측점별 GH FH HWL 정리해줘"
  Use when given a 횡단면도 .dxf file and asked to fill a cross-section summary table (개수후 실시설계-1 style) with GH / FH / HWL / planned bank elevation per station.
paths: "**/*.dxf"
---

# DXF 횡단면도 → 개수후(실시설계) 엑셀 표 생성 스킬

## 핵심 원칙
- 원본 DXF·엑셀 절대 수정 금지 — 새 파일로 저장
- ezdxf로 레이어별 TEXT/MTEXT 전수 추출 후 분류
- 출력 파일: `바탕화면\{하천명}_개수후_실시설계.xlsx`

---

## DXF 레이어 구조 (대촌소하천 기준 — 파일마다 다를 수 있음)

| 레이어명 | 포함 정보 |
|---------|---------|
| `00-NO` | 측점명(NO.x+y), GH:xx.xx, FH:xx.xx (하상 계획고) |
| `00.홍수위` 또는 `홍수위` | HWL 수치 (EL.m) |
| `#계획-1` 또는 `계획` | 계획 제방고 FH:xx.xx (양안 각 1개) |
| `00.현황` 또는 `현황` | 현황 제방 실측 고도 (좌·우 각 1개) |

> **주의:** 레이어명은 프로젝트마다 다를 수 있다. 처음에는 전체 레이어 목록을 출력하고 위 패턴에 맞는 레이어를 특정할 것.

---

## 작업 흐름

### STEP 1 — 파일 확인
```
DXF 경로: 사용자 확인 (보통 바탕화면/실시설계 폴더)
참조 엑셀: 기존 개수후(실시설계) 시트가 있으면 열어서 컬럼 구조 파악
```

### STEP 2 — DXF 레이어 파악
```python
import ezdxf

doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

layers = [l.dxf.name for l in doc.layers]
print(layers)  # 어떤 레이어가 있는지 확인
```

### STEP 3 — 전체 텍스트 추출 (레이어별)
```python
texts_by_layer = {}
for e in msp:
    if e.dxftype() in ('TEXT', 'MTEXT'):
        layer = e.dxf.layer
        txt = e.dxf.text if e.dxftype()=='TEXT' else e.plain_mtext()
        x, y = e.dxf.insert.x, e.dxf.insert.y
        texts_by_layer.setdefault(layer, []).append((txt, x, y))
```

### STEP 4 — 측점 패널 구조 파악

DXF 횡단면도는 보통 **3열 × n행** 패널로 배치된다.
- **y 좌표**로 행(row) 구분: 값이 비슷한 y끼리 같은 행
- **x 좌표**로 열(column) 구분

패널 구조를 파악하면 각 텍스트가 어느 측점에 속하는지 알 수 있다.

```python
# 00-NO 레이어에서 측점명 추출
import re

station_pattern = re.compile(r'NO\.(\d+)(?:\+(\d+(?:\.\d+)?))?')
# NO.0+10.0 → station_m = 0*20 + 10.0 = 10.0
# NO.2 → station_m = 2*20 = 40.0
# 간격이 20m인 경우: NO번호 × 20 + 나머지

def parse_station(text):
    m = station_pattern.search(text)
    if m:
        major = int(m.group(1))
        minor = float(m.group(2)) if m.group(2) else 0.0
        return major * 20 + minor
    return None
```

### STEP 5 — 각 측점에 데이터 매핑

각 패널(x, y 범위)에서 아래 값을 수집한다:

| 항목 | 레이어 | 텍스트 패턴 | 비고 |
|------|--------|-----------|------|
| 지반고(GH) | `00-NO` | `GH:xx.xx` | 채널 바닥 기존 지반 |
| 계획하상고(FH) | `00-NO` | `FH:xx.xx` | 채널 바닥 계획고 |
| 홍수위(HWL) | `홍수위` | 숫자만 (xx.xx) | EL.m |
| 현황좌 | `현황` | 숫자, 패널 좌측 x | 좌안 현황 제방고 |
| 현황우 | `현황` | 숫자, 패널 우측 x | 우안 현황 제방고 |
| 계획FH좌 | `#계획-1` | `FH:xx.xx`, 패널 좌측 x | 좌안 계획 제방고 |
| 계획FH우 | `#계획-1` | `FH:xx.xx`, 패널 우측 x | 우안 계획 제방고 (없으면 빈칸) |

- **좌/우 구분**: 같은 패널 안에서 x가 작은 값 = 좌, 큰 값 = 우
- **계획FH가 없는 측점**: 기존 제방이 계획고를 만족 → 현황값 그대로 사용하거나 빈칸

### STEP 6 — 여유고 계산

```python
여유고좌 = round(계획FH좌 - HWL, 2)
여유고우 = round(계획FH우 - HWL, 2)  # 계획FH우가 있을 때만
```

### STEP 7 — 엑셀 작성

```python
import openpyxl
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()
ws = wb.active
ws.title = '개수후 (실시설계)-1'

thin = Side(style='thin')
bd = Border(left=thin, right=thin, top=thin, bottom=thin)
center = Alignment(horizontal='center', vertical='center')
hfill = PatternFill('solid', fgColor='D9E1F2')

# 1행 헤더
headers = ['구 분','측 점','지반고','계획하상고',
           '좌측제방','우측제방','홍수위',
           '계획제방','제방여유고','계획제방','여유고']
for c, h in enumerate(headers, 1):
    cell = ws.cell(1, c, h)
    cell.border = bd; cell.alignment = center
    cell.font = Font(bold=True); cell.fill = hfill

# 2행 서브헤더
sub = ['','측 점','(EL.m)','(EL.m)','현황(EL.m)','현황(EL.m)','(EL.m)',
       '좌(EL.m)','좌(m)','우(EL.m)','우(m)']
for c, s in enumerate(sub, 1):
    cell = ws.cell(2, c, s)
    cell.border = bd; cell.alignment = center
    cell.font = Font(bold=True); cell.fill = hfill

# 데이터 행 (row 3부터)
for i, row in enumerate(data_rows, 3):
    측점, gh, fh, 현좌, 현우, hwl, plan좌, 여좌, plan우, 여우 = row
    values = ['', 측점, gh, fh, 현좌, 현우, hwl, plan좌, 여좌, plan우, 여우]
    for c, v in enumerate(values, 1):
        cell = ws.cell(i, c, v if v is not None else '')
        cell.border = bd; cell.alignment = center
        if isinstance(v, float):
            cell.number_format = '0.00'

# 열 너비
for c, w in enumerate([6,8,8,9,9,9,8,9,8,9,8], 1):
    ws.column_dimensions[get_column_letter(c)].width = w

out = r'C:\Users\piri6\OneDrive\바탕 화면\{하천명}_개수후_실시설계.xlsx'
wb.save(out)
```

---

## 대촌소하천 작업 결과 (2026-04-01 기준)

DXF: `4. 실시설계/04.횡단면도-수정.dxf`
참조 엑셀: `4. 실시설계/대촌소하천.xls`
출력: `바탕화면/대촌소하천_개수후_실시설계.xlsx`

### 레이어 매핑
| 역할 | 레이어명 |
|------|---------|
| 측점·GH·FH | `00-NO` |
| 홍수위 | `00.홍수위_계획` (숫자 18개) |
| 계획 제방고 | `#계획-1` (FH:xx.xx) |
| 현황 제방고 | `00.현황` (숫자) |

### 측점 체계
- NO 간격 = **20m** (NO.1 = 20m, NO.2 = 40m …)
- 수정 DXF 기준 특이 측점: NO.2+4.1(44.1m), NO.2+6.6(46.6m), NO.2+9.1(49.1m), NO.8+10.7(170.7m)
  - 기존 엑셀(43.6 / 46.1 / 48.5 / 170.3)과 **다름** → DXF 수정본 값 우선 적용

### 최종 데이터

| 측점 | GH | FH하상 | 현황좌 | 현황우 | HWL | 계획FH좌 | 여유고좌 | 계획FH우 | 여유고우 |
|------|-----|--------|--------|--------|-----|---------|---------|---------|---------|
| 0.0 | 20.00 | 20.00 | 23.20 | 23.20 | 21.13 | 23.20 | 2.07 | 23.20 | 2.07 |
| 10.0 | 19.80 | 20.00 | 21.57 | 21.53 | 21.20 | 21.80 | 0.60 | 21.80 | 0.60 |
| 20.0 | 19.85 | 20.00 | 21.75 | 21.72 | 21.26 | 22.08 | 0.82 | 22.10 | 0.84 |
| 28.2 | 19.85 | 20.12 | 21.75 | 21.72 | 21.31 | 22.32 | 1.01 | 22.32 | 1.01 |
| 40.0 | 20.16 | 20.29 | 22.10 | 22.20 | 21.45 | 22.69 | 1.24 | 22.69 | 1.24 |
| 44.1 | 22.13 | 20.29 | 22.17 | 22.38 | 21.59 | 22.69 | 1.10 | 22.69 | 1.10 |
| 46.6 | 22.29 | 20.29 | 22.29 | 22.42 | 21.59 | 22.69 | 1.10 | 22.69 | 1.10 |
| 49.1 | 22.33 | 20.29 | 22.37 | 22.51 | 21.59 | 22.69 | 1.10 | 22.69 | 1.10 |
| 60.0 | 22.11 | 20.43 | 22.31 | 22.53 | 21.71 | 22.31 | 0.60 | — | — |
| 80.0 | 22.45 | 20.61 | 22.54 | 22.79 | 21.87 | 22.47 | 0.60 | — | — |
| 100.0 | 22.84 | 20.95 | 22.87 | 23.10 | 22.20 | 22.80 | 0.60 | — | — |
| 120.0 | 23.14 | 21.34 | 23.14 | 23.40 | 22.59 | 23.19 | 0.60 | — | — |
| 140.0 | 23.52 | 21.68 | 23.52 | 23.71 | 22.93 | 23.53 | 0.60 | — | — |
| 160.0 | 23.94 | 21.87 | 23.94 | 23.92 | 23.15 | 23.75 | 0.60 | — | — |
| 170.7 | 24.19 | 22.00 | 24.19 | 24.04 | 23.31 | 24.19 | 0.88 | — | — |

> 60m 이상: 우측 제방은 기존 제방이 계획고 만족 → 계획제방고(우) 없음

---

## 자주 발생하는 문제

| 문제 | 해결 |
|------|------|
| ezdxf 폰트 에러 출력 | `2>&1 \| grep -v "cannot open font"` 로 필터 |
| 레이어명 한글 깨짐 | repr()로 출력하면 내용 확인 가능 |
| NO.(좌)/(우) 중복 측점 | 동일 측점으로 통합, GH는 좌측 패널 값 사용 |
| 계획FH가 한쪽만 있음 | 우측 계획FH 없음 → 빈칸 처리 |
| 기존 엑셀 측점과 DXF 측점 불일치 | DXF 수정본 기준 우선 |
