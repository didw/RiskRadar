"""GraphQL 서버 설정"""
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.schema.config import StrawberryConfig
from typing import AsyncGenerator
import logging

from src.graphql.schema import *
from src.graphql.resolvers import Query, Mutation
from src.graphql.dataloaders import (
    company_loader, person_loader, event_loader,
    relationship_loader, company_competitor_loader,
    company_partner_loader, company_employee_loader,
    company_news_loader, company_risk_loader, company_event_loader
)

logger = logging.getLogger(__name__)


@strawberry.type
class Subscription:
    """GraphQL 구독 (향후 실시간 기능)"""
    
    @strawberry.subscription
    async def risk_score_updates(self, company_id: strawberry.ID) -> AsyncGenerator[float, None]:
        """리스크 점수 실시간 업데이트"""
        # TODO: Kafka 또는 WebSocket을 통한 실시간 스트림 구현
        yield 5.0


# GraphQL 스키마 생성
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(
        auto_camel_case=True,  # Python snake_case를 GraphQL camelCase로 자동 변환
    )
)


def get_context() -> dict:
    """GraphQL 컨텍스트 생성"""
    return {
        "dataloaders": {
            "company": company_loader,
            "person": person_loader,
            "event": event_loader,
            "relationship": relationship_loader,
            "company_competitors": company_competitor_loader,
            "company_partners": company_partner_loader,
            "company_employees": company_employee_loader,
            "company_news": company_news_loader,
            "company_risks": company_risk_loader,
            "company_events": company_event_loader,
        }
    }


# GraphQL 라우터 생성
graphql_router = GraphQLRouter(
    schema=schema,
    context_getter=get_context,
    graphiql=True,  # GraphiQL 인터페이스 활성화
)


def get_graphql_router() -> GraphQLRouter:
    """GraphQL 라우터 반환"""
    return graphql_router


# GraphQL Playground용 HTML
GRAPHQL_PLAYGROUND_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>RiskRadar Graph Service - GraphQL Playground</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphql-playground-react@1.7.26/build/static/css/index.css" />
</head>
<body>
    <div id="root">
        <style>
            body { margin: 0; font-family: 'Open Sans', sans-serif; overflow: hidden; }
            #root { height: 100vh; }
        </style>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/graphql-playground-react@1.7.26/build/static/js/middleware.js"></script>
    <script>
        window.addEventListener('load', function() {
            GraphQLPlayground.init(document.getElementById('root'), {
                endpoint: '/graphql',
                settings: {
                    'editor.theme': 'dark',
                    'editor.fontSize': 14,
                    'request.credentials': 'include',
                }
            })
        })
    </script>
</body>
</html>
"""