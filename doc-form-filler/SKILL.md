---
name: doc-form-filler
description: |
  문서 양식(Word .docx, PDF, Excel .xlsx, 한글 .hwpx)을 저장·보관하고, 사용자가 정보를 입력하면 양식에 자동으로 채워 완성 문서를 생성한다.
  트리거: "양식 채워줘", "문서 작성해줘", "템플릿 저장해줘", "계약서/보고서/신청서 만들어줘", "이 양식에 내용 넣어줘", "반복 문서 자동으로 만들어줘", "기존 양식 업로드해서 쓸게"
  Use when filling document templates (hwpx, docx, pdf, xlsx) with user-provided data and delivering completed files.
---

# 문서 양식 저장 & 자동 채우기 스킬

## 핵심 안전 원칙
- **원본 양식 절대 수정 금지** — 복사본에 작업 후 새 파일명으로 저장
- 플레이스홀더가 XML에서 쪼개진 경우 LibreOffice 재저장 후 재시도
- 완성 파일이 해당 프로그램에서 오류 없이 열리는 것 확인 후 납품

## 전체 흐름

```
① 양식 확인/등록  →  ② 필드(빈칸) 파악  →  ③ 사용자에게 정보 수집  →  ④ 완성 문서 생성  →  ⑤ 출력
```

---

## 1. 양식 형식별 처리 방법

### 1-1. Word (.docx) 양식

**find-and-replace 방식** (플레이스홀더 치환) — 가장 간단하고 안정적
```python
import zipfile, shutil

def fill_docx(template_path, output_path, replacements: dict):
    """replacements = {"{{이름}}": "홍길동", "{{날짜}}": "2026-03-06"}"""
    shutil.copy(template_path, output_path)
    with zipfile.ZipFile(output_path, 'r') as z:
        names = z.namelist()
        contents = {n: z.read(n) for n in names}
    
    xml = contents['word/document.xml'].decode('utf-8')
    for placeholder, value in replacements.items():
        xml = xml.replace(placeholder, value)
    contents['word/document.xml'] = xml.encode('utf-8')
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in contents.items():
            z.writestr(name, data)
```

> ⚠️ Word는 플레이스홀더가 여러 `<w:r>` 태그로 쪼개질 수 있음 → python-docx의 run 순회 방식 사용

---

### 1-2. PDF 양식

**AcroForm 필드 확인**
```python
from pypdf import PdfReader
reader = PdfReader("양식.pdf")
fields = reader.get_fields()
for name, field in (fields or {}).items():
    print(f"필드명: {name} | 값: {field.get('/V','')}")
```

**폼 필드 채우기**
```python
from pypdf import PdfReader, PdfWriter
reader = PdfReader("양식.pdf")
writer = PdfWriter()
writer.append(reader)
writer.update_page_form_field_values(
    writer.pages[0],
    {"이름": "홍길동", "날짜": "2026-03-06"}
)
with open("완성.pdf", "wb") as f:
    writer.write(f)
```

> 폼 필드 없는 스캔 PDF → OCR 후 텍스트 오버레이 방식 사용

---

### 1-3. Excel (.xlsx) 양식

```python
import openpyxl, shutil

def fill_xlsx(template_path, output_path, cell_data: dict):
    """cell_data = {"B3": "홍길동", "D5": "2026-03-06"}"""
    shutil.copy(template_path, output_path)
    wb = openpyxl.load_workbook(output_path)
    ws = wb.active
    for cell, value in cell_data.items():
        ws[cell] = value
    wb.save(output_path)
```

**플레이스홀더 자동 탐지**
```python
def find_and_replace_xlsx(template_path, output_path, replacements):
    shutil.copy(template_path, output_path)
    wb = openpyxl.load_workbook(output_path)
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    for ph, val in replacements.items():
                        if ph in cell.value:
                            cell.value = cell.value.replace(ph, str(val))
    wb.save(output_path)
```

> ⚠️ 수식 셀 덮어쓰지 않도록 주의 — data_only=False 유지

---

### 1-4. 한글 (.hwpx) 양식

