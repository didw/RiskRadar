#!/bin/bash

# Archive Phase 1 Development Documentation
# This script moves completed Phase 1 sprint docs to an archive folder
# while keeping important reference documents accessible

echo "🗄️ Archiving Phase 1 Development Documentation..."

# Create archive directory
ARCHIVE_DIR="docs/archive/phase1"
mkdir -p $ARCHIVE_DIR

# Move completed sprint documentation
echo "📦 Archiving Sprint 1 documents..."
mv docs/trd/phase1/Sprint_*.md $ARCHIVE_DIR/ 2>/dev/null || echo "  No sprint files to archive"

# Move week-specific requirements
echo "📦 Archiving weekly requirement documents..."
find . -name "*Week[1-4]*.md" -path "*/docs/*" -exec mv {} $ARCHIVE_DIR/ \; 2>/dev/null || echo "  No weekly files to archive"

# Keep these important reference documents:
# - PRD_Overview.md (Product vision)
# - TRD_*_Squad_P1.md (Technical references)
# - Integration_Points.md (API contracts)
# - API_Standards.md (Standards)
# - Data_Models.md (Data structures)

echo "✅ Creating archive index..."
cat > $ARCHIVE_DIR/README.md << 'EOF'
# Phase 1 Archive

This directory contains completed Phase 1 development documentation that is no longer actively used but kept for historical reference.

## Archived Documents

### Sprint Documentation
- Sprint_0_Quick_Start.md - Initial setup sprint
- Sprint_1_Week*.md - Weekly sprint plans
- Sprint_Breakdown.md - Original sprint planning

### Weekly Requirements
- Various Week 1-4 requirement documents

## Important Active Documents (Not Archived)

The following documents remain in their original locations as they contain important reference information:

- `/docs/prd/PRD_Overview.md` - Product vision and strategy
- `/docs/trd/phase1/TRD_*_Squad_P1.md` - Technical architecture references
- `/docs/trd/common/Integration_Points.md` - API contracts
- `/docs/trd/common/API_Standards.md` - Development standards
- `/docs/trd/common/Data_Models.md` - Data structure definitions

## Phase 1 Completion Summary

- **Duration**: Weeks 1-4 (Completed 2025-07-19)
- **Major Achievement**: MVP with 7 news sources, ML pipeline, Graph DB, and API Gateway
- **Performance**: Exceeded all targets except ML F1-Score (56.3% vs 80% target)

For Phase 2 planning, see `/docs/prd/PRD_Phase2_Overview.md`
EOF

# Create a Phase Status document
echo "📄 Creating phase status document..."
cat > docs/PROJECT_STATUS.md << 'EOF'
# RiskRadar Project Status

> Last Updated: 2025-07-19

## 🎯 Current Phase: Phase 2 Planning

### ✅ Phase 1: Foundation (Weeks 1-4) - COMPLETED

**Achievements:**
- 7 news sources integrated (expanded from planned 5)
- ML pipeline operational (F1: 56.3%, need improvement to 80%)
- Graph database cluster deployed
- API Gateway with GraphQL
- Performance targets exceeded (processing: 2.57ms vs 10ms target)

**Key Metrics:**
- Data Processing: 1,000+ articles/hour ✅
- ML Inference: 389 docs/second ✅
- Graph Query: 15ms (1-hop), 145ms (3-hop) ✅
- System Uptime: 99%+ ✅

### 🚀 Phase 2: Production Ready (Weeks 5-8) - PLANNED

**Sprint 2 (Weeks 5-6): Enhanced Intelligence**
- [ ] ML F1-Score improvement to 80%+
- [ ] 15+ data sources
- [ ] Kubernetes migration
- [ ] Advanced graph analytics

**Sprint 3 (Weeks 7-8): Enterprise Features**  
- [ ] Multi-tenant architecture
- [ ] Enterprise security (RBAC, encryption)
- [ ] Business intelligence platform
- [ ] Public APIs and SDKs

### 🔮 Phase 3: Scale & Launch (Weeks 9-12) - PLANNED

**Sprint 4 (Weeks 9-10): Intelligent Automation**
- [ ] AI-powered insights
- [ ] Conversational interface
- [ ] Auto-scaling infrastructure
- [ ] Global deployment

**Sprint 5 (Weeks 11-12): Market Launch**
- [ ] Beta customer program
- [ ] 24/7 operations
- [ ] Production SLAs
- [ ] Revenue generation

## 📁 Key Documentation

### Planning Documents
- [Phase 2 PRD](/docs/prd/PRD_Phase2_Overview.md)
- [Phase 2 TRD](/docs/trd/phase2/TRD_Phase2_Overview.md)
- [Phase 3 PRD](/docs/prd/PRD_Phase3_Overview.md)

### Sprint Plans
- [Sprint 2: Enhanced Intelligence](/docs/trd/phase2/Sprint_2_Enhanced_Intelligence.md)
- [Sprint 3: Enterprise Features](/docs/trd/phase2/Sprint_3_Enterprise_Features.md)

### Reference Documents
- [API Standards](/docs/trd/common/API_Standards.md)
- [Data Models](/docs/trd/common/Data_Models.md)
- [Integration Points](/docs/trd/common/Integration_Points.md)

## 👥 Team Structure

### Squads
1. **Data Squad**: Data collection, quality, pipelines
2. **ML/NLP Squad**: Models, training, inference  
3. **Graph Squad**: Neo4j, analytics, algorithms
4. **Platform Squad**: Infrastructure, security, APIs

### Next Milestones
- **Week 5**: ML model reaches 80% F1-Score
- **Week 6**: 15+ data sources integrated
- **Week 7**: Multi-tenant architecture complete
- **Week 8**: Beta program ready

---

For archived Phase 1 documents, see `/docs/archive/phase1/`
EOF

echo "✅ Archive complete!"
echo ""
echo "📊 Summary:"
echo "- Archived documents moved to: $ARCHIVE_DIR"
echo "- Project status created at: docs/PROJECT_STATUS.md"
echo "- Important reference docs kept in original locations"
echo ""
echo "🚀 Ready for Phase 2 development!"