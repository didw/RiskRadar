# API Standards
# RiskRadar 공통 API 표준

## 1. RESTful API 규약

### 1.1 URL 구조
```
https://api.riskradar.io/v1/{resource}/{id}/{sub-resource}
```

### 1.2 HTTP 메서드
- **GET**: 리소스 조회
- **POST**: 리소스 생성
- **PUT**: 리소스 전체 업데이트
- **PATCH**: 리소스 부분 업데이트
- **DELETE**: 리소스 삭제

### 1.3 상태 코드
| Code | 의미 | 사용 예시 |
|------|------|-----------|
| 200 | OK | 성공적인 조회 |
| 201 | Created | 리소스 생성 완료 |
| 204 | No Content | 삭제 완료 |
| 400 | Bad Request | 잘못된 요청 |
| 401 | Unauthorized | 인증 필요 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 429 | Too Many Requests | Rate limit 초과 |
| 500 | Internal Server Error | 서버 오류 |

## 2. 요청/응답 포맷

### 2.1 요청 헤더
```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer {JWT_TOKEN}
X-Request-ID: {UUID}
X-Client-Version: 1.0.0
```

### 2.2 응답 포맷 (성공)
```json
{
  "success": true,
  "data": {
    // 실제 데이터
  },
  "meta": {
    "timestamp": "2024-07-19T10:00:00Z",
    "version": "1.0",
    "requestId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 2.3 응답 포맷 (에러)
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Company not found",
    "details": {
      "companyId": "invalid-id"
    }
  },
  "meta": {
    "timestamp": "2024-07-19T10:00:00Z",
    "requestId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 2.4 페이지네이션
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "perPage": 20,
    "total": 100,
    "totalPages": 5,
    "hasNext": true,
    "hasPrev": false
  }
}
```

## 3. GraphQL 표준

### 3.1 명명 규칙
- **Type**: PascalCase (예: `Company`, `RiskEvent`)
- **Field**: camelCase (예: `companyId`, `riskScore`)
- **Enum**: UPPER_SNAKE_CASE (예: `RISK_LEVEL_HIGH`)
- **Input**: `{Type}Input` (예: `CompanyInput`)

### 3.2 에러 처리
```json
{
  "errors": [
    {
      "message": "Company not found",
      "extensions": {
        "code": "RESOURCE_NOT_FOUND",
        "companyId": "invalid-id"
      },
      "path": ["company"],
      "locations": [{"line": 2, "column": 3}]
    }
  ],
  "data": null
}
```

## 4. 인증/인가

### 4.1 JWT 구조
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user-id",
    "email": "user@example.com",
    "role": "USER",
    "permissions": ["read:company", "write:watchlist"],
    "iat": 1626701234,
    "exp": 1626787634
  }
}
```

### 4.2 권한 레벨
| Role | 권한 |
|------|------|
| VIEWER | 읽기 전용 |
| USER | 읽기/쓰기 (자신의 데이터) |
| ADMIN | 모든 권한 |

## 5. Rate Limiting

### 5.1 제한 정책
| Endpoint | 제한 | 윈도우 |
|----------|------|--------|
| /api/v1/* | 100 | 1분 |
| /graphql | 100 | 1분 |
| /api/v1/auth/* | 10 | 1분 |

### 5.2 Rate Limit 헤더
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1626701234
```

## 6. 버전 관리

### 6.1 API 버전
- URL에 버전 포함: `/v1/`, `/v2/`
- 주요 버전만 관리 (Major version)
- 하위 호환성 유지

### 6.2 Deprecation 정책
1. 최소 6개월 전 공지
2. `Sunset` 헤더 추가
3. 문서에 명시

## 7. 보안

### 7.1 HTTPS 필수
모든 API 통신은 HTTPS로만 가능

### 7.2 CORS 설정
```
Access-Control-Allow-Origin: https://app.riskradar.io
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
```

### 7.3 입력 검증
- SQL Injection 방지
- XSS 방지
- 파일 업로드 제한

## 8. 로깅 및 모니터링

### 8.1 로그 포맷
```json
{
  "timestamp": "2024-07-19T10:00:00Z",
  "level": "INFO",
  "service": "api-gateway",
  "requestId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "user-123",
  "method": "GET",
  "path": "/api/v1/companies/123",
  "statusCode": 200,
  "duration": 45,
  "userAgent": "RiskRadar-Web/1.0"
}
```

### 8.2 메트릭
- Request rate
- Error rate
- Response time (P50, P95, P99)
- Active connections

## 9. 테스트

### 9.1 API 테스트 체크리스트
- [ ] 정상 케이스
- [ ] 에러 케이스
- [ ] 권한 테스트
- [ ] Rate limit 테스트
- [ ] 입력 검증 테스트

### 9.2 문서화
- OpenAPI 3.0 스펙
- GraphQL Schema
- Postman Collection