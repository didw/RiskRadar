# 개발자 체크리스트 - Sprint 1

## 🎯 담당 서비스별 즉시 시작 가이드

### Data Service 담당자
```bash
cd services/data-service
cat CLAUDE.md                    # 개발 가이드
cat Sprint1_Requirements.md      # Week 1: 조선일보 크롤러부터 시작
```
**첫 번째 작업**: BaseCrawler 클래스 구현
> ⚠️ **통합 환경 없음**: Mock Kafka 사용, 결과는 파일로 저장

### ML Service 담당자
```bash
cd services/ml-service
cat CLAUDE.md
cat Sprint1_Requirements.md      # Week 1: Kafka Consumer부터 시작
```
**첫 번째 작업**: Mock Consumer로 NER 모델 테스트
> ⚠️ **통합 환경 없음**: 샘플 데이터로 개발, Contract Testing 필수

### Graph Service 담당자
```bash
cd services/graph-service
cat CLAUDE.md
cat Sprint1_Requirements.md      # Week 1: Neo4j 스키마부터 시작
```
**첫 번째 작업**: 그래프 스키마 정의

### API Gateway 담당자
```bash
cd services/api-gateway
cat CLAUDE.md
cat Sprint1_Requirements.md      # Week 1: GraphQL 설정부터 시작
```
**첫 번째 작업**: Apollo Server 설정

### Web UI 담당자
```bash
cd services/web-ui
cat CLAUDE.md
cat Sprint1_Requirements.md      # Week 1: 대시보드 레이아웃부터 시작
```
**첫 번째 작업**: Next.js 라우팅 설정

## ⏰ 일일 스케줄

| 시간 | 활동 | 환경 |
|------|------|------|
| 09:00-13:50 | 개별 모듈 개발 & 단위 테스트 | 최소 환경 (`minimal-start.sh`) |
| 13:50 | 통합 준비 (코드 정리) | - |
| 14:00-15:00 | **팀 전체: 통합 테스트 & 디버깅** | 전체 환경 (`quick-start.sh`) |
| 15:00-18:00 | 통합 이슈 수정 & 개발 계속 | 최소 환경 |

## 🚨 주의사항

1. **매일 14:00 통합 필수** - 놓치면 충돌 지옥
2. **테스트 없이 커밋 금지** - CI/CD가 실패하면 모두가 고통
3. **담당 서비스만 수정** - 다른 서비스는 PR로 요청
4. **문서 업데이트** - 코드 변경 시 관련 문서도 수정

## 📞 긴급 연락

- **통합 실패 시**: 즉시 develop 브랜치 확인
- **서비스 간 충돌**: Integration Points 문서 참조
- **성능 문제**: 2GB RAM Workflow 적용

---
**Remember**: 우리는 매일 14:00에 만납니다! 🤝