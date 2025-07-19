"""GraphQL 스키마 정의"""
import strawberry
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum

# Enums
@strawberry.enum
class NodeType(Enum):
    COMPANY = "COMPANY"
    PERSON = "PERSON"
    EVENT = "EVENT"
    RISK = "RISK"
    NEWS_ARTICLE = "NEWS_ARTICLE"

@strawberry.enum
class RiskType(Enum):
    FINANCIAL = "FINANCIAL"
    LEGAL = "LEGAL"
    REPUTATION = "REPUTATION"
    OPERATIONAL = "OPERATIONAL"
    ESG = "ESG"

@strawberry.enum
class EventType(Enum):
    MERGER = "MERGER"
    ACQUISITION = "ACQUISITION"
    LAWSUIT = "LAWSUIT"
    BANKRUPTCY = "BANKRUPTCY"
    IPO = "IPO"
    PARTNERSHIP = "PARTNERSHIP"

@strawberry.enum
class RelationshipType(Enum):
    COMPETES_WITH = "COMPETES_WITH"
    PARTNERS_WITH = "PARTNERS_WITH"
    SUPPLIES_TO = "SUPPLIES_TO"
    INVESTS_IN = "INVESTS_IN"
    WORKS_AT = "WORKS_AT"
    AFFECTS = "AFFECTS"
    MENTIONED_IN = "MENTIONED_IN"
    EXPOSED_TO = "EXPOSED_TO"

# Base Types
@strawberry.type
class Connection:
    """GraphQL Connection 패턴"""
    page_info: "PageInfo"
    edges: List["Edge"]
    total_count: int

@strawberry.type
class PageInfo:
    """페이지네이션 정보"""
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None

@strawberry.type
class Edge:
    """GraphQL Edge 패턴"""
    node: "Node"
    cursor: str

# Core Node Types
@strawberry.interface
class Node:
    """기본 노드 인터페이스"""
    id: strawberry.ID
    created_at: datetime
    updated_at: datetime

@strawberry.type
class Company(Node):
    """기업 노드"""
    id: strawberry.ID
    name: str
    name_en: Optional[str] = None
    aliases: List[str] = strawberry.field(default_factory=list)
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    country: Optional[str] = None
    stock_code: Optional[str] = None
    market_cap: Optional[float] = None
    employee_count: Optional[int] = None
    founded_year: Optional[int] = None
    risk_score: float = 5.0
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    competitors: List["Company"] = strawberry.field(default_factory=list)
    partners: List["Company"] = strawberry.field(default_factory=list)
    suppliers: List["Company"] = strawberry.field(default_factory=list)
    customers: List["Company"] = strawberry.field(default_factory=list)
    employees: List["Person"] = strawberry.field(default_factory=list)
    news_mentions: List["NewsArticle"] = strawberry.field(default_factory=list)
    risk_exposures: List["Risk"] = strawberry.field(default_factory=list)
    events: List["Event"] = strawberry.field(default_factory=list)

@strawberry.type
class Person(Node):
    """인물 노드"""
    id: strawberry.ID
    name: str
    aliases: List[str] = strawberry.field(default_factory=list)
    company: Optional[str] = None
    role: Optional[str] = None
    nationality: Optional[str] = None
    birth_year: Optional[int] = None
    influence_score: float = 5.0
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    works_at: Optional["Company"] = None
    mentioned_in: List["NewsArticle"] = strawberry.field(default_factory=list)
    related_events: List["Event"] = strawberry.field(default_factory=list)

@strawberry.type
class Risk(Node):
    """리스크 노드"""
    id: strawberry.ID
    category: RiskType
    level: int  # 1-10
    trend: str  # INCREASING, DECREASING, STABLE
    description: str
    mitigation: Optional[str] = None
    probability: Optional[float] = None  # 0-1
    impact: Optional[float] = None  # 0-1
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    affects_companies: List["Company"] = strawberry.field(default_factory=list)
    related_events: List["Event"] = strawberry.field(default_factory=list)

@strawberry.type
class Event(Node):
    """이벤트 노드"""
    id: strawberry.ID
    type: EventType
    title: str
    description: Optional[str] = None
    date: datetime
    severity: int = 5  # 1-10
    impact: float = 5.0  # 1-10
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    affects_companies: List["Company"] = strawberry.field(default_factory=list)
    involves_people: List["Person"] = strawberry.field(default_factory=list)
    related_risks: List["Risk"] = strawberry.field(default_factory=list)

