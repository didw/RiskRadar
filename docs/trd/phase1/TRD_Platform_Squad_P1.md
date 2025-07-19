# Technical Requirements Document
# Platform Squad - Phase 1

## 1. 개요

### 1.1 문서 정보
- **Squad**: Platform Squad
- **Phase**: 1 (Week 1-4)
- **작성일**: 2024-07-19
- **버전**: 1.0

### 1.2 범위
Kubernetes 인프라 구축, CI/CD 파이프라인 설정, 기본 모니터링 시스템 구현

### 1.3 관련 문서
- PRD: [PRD_Tech_Architecture.md](../../prd/PRD_Tech_Architecture.md)
- Development Plan: [PRD_Development_Plan.md](../../prd/PRD_Development_Plan.md)
- 의존 TRD: 모든 Squad (인프라 제공)

## 2. 기술 요구사항

### 2.1 기능 요구사항
| ID | 기능명 | 설명 | 우선순위 | PRD 참조 |
|----|--------|------|----------|----------|
| F001 | K8s 클러스터 구축 | EKS 기반 프로덕션 환경 | P0 | NFR |
| F002 | CI/CD 파이프라인 | GitLab CI + ArgoCD | P0 | NFR |
| F003 | 서비스 메시 | Istio 설정 및 구성 | P0 | NFR |
| F004 | 모니터링 스택 | Prometheus + Grafana | P0 | NFR |
| F005 | 시크릿 관리 | Vault 통합 | P1 | NFR |

### 2.2 비기능 요구사항
| 항목 | 요구사항 | 측정 방법 |
|------|----------|-----------|
| 가용성 | 99.9% uptime | 모니터링 대시보드 |
| 확장성 | Auto-scaling 30초 내 | 부하 테스트 |
| 보안 | Zero-trust 네트워크 | 보안 감사 |
| 복구 | RTO < 30분 | 장애 시뮬레이션 |

## 3. 시스템 아키텍처

### 3.1 전체 인프라 구조
```
┌─────────────────────────────────────────────────────────┐
│                    AWS Account                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │                  VPC (10.0.0.0/16)              │   │
│  ├─────────────────────────────────────────────────┤   │
│  │                                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │Public Subnet │  │Public Subnet │           │   │
│  │  │  10.0.1.0/24 │  │  10.0.2.0/24 │           │   │
│  │  │  ┌────────┐  │  │  ┌────────┐  │           │   │
│  │  │  │  ALB   │  │  │  │  NAT   │  │           │   │
│  │  │  └────┬───┘  │  │  └────┬───┘  │           │   │
│  │  └───────┼──────┘  └───────┼──────┘           │   │
│  │          │                  │                   │   │
│  │  ┌───────▼──────────────────▼───────┐          │   │
│  │  │      Private Subnets             │          │   │
│  │  │  10.0.10.0/24, 10.0.11.0/24     │          │   │
│  │  │                                  │          │   │
│  │  │  ┌────────────────────────────┐ │          │   │
│  │  │  │    EKS Control Plane       │ │          │   │
│  │  │  └────────────┬───────────────┘ │          │   │
│  │  │               │                 │          │   │
│  │  │  ┌────────────▼────────────────┐│          │   │
│  │  │  │     EKS Node Groups         ││          │   │
│  │  │  │  ┌─────┐ ┌─────┐ ┌─────┐  ││          │   │
│  │  │  │  │Node1│ │Node2│ │Node3│  ││          │   │
│  │  │  │  └─────┘ └─────┘ └─────┘  ││          │   │
│  │  │  └─────────────────────────────┘│          │   │
│  │  └──────────────────────────────────┘          │   │
│  │                                                 │   │
│  │  ┌─────────────────────────────────────────┐   │   │
│  │  │        Data Tier Subnets                │   │   │
│  │  │        10.0.20.0/24, 10.0.21.0/24      │   │   │
│  │  │  ┌─────────┐  ┌──────────┐  ┌────────┐│   │   │
│  │  │  │  RDS    │  │  Neo4j   │  │ Redis  ││   │   │
│  │  │  └─────────┘  └──────────┘  └────────┘│   │   │
│  │  └─────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Kubernetes 아키텍처
```yaml
namespaces:
  - riskradar-prod
  - riskradar-staging
  - riskradar-dev
  - monitoring
  - istio-system

