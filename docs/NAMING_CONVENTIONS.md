# RiskRadar 문서 명명 규칙
# Document Naming Conventions

## 📝 일반 원칙

### 1. 파일명 규칙
- **언어**: 영어 사용 (일관성 및 접근성)
- **구분자**: 언더스코어(`_`) 사용
- **대소문자**: Title_Case_Format
- **확장자**: `.md` (Markdown)

### 2. 디렉토리 구조
```
docs/
├── prd/          # Product Requirements Documents
├── strategy/     # Strategic & Business Documents  
├── research/     # Technical Research & Studies
└── analysis/     # Market & Competitor Analysis
```

## 🏷️ 문서 유형별 명명 규칙

### PRD 문서 (Product Requirements)
- **메인 PRD**: `PRD.md`
- **하위 문서**: `PRD_{Category}.md`
- 예시:
  - `PRD_Tech_Architecture.md`
  - `PRD_Development_Plan.md`
  - `PRD_RKG_Design.md`

### 전략 문서 (Strategy)
- **패턴**: `{Topic}_{Type}.md`
- 예시:
  - `Risk_Management_Overview.md`
  - `Target_Customer_Definition.md`
  - `Passive_to_Active_RM_Strategy.md`

### 연구 문서 (Research)
- **패턴**: `{Subject}_Specification.md` 또는 `{Subject}_Study.md`
- 예시:
  - `RKG_Technical_Specification.md`
  - `Media_Source_Tiering.md`

### 분석 문서 (Analysis)
- **패턴**: `{Company}_Analysis.md`
- 예시:
  - `Gemini_Analysis.md`
  - `ChatGPT_Analysis.md`

## 🔄 변경 이력

### 2024-07-19 문서명 변경
| 이전 이름 | 새 이름 | 이유 |
|-----------|---------|------|
| 1차 고객, 200대 고객 CEO 정의.md | Target_Customer_Definition.md | 영문 통일 |
| New pitch-deck Draft.md | Pitch_Deck_Draft.md | 일관된 형식 |
| Passive → Active RM 전략.md | Passive_to_Active_RM_Strategy.md | 특수문자 제거 |
| RKG 기반 제품 로드맵.md | RKG_Product_Roadmap.md | 간결성 |
| Risk Management 로드맵.md | Risk_Management_Roadmap.md | 일관성 |
| Risk Knowledge Graph (RKG).md | RKG_Technical_Specification.md | 명확성 |
| 언론사 티어링.md | Media_Source_Tiering.md | 영문 통일 |

## ✅ 권장사항

### DO
- ✅ 명확하고 설명적인 이름 사용
- ✅ 일관된 명명 패턴 유지
- ✅ 버전 관리는 Git으로 (파일명에 버전 번호 X)
- ✅ 약어는 널리 알려진 것만 사용 (RKG, RM, API 등)

### DON'T
- ❌ 특수문자 사용 (→, &, @ 등)
- ❌ 공백 사용 (언더스코어로 대체)
- ❌ 날짜를 파일명에 포함
- ❌ 너무 긴 파일명 (50자 이내 권장)

## 🔍 빠른 참조

### 새 문서 생성 시
1. 해당 카테고리 확인 (prd, strategy, research, analysis)
2. 명명 패턴 적용
3. 영어로 작성 (필요시 한글 부제 추가 가능)
4. README.md에 링크 추가