@strawberry.type
class NewsArticle(Node):
    """뉴스 기사 노드"""
    id: strawberry.ID
    title: str
    content: Optional[str] = None
    url: str
    published_at: datetime
    source: str
    sentiment: float = 0.0  # -1 to 1
    risk_indicators: List[str] = strawberry.field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    mentions_companies: List["Company"] = strawberry.field(default_factory=list)
    mentions_people: List["Person"] = strawberry.field(default_factory=list)
    reports_events: List["Event"] = strawberry.field(default_factory=list)

# Relationship Types
@strawberry.type
class Relationship:
    """관계 기본 타입"""
    id: strawberry.ID
    type: RelationshipType
    from_node: Node
    to_node: Node
    properties: Optional[str] = None  # JSON string
    strength: Optional[float] = None
    confidence: Optional[float] = None
    created_at: datetime

@strawberry.type
class CompetitionRelationship(Relationship):
    """경쟁 관계"""
    intensity: float = 0.5  # 0-1
    market: Optional[str] = None
    market_share_overlap: Optional[float] = None

@strawberry.type
class PartnershipRelationship(Relationship):
    """파트너십 관계"""
    partnership_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    revenue_impact: Optional[float] = None

# Analysis Types
@strawberry.type
class NetworkAnalysis:
    """네트워크 분석 결과"""
    central_entity: Node
    connected_entities: int
    average_risk_score: float
    network_density: float
    clustering_coefficient: float
    centrality_scores: List["CentralityScore"]
    risk_paths: List["RiskPath"]

@strawberry.type
class CentralityScore:
    """중심성 점수"""
    node: Node
    betweenness: float
    closeness: float
    degree: int
    eigenvector: float
    pagerank: float

@strawberry.type
class RiskPath:
    """리스크 경로"""
    source: Node
    target: Node
    path: List[Node]
    risk_score: float
    path_length: int

@strawberry.type
class RiskAssessment:
    """리스크 평가"""
    entity: Node
    overall_risk: float
    risk_factors: List["RiskFactor"]
    risk_timeline: List["RiskTimePoint"]
    recommendations: List[str]

@strawberry.type
class RiskFactor:
    """리스크 요인"""
    category: RiskType
    score: float
    weight: float
    description: str
    evidence: List[Node]

@strawberry.type
class RiskTimePoint:
    """리스크 시점"""
    date: datetime
    risk_score: float
    events: List[Event]

# Search and Filter Types
@strawberry.input
class CompanyFilter:
    """기업 필터"""
    name: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    min_risk_score: Optional[float] = None
    max_risk_score: Optional[float] = None
    min_market_cap: Optional[float] = None
    max_market_cap: Optional[float] = None

@strawberry.input
class PersonFilter:
    """인물 필터"""
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    min_influence_score: Optional[float] = None

@strawberry.input
class EventFilter:
    """이벤트 필터"""
    type: Optional[EventType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_severity: Optional[int] = None
    involves_company: Optional[str] = None

@strawberry.input
class RiskFilter:
    """리스크 필터"""
    category: Optional[RiskType] = None
    min_level: Optional[int] = None
    max_level: Optional[int] = None
    trend: Optional[str] = None

@strawberry.input
class PaginationInput:
    """페이지네이션 입력"""
    first: Optional[int] = None
    after: Optional[str] = None
    last: Optional[int] = None
    before: Optional[str] = None

# Mutation Input Types
@strawberry.input
class CompanyInput:
    """기업 생성/수정 입력"""
    name: str
    name_en: Optional[str] = None
    aliases: Optional[List[str]] = None
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    country: Optional[str] = None
    stock_code: Optional[str] = None
    market_cap: Optional[float] = None
    employee_count: Optional[int] = None
    founded_year: Optional[int] = None

@strawberry.input
class PersonInput:
    """인물 생성/수정 입력"""
    name: str
    aliases: Optional[List[str]] = None
    company: Optional[str] = None
    role: Optional[str] = None
    nationality: Optional[str] = None
    birth_year: Optional[int] = None

@strawberry.input
class RelationshipInput:
    """관계 생성 입력"""
    from_id: strawberry.ID
    to_id: strawberry.ID
    type: RelationshipType
    properties: Optional[str] = None
    strength: Optional[float] = None
    confidence: Optional[float] = None

# Union Types
NodeUnion = Union[Company, Person, Risk, Event, NewsArticle]