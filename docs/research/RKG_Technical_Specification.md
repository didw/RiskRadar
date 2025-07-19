---

## 1. Canonical Domain Model

### 1.1 Core Node Labels & Key Properties

| Label | Mandatory Key(s)* | Other Frequently‑Queried Properties | Notes |
| --- | --- | --- | --- |
| `Company` | `companyId` (LEI/CIK/DUNS, **unique**) | `name`, `aliases` (array), `hqCountry`, `sector`, `industry`, `marketCapUSD` (float), `isPublic` (bool), `riskScore` (float), `updatedAt` | Central anchor for most traversals. |
| `Person` | `personId` (ORCID / internal) | `fullName`, `roles` (array), `primaryCompanyId`, `nationality`, `riskScore`, `updatedAt` | Covers executives, board members, regulators, litigants, journalists. |
| `Event` | `eventId` (UUID) | `eventType` (enum: *Merger, Lawsuit, Recall, …*), `title`, `description`, `eventDate`, `severity` (ordinal 1‑5), `sourceUri`, `ingestTimestamp` | Immutable. |
| `Regulation` | `regId` (URI / docket) | `title`, `jurisdiction`, `effectiveDate`, `status` (draft/active/repealed), `textHash` |  |
| `Trend` | `trendId` (UUID) | `name`, `taxonomy` (e.g., “AI Safety”), `timeWindowStart`, `timeWindowEnd`, `direction` (+/‑/flat), `signalStrength` (float) | Synced from NLP topic modeling. |
| `Source` | `sourceId` (URL hash) | `publisher`, `mediaType` (html/pdf/api), `crawlDate`, `credibilityScore` | Allows traceability & de‑duplication. |
| `Product` | `productId` | `name`, `category`, `launchDate`, `status` | Optional—adds granularity for product‑level events. |
| `Country` | `isoCode` | `name`, `region`, `economicRiskRating` | Useful for geo‑political risk. |
- Create **existence + uniqueness constraints** for each mandatory key (`CREATE CONSTRAINT … IS UNIQUE`).

### 1.2 Relationship Types & Key Attributes

| Type | Direction | Attributes | Semantics |
| --- | --- | --- | --- |
| `(:Person)-[:LEADS {role, sinceDate}]->(:Company)` | Person ➜ Company | `role`, `sinceDate`, `untilDate` | Executives, board, advisors. |
| `(:Company)-[:OWNS {pctOwned}]->(:Company)` | Parent ➜ Subsidiary | `pctOwned` (float) | Supports ownership roll‑ups. |
| `(:Company)-[:COMPETES_WITH]->(:Company)` | Undirected | `similarityScore` (float) | Symmetric; managed by analytic job; store once, treat as bidirectional. |
| `(:Company)-[:OPERATES_IN]->(:Country)` | Company ➜ Country | `since` | Supply‑chain exposure. |
| `(:Company)-[:INVOLVED_IN]->(:Event)` | Company ➜ Event | `role` (*Defendant, Acquirer, Issuer …*) |  |
| `(:Event)-[:MENTIONED_IN]->(:Source)` | Event ➜ Source | `confidence` (0‑1) | Link for explainability. |
| `(:Regulation)-[:APPLIES_TO]->(:Company)` | Regulation ➜ Company | `complianceStatus` (*Compliant, Non‑compliant*), `evidenceUri` |  |
| `(:Trend)-[:AFFECTS]->(:Industry {name})` | Trend ➜ Industry (as a node or string property) | `impactScore` |  |
| `(:Company)-[:LINKED {type, hops, algorithm, confidence}]->(:Company)` | Company ➜ Company | **Inferred edges** produced by graph algorithms; `type` (*SharedSupplier, BoardInterlock,* etc.). |  |

> Why separate Source? Traceability, provenance scoring, and easier “why is this edge here?” explanations.
> 

---

## 2. Scalable Data‑Ingestion & Update Pipeline

```
            ┌─────────────┐
            │ Web Crawlers│  (RSS/API/Scraping)
            └─────┬───────┘
                  ▼
        ┌───────────────────────┐
        │  Stream Ingestion Bus │  (Kafka / Pulsar)
        └─────┬─────────┬───────┘
   raw_html   ▼         ▼  structured_feeds
        ┌──────────┐   ┌─────────┐
        │ NLP/IE   │   │ Parsers │
        │  (Spark) │   │ (Flink) │
        └────┬─────┘   └────┬────┘
             ▼             ▼
        enriched JSON  ↔  reference data
             ▼
        ┌──────────┐
        │  Neo4j   │   ←  batch via **APOC.periodic.iterate** or **Kafka Connect Neo4j Sink**
        └──────────┘

```