node_groups:
  - name: general
    instance_type: t3.large
    min_size: 3
    max_size: 10
    labels:
      workload: general
      
  - name: compute
    instance_type: c5.2xlarge
    min_size: 2
    max_size: 8
    labels:
      workload: compute
      
  - name: gpu
    instance_type: g4dn.xlarge
    min_size: 0
    max_size: 4
    labels:
      workload: ml
    taints:
      - key: nvidia.com/gpu
        value: "true"
        effect: NoSchedule
```

## 4. 상세 설계

### 4.1 CI/CD 파이프라인

#### 4.1.1 GitLab CI 구성
```yaml
stages:
  - test
  - build
  - security
  - deploy

variables:
  DOCKER_REGISTRY: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
  KUBERNETES_NAMESPACE: riskradar-${CI_ENVIRONMENT_NAME}

test:
  stage: test
  script:
    - make test
    - make lint
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

build:
  stage: build
  script:
    - docker build -t $DOCKER_REGISTRY/$CI_PROJECT_NAME:$CI_COMMIT_SHA .
    - docker push $DOCKER_REGISTRY/$CI_PROJECT_NAME:$CI_COMMIT_SHA
  only:
    - main
    - develop

security_scan:
  stage: security
  script:
    - trivy image $DOCKER_REGISTRY/$CI_PROJECT_NAME:$CI_COMMIT_SHA
  allow_failure: false

deploy:
  stage: deploy
  script:
    - |
      argocd app create $CI_PROJECT_NAME \
        --repo $CI_PROJECT_URL \
        --path kubernetes/overlays/$CI_ENVIRONMENT_NAME \
        --dest-server https://kubernetes.default.svc \
        --dest-namespace $KUBERNETES_NAMESPACE \
        --sync-policy automated
```

#### 4.1.2 ArgoCD Application 정의
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: riskradar-backend
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://gitlab.com/riskradar/backend
    targetRevision: main
    path: kubernetes/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: riskradar-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
  revisionHistoryLimit: 10
```

### 4.2 Service Mesh (Istio)

#### 4.2.1 Istio 구성
```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: control-plane
spec:
  profile: production
  values:
    pilot:
      autoscaleMin: 2
      autoscaleMax: 5
      resources:
        requests:
          cpu: 500m
          memory: 2048Mi
    global:
      proxy:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
  components:
    egressGateways:
    - name: istio-egressgateway
      enabled: true
    ingressGateways:
    - name: istio-ingressgateway
      enabled: true
      k8s:
        service:
          type: LoadBalancer
```

#### 4.2.2 트래픽 관리
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: riskradar-api
spec:
  hosts:
  - api.riskradar.io
  gateways:
  - istio-ingressgateway
  http:
  - match:
    - uri:
        prefix: /api/v1
    route:
    - destination:
        host: api-service
        port:
          number: 8080
      weight: 90
    - destination:
        host: api-service-canary
        port:
          number: 8080
      weight: 10
    timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
```

### 4.3 모니터링 스택

#### 4.3.1 Prometheus 구성
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
    
    - job_name: 'istio-mesh'
      kubernetes_sd_configs:
      - role: endpoints
        namespaces:
          names:
          - istio-system
    
    - job_name: 'neo4j'
      static_configs:
      - targets: ['neo4j-metrics:2004']
    
    rule_files:
    - '/etc/prometheus/rules/*.yml'
```

#### 4.3.2 Grafana 대시보드
```json
{
  "dashboard": {
    "title": "RiskRadar Platform Overview",
    "panels": [
      {
        "title": "API Request Rate",
        "targets": [{
          "expr": "sum(rate(http_requests_total[5m])) by (service)"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))"
        }]
      },
      {
        "title": "Pod CPU Usage",
        "targets": [{
          "expr": "sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)"
        }]
      },
      {
        "title": "Neo4j Query Performance",
        "targets": [{
          "expr": "histogram_quantile(0.95, neo4j_bolt_query_duration_seconds_bucket)"
        }]
      }
    ]
  }
}
```