```python
import zipfile, shutil

def fill_hwpx(template_path, output_path, replacements: dict):
    shutil.copy(template_path, output_path)
    with zipfile.ZipFile(output_path, 'r') as z:
        names = z.namelist()
        contents = {n: z.read(n) for n in names}
    
    for name in names:
        if 'section' in name.lower() and name.endswith('.xml'):
            xml = contents[name].decode('utf-8')
            for placeholder, value in replacements.items():
                xml = xml.replace(placeholder, value)
            contents[name] = xml.encode('utf-8')
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in contents.items():
            z.writestr(name, data)

# 사용 예시
fill_hwpx('template.hwpx', 'output.hwpx', {
    "{{담당자}}": "홍길동",
    "{{날짜}}": "2026년 3월 6일",
    "{{사업명}}": "한강 수계 정비사업"
})
```

> ⚠️ hwpx도 텍스트가 여러 XML 요소로 분리될 수 있음. 복잡한 경우 LibreOffice 변환 후 docx 처리 권장

---

## 2. 플레이스홀더 명명 규칙

| 유형 | 형식 | 예시 |
|------|------|------|
| 일반 텍스트 | `{{필드명}}` | `{{이름}}`, `{{부서}}` |
| 날짜 | `{{날짜_YYYY-MM-DD}}` | `{{작성일_YYYY-MM-DD}}` |
| 금액 | `{{금액_원}}` | `{{계약금액_원}}` |
| 선택값 | `{{선택_옵션A|옵션B}}` | `{{등급_상|중|하}}` |

---

## 3. 정보 수집 → 문서 생성 워크플로우

### Step 1: 양식 분석
1. 파일 형식 확인
2. 플레이스홀더 또는 빈 필드 목록 추출
3. 필수/선택 항목 구분

### Step 2: 사용자에게 정보 수집
→ 한 번에 모아서 물어볼 것 (여러 번 왔다갔다 최소화)

### Step 3: 문서 생성 및 검증
1. 형식에 맞는 처리 방법 선택
2. 치환 실행
3. 완성 파일 열림 확인

### Step 4: 배치 생성 (여러 건)
```python
records = [
    {"{{이름}}": "홍길동", "{{날짜}}": "2026-03-06"},
    {"{{이름}}": "김철수", "{{날짜}}": "2026-03-07"},
]
for i, rec in enumerate(records):
    fill_docx('template.docx', f'output_{i+1}.docx', rec)
```

---

## 4. 자주 쓰는 문서 유형별 플레이스홀더 세트

### 공문 / 업무연락
`{{문서번호}}`, `{{수신}}`, `{{발신}}`, `{{제목}}`, `{{내용}}`, `{{작성일}}`, `{{담당자}}`, `{{연락처}}`

### 계약서
`{{계약번호}}`, `{{갑_기관명}}`, `{{을_업체명}}`, `{{사업명}}`, `{{계약금액}}`, `{{계약기간_시작}}`, `{{계약기간_종료}}`, `{{담당자}}`, `{{작성일}}`

### 설계 보고서 (수자원/토목)
`{{프로젝트명}}`, `{{발주처}}`, `{{설계사}}`, `{{담당자}}`, `{{검토일}}`, `{{설계기준}}`, `{{주요제원}}`, `{{특기사항}}`

### 견적서
`{{견적번호}}`, `{{고객사}}`, `{{품목}}`, `{{단가}}`, `{{수량}}`, `{{합계}}`, `{{유효기간}}`, `{{담당자}}`

---

## 5. 에러 대응

| 상황 | 원인 | 해결 |
|------|------|------|
| 플레이스홀더가 치환 안 됨 | XML이 쪼개짐 | LibreOffice 재저장 후 재시도 |
| hwpx 깨짐 | 인코딩 문제 | UTF-8 명시, 또는 docx 변환 |
| PDF 폼 필드 없음 | 스캔 PDF | OCR 후 오버레이 방식 사용 |
| Excel 수식 깨짐 | 값 덮어쓰기 | data_only=False 유지 |