### 2.1 Key Steps

1. **Crawl / Poll** web APIs, RSS, regulatory filings.
2. **Streaming Bus** buffers & orders messages; partitions by `companyId` for parallelism.
3. **Enrichment Layer**
   - Language detection, named‑entity recognition (NER).
   - Entity resolution (dedup) via **spaCy**, **BERT embeddings + cosine**, or vendor (OpenCalais, Diffbot).
4. **Schema Mapping** ➜ domain JSON:

   ```
   {
     "entityType": "Company",
     "companyId": "US5949181045",
     "properties": {…},
     "relationships": [
       {"type": "INVOLVED_IN", "targetId": "EVT_123", "role": "Defendant"}
     ]
   }

   ```

5. **Upsert to Neo4j** using `MERGE` on key(s); rels use `MERGE` + `ON CREATE SET` for immutables, `ON MATCH SET` for updates.
6. **Post‑Ingest Jobs**
   - **Graph algorithms** (FastRP, Node2Vec, Betweenness) to produce `LINKED` inferred edges.
   - **Risk scoring** per node (custom composite algorithm) stored in `riskScore`.
7. **Data Retention & TTL**
   - Soft‑delete by adding `archived:true, archivedAt` instead of hard deletes.
   - Periodic purge job keeps disk usage predictable.

---

## 3. Update & Maintenance Strategy

| Task                                   | Cadence                                                       | Tooling                                                           |
| -------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------- |
| **Incremental ingest**                 | Near‑real‑time (<5 min lag)                                   | Kafka Connect sink, idempotent Cypher.                            |
| **Re‑crawl high‑value sources**        | Hourly / daily depending on volatility                        | Job scheduler (Airflow).                                          |
| **Re‑compute inferred edges & scores** | Nightly full run + streaming micro‑batch for deltas           | Neo4j GDS (Graph Data Science) on dedicated analytics cluster.    |
| **Schema migrations**                  | Versioned Liquibase‑type scripts; zero‑downtime using Fabric. |                                                                   |
| **Index rebuild & stats update**       | Weekly (during low‑traffic)                                   | `CALL db.index.fulltext.awaitEventuallyConsistentIndexRefresh()`. |
| **Backup & Restore**                   | Hot backups hourly; cold backups nightly                      | Neo4j Ops Manager.                                                |

---

## 4. Query Layer & Optimization

### 4.1 Common Query Patterns