### 4.4 보안 구성

#### 4.4.1 Vault 통합
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vault-auth
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/VaultAuth

---
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultAuth
metadata:
  name: riskradar-auth
spec:
  method: kubernetes
  mount: kubernetes
  kubernetes:
    role: riskradar
    serviceAccount: vault-auth

---
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultStaticSecret
metadata:
  name: database-creds
spec:
  type: kv-v2
  mount: secret
  path: riskradar/database
  destination:
    name: database-creds
    create: true
  refreshAfter: 1h
```

#### 4.4.2 네트워크 정책
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-service-policy
spec:
  podSelector:
    matchLabels:
      app: api-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: istio-system
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: neo4j
    ports:
    - protocol: TCP
      port: 7687
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
```

## 5. 기술 스택

### 5.1 사용 기술
- **Container Platform**: Kubernetes 1.28 (EKS)
- **Service Mesh**: Istio 1.19
- **CI/CD**: GitLab CI + ArgoCD
- **Monitoring**: 
  - Prometheus 2.47
  - Grafana 10.2
  - Jaeger 1.50
- **Logging**: ELK Stack
- **Secret Management**: HashiCorp Vault
- **Infrastructure as Code**: Terraform

### 5.2 인프라 요구사항
- **Control Plane**: EKS Managed
- **Worker Nodes**:
  - General: 3 × t3.large (최소)
  - Compute: 2 × c5.2xlarge
  - GPU: 2 × g4dn.xlarge (ML 워크로드)
- **네트워킹**:
  - VPC: 10.0.0.0/16
  - Multi-AZ 구성
  - NAT Gateway

## 6. 구현 계획

### 6.1 마일스톤
| 주차 | 목표 | 산출물 |
|------|------|--------|
| Week 1 | 인프라 프로비저닝 | EKS 클러스터, VPC |
| Week 2 | 핵심 서비스 배포 | Istio, Prometheus |
| Week 3 | CI/CD 구축 | GitLab CI, ArgoCD |
| Week 4 | 보안 및 최적화 | Vault, 모니터링 |

### 6.2 리스크 및 대응
| 리스크 | 영향도 | 대응 방안 |
|--------|--------|-----------|
| EKS 업그레이드 | Medium | 블루/그린 클러스터 전략 |
| 비용 초과 | Medium | 자동 스케일링 정책, 예산 알림 |
| 보안 취약점 | High | 정기 스캔, 자동 패치 |

## 7. 테스트 계획

### 7.1 인프라 테스트
- **Chaos Engineering**: Litmus 사용
- **부하 테스트**: K6로 1000 TPS 시뮬레이션
- **장애 복구**: 노드 장애 시나리오

### 7.2 보안 테스트
- **취약점 스캔**: Trivy, Snyk
- **침투 테스트**: 분기별 실시
- **컴플라이언스**: CIS Benchmark

## 8. 완료 기준

### 8.1 기능 완료
- [x] EKS 클러스터 3-node 구성
- [x] Istio 서비스 메시 구축
- [x] CI/CD 파이프라인 동작
- [x] 모니터링 대시보드 구성

### 8.2 성능 완료
- [x] Auto-scaling 30초 내 반응
- [x] 시스템 가용성 99.9%
- [x] 배포 시간 10분 이내

## 9. 의존성

### 9.1 외부 의존성
- AWS 계정 및 권한
- GitLab 저장소
- Docker Registry (ECR)

### 9.2 내부 의존성
- 모든 Squad의 애플리케이션 컨테이너화

## 10. 부록

### 10.1 Terraform 예제
```hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.15.3"

  cluster_name    = "riskradar-eks"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 3
      max_size     = 10

      instance_types = ["t3.large"]
      
      k8s_labels = {
        Environment = "production"
        Workload    = "general"
      }
    }
  }
}
```

### 10.2 참고 자료
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Istio Production Guide](https://istio.io/latest/docs/ops/deployment/)