| Use Case                                                                                    | Cypher Sketch                                                                                    | Optimizations                                |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------- |
| **Company briefing (direct facts)**                                                         | `MATCH (c:Company {companyId:$id})-[:LEADS                                                       | INVOLVED_IN                                  |
| **Hidden links between two firms**                                                          | `MATCH p=shortestPath((a:Company {companyId:$a})-[:LEADS                                         | OWNS                                         |
| **Industry‑level trend impact**                                                             | `MATCH (t:Trend {name:$trend})-[:AFFECTS]->(i:Industry)<-[:OPERATES_IN]-(c:Company) RETURN c, t` | Index on `Trend(name)`, `Company(industry)`. |
| **Meeting prep (LigaChem Bio)**                                                             | ```cypher                                                                                        |                                              |
| MATCH (c:Company)-[:INVOLVED_IN                                                             | OWNS                                                                                             | COMPETES_WITH                                |
| WHERE c.name =~ '(?i)LigaChem Bio.\*' AND (x:Event OR x:Trend OR x:Regulation OR x:Company) |                                                                                                  |                                              |
| RETURN x, relationships(p) ORDER BY x.eventDate DESC LIMIT 50                               |                                                                                                  |                                              |
| ```                                                                                         | Use full‑text index on `Company.name`; apply a **relationship type filter** to prune paths.      |                                              |

### 4.2 Index & Constraint Strategy

| Index Type                     | Target                                              | Purpose                                                |
| ------------------------------ | --------------------------------------------------- | ------------------------------------------------------ |
| **Uniqueness constraints**     | All IDs (`companyId`, `personId`…)                  | De‑dupe & MERGE speed.                                 |
| **Composite b‑tree**           | `(Company, sector, hqCountry)`                      | Analytical slicing.                                    |
| **Range indexes**              | `Event.eventDate`, `Trend.signalStrength`           | Time‑series queries; enable `ORDER BY eventDate DESC`. |
| **Full‑text**                  | `Company{name,aliases}`, `Event{title,description}` | Keyword search entry points.                           |
| **Relationship indexes (v5+)** | `[:LEADS(role)]`, `[:INVOLVED_IN(role)]`            | Reduces filtering cost on rel properties.              |
| **Bloom Filter** (GDS)         | For `COMPETES_WITH` sparsity                        | Speeds up existence checks in large neighbor sets.     |

> Partitioning / Sharding:
>
> - Use **Neo4j Fabric**: logical shards by `hqCountry` or hash of `companyId` to horizontally scale while preserving global query via Fabric Coordinator.
> - Keep high‑connectivity “core” firms replicated across shards if necessary (hot‑spot mitigation).

---

## 5. Capturing Hidden & Indirect Relationships

1. **Similarity‑based LINKED edges**
   - **FastRP / Node2Vec** vector embeddings → cosine > 0.8 → `LINKED {algorithm:'FastRP', similarity:0.87}`.
2. **Path‑based Inference**
   - Multi‑hop pattern detection (e.g., shared supplier ➜ shared board member ➜ same auditor) encoded in GDS rules.
3. **Rule‑Driven Patterns** (APOC triggers)

   ```
   MATCH (c1:Company)-[:LEADS]->(:Person)-[:LEADS]->(c2:Company)
   WHERE id(c1) < id(c2)
   MERGE (c1)-[:LINKED {type:'BoardInterlock', hops:2, confidence:1.0}]->(c2);

   ```

4. **Temporal Co‑movement** (Event correlation)
   - Correlate spikes in `riskScore` within 30 days window → `LINKED {type:'RiskCoMovement', confidence:0.6}`.
5. Store **inferred edges** in a **separate relationship type** (`LINKED`) with `confidence` and `algorithm` so they can be **filtered or refreshed** without disturbing curated data.

---

## 6. Performance, Scalability & Reliability

| Challenge                        | Mitigation                                                                                                                                          |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Write throughput spikes          | Buffer in Kafka; use **batch size 5 000** in sink; **MERGE** on constrained keys prevents duplicates.                                               |
| Hotspot nodes (e.g., Apple Inc.) | **Super‑node pattern**: split by relationship type; store outbound `COMPETES_WITH` in separate shards; enable **degree‑based sampling** in queries. |
| Graph algorithms on TB‑scale     | **Neo4j GDS Enterprise** on analytic‑only replica; stream results back.                                                                             |
| Memory pressure                  | **Node property compression**; move rarely‑accessed text to `Source` nodes only; apply `dbms.memory.transaction.global_max_size`.                   |
| Failure recovery                 | Multi‑cluster causal clustering; Fabric‑aware backups; Chaos testing.                                                                               |

---

## 7. Governance & Observability

- **Data Lineage**: every node/relationship carries `sourceId` → `Source`.
- **Quality Scores**: `credibilityScore` (source) and `confidence` (edge) power query filters (`WHERE confidence > 0.7`).
- **Monitoring**: Neo4j Ops metrics to Prometheus → Grafana dashboards (ingest lag, query latency, heap).
- **Security**: Row‑level security via Neo4j RBAC; mask PII fields (`fullName`) with attribute‑based access controls.
- **Versioning**: For mutable entities (Company), keep `updatedAt` + history in **time‑trees** if regulatory traceability is required.

---

## 8. Implementation Checklist

1. **Create schema constraints & indexes** (Cypher migration).
2. **Set up Fabric cluster** + per‑shard databases.
3. **Deploy Kafka Connect Neo4j Sink** with exactly‑once semantics.
4. **Build enrichment layer** (Spark NLP, entity resolution service).
5. **Develop APOC‑based upsert procedures**; normalize UTC timestamps.
6. **Schedule GDS pipelines** (link prediction, risk scoring).
7. **Publish GraphQL / REST façade** for consuming apps & dashboards (e.g., Neo4j GraphQL Library).
8. **Load test** with Gatling or k6 to validate 99‑th percentile latency targets.
9. **Set up CI/CD** (Liquibase‑like migrations + Helm charts).
10. **Document** Cypher query cookbook and operational runbooks.

---

### Ready for Day‑1

With the above architecture, the Risk Knowledge Graph will:

- **Scale horizontally** (Fabric, Kafka, stateless enrichment).
- **Support real‑time insights** (sub‑minute ingest → queryable).
- **Expose indirect risk signals** via algorithmic relationships.
- **Remain maintainable** thanks to constrained schema, versioned migrations, and automated re‑indexing.

[Smart Categorization of “Events” (2)](https://www.notion.so/Smart-Categorization-of-Events-2-234a615a10ce809b8875f48a630d27ff?pvs=21)
