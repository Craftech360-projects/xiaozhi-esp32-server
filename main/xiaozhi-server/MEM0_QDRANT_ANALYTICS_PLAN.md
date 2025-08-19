# Mem0 + Qdrant Analytics Implementation Plan

## Executive Summary
This plan outlines how to implement a comprehensive analytics system using mem0 for AI-powered memory management while leveraging direct Qdrant access for metrics and insights.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Input    │────▶│  Mem0 Service   │────▶│  Your Qdrant    │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                        ┌─────────────────┐              │
                        │Analytics Service│◀─────────────┘
                        └────────┬────────┘
                                 │
                        ┌────────┴────────┐
                        │   Dashboard     │
                        └─────────────────┘
```

## Phase 1: Setup Infrastructure (Week 1)

### 1.1 Qdrant Setup
- [ ] Create Qdrant Cloud account or set up self-hosted instance
- [ ] Configure security and access controls
- [ ] Document connection credentials

### 1.2 Update Configuration
```yaml
# config.yaml
Memory:
  mem0_with_analytics:
    type: mem0ai
    api_key: ${MEM0_API_KEY}
    vector_store:
      provider: "qdrant"
      config:
        url: ${QDRANT_URL}
        api_key: ${QDRANT_API_KEY}
        collection_name: "mem0_memories"
        
Analytics:
  qdrant_direct:
    url: ${QDRANT_URL}  # Same as above
    api_key: ${QDRANT_API_KEY}
    collection_name: "mem0_memories"
    analytics_collection: "usage_metrics"
```

### 1.3 Dependencies Installation
```bash
pip install mem0ai qdrant-client pandas streamlit plotly
```

## Phase 2: Analytics Infrastructure (Week 1-2)

### 2.1 Create Analytics Module
```
/core/analytics/
├── __init__.py
├── base.py
├── mem0_analytics.py
├── metrics_collector.py
└── dashboard/
    ├── app.py
    └── pages/
```

### 2.2 Implement Base Analytics Class
```python
# /core/analytics/base.py
from abc import ABC, abstractmethod
from qdrant_client import QdrantClient
import pandas as pd

class AnalyticsBase(ABC):
    def __init__(self, qdrant_config):
        self.client = QdrantClient(
            url=qdrant_config['url'],
            api_key=qdrant_config['api_key']
        )
        self.mem0_collection = qdrant_config['collection_name']
        
    @abstractmethod
    def collect_metrics(self):
        pass
    
    @abstractmethod
    def generate_report(self):
        pass
```

### 2.3 Implement Mem0 Analytics Adapter
```python
# /core/analytics/mem0_analytics.py
class Mem0Analytics(AnalyticsBase):
    def __init__(self, config):
        super().__init__(config)
        self.metrics_cache = {}
        
    def discover_schema(self):
        """Discover mem0's data structure"""
        # Implementation to analyze mem0's payload structure
        
    def collect_metrics(self):
        """Collect metrics from mem0's data"""
        # Implementation
```

## Phase 3: Metrics Collection System (Week 2)

### 3.1 Core Metrics to Track

| Metric Category | Specific Metrics | Collection Method |
|----------------|------------------|-------------------|
| **Usage** | Total memories, Active users, Daily/Weekly/Monthly activity | Direct Qdrant query |
| **Performance** | Query latency, Save latency, Vector search time | Logging + Analytics DB |
| **Content** | Topic distribution, Sentiment analysis, Language detection | NLP processing |
| **Quality** | Memory relevance scores, Retrieval success rate | User feedback + logs |
| **System** | Storage usage, Vector dimensions, Collection size | Qdrant stats |

### 3.2 Implement Metrics Collector
```python
# /core/analytics/metrics_collector.py
import asyncio
from datetime import datetime
from typing import Dict, List

class MetricsCollector:
    def __init__(self, analytics_client, collection_interval=300):
        self.analytics = analytics_client
        self.interval = collection_interval
        self.running = False
        
    async def start(self):
        """Start continuous metrics collection"""
        self.running = True
        while self.running:
            await self.collect_all_metrics()
            await asyncio.sleep(self.interval)
    
    async def collect_all_metrics(self):
        metrics = {
            'timestamp': datetime.utcnow(),
            'usage': await self.collect_usage_metrics(),
            'performance': await self.collect_performance_metrics(),
            'content': await self.collect_content_metrics()
        }
        await self.store_metrics(metrics)
```

### 3.3 Implement Wrapper for Tracking
```python
# /core/providers/memory/mem0ai/mem0ai_with_analytics.py
from .mem0ai import MemoryProvider as BaseMem0Provider
from core.analytics.metrics_collector import MetricsCollector
import time

class MemoryProvider(BaseMem0Provider):
    def __init__(self, config, summary_memory=None):
        super().__init__(config, summary_memory)
        
        # Initialize analytics
        analytics_config = config.get('analytics', {})
        if analytics_config.get('enabled', False):
            self.analytics = MetricsCollector(analytics_config)
        else:
            self.analytics = None
    
    async def save_memory(self, msgs):
        start_time = time.time()
        
        # Call original mem0 save
        result = await super().save_memory(msgs)
        
        # Track metrics
        if self.analytics:
            await self.analytics.track_event('memory_save', {
                'user_id': self.role_id,
                'message_count': len(msgs),
                'latency': time.time() - start_time,
                'success': result is not None
            })
        
        return result
    
    async def query_memory(self, query: str) -> str:
        start_time = time.time()
        
        # Call original mem0 query
        result = await super().query_memory(query)
        
        # Track metrics
        if self.analytics:
            await self.analytics.track_event('memory_query', {
                'user_id': self.role_id,
                'query_length': len(query),
                'result_length': len(result),
                'latency': time.time() - start_time,
                'has_results': bool(result)
            })
        
        return result
```

## Phase 4: Analytics Dashboard (Week 2-3)

### 4.1 Dashboard Structure
```
/dashboard/
├── app.py                 # Main Streamlit app
├── pages/
│   ├── overview.py       # Overview metrics
│   ├── users.py          # User analytics
│   ├── content.py        # Content analysis
│   ├── performance.py    # Performance metrics
│   └── realtime.py       # Real-time monitoring
├── components/
│   ├── charts.py         # Reusable chart components
│   └── filters.py        # Date/user filters
└── utils/
    └── data_processor.py # Data processing utilities
```

### 4.2 Main Dashboard Implementation
```python
# /dashboard/app.py
import streamlit as st
from core.analytics.mem0_analytics import Mem0Analytics
import plotly.express as px

st.set_page_config(page_title="Memory Analytics", layout="wide")

# Initialize analytics
@st.cache_resource
def init_analytics():
    config = load_config()
    return Mem0Analytics(config['Analytics']['qdrant_direct'])

analytics = init_analytics()

# Sidebar
st.sidebar.title("Memory Analytics")
page = st.sidebar.selectbox("Select Page", 
    ["Overview", "Users", "Content", "Performance", "Real-time"])

# Main content
if page == "Overview":
    st.title("Memory System Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    metrics = analytics.get_overview_metrics()
    
    col1.metric("Total Memories", f"{metrics['total_memories']:,}")
    col2.metric("Active Users", metrics['active_users'])
    col3.metric("Avg Response Time", f"{metrics['avg_response_ms']:.0f}ms")
    col4.metric("Success Rate", f"{metrics['success_rate']:.1f}%")
    
    # Charts
    st.subheader("Memory Growth Over Time")
    growth_data = analytics.get_memory_growth()
    fig = px.line(growth_data, x='date', y='cumulative_memories')
    st.plotly_chart(fig, use_container_width=True)
```

## Phase 5: Advanced Analytics Features (Week 3-4)

### 5.1 Memory Quality Scoring
```python
class MemoryQualityAnalyzer:
    def score_memory(self, memory_payload):
        """Score memory quality based on multiple factors"""
        score = 0
        
        # Length and completeness
        content = memory_payload.get('content', '')
        if len(content) > 100:
            score += 2
        
        # Contains actionable information
        actionable_keywords = ['prefer', 'like', 'dislike', 'always', 'never']
        for keyword in actionable_keywords:
            if keyword in content.lower():
                score += 1
        
        # Recency
        timestamp = memory_payload.get('timestamp')
        if timestamp:
            age_days = (datetime.now() - timestamp).days
            if age_days < 7:
                score += 2
            elif age_days < 30:
                score += 1
        
        return min(score, 10)  # Max score of 10
```

### 5.2 User Segmentation
```python
class UserSegmentation:
    def segment_users(self, user_metrics_df):
        """Segment users based on usage patterns"""
        segments = {
            'power_users': user_metrics_df[
                (user_metrics_df['memory_count'] > 100) & 
                (user_metrics_df['days_active'] > 30)
            ],
            'regular_users': user_metrics_df[
                (user_metrics_df['memory_count'].between(10, 100)) & 
                (user_metrics_df['days_active'] > 7)
            ],
            'new_users': user_metrics_df[
                user_metrics_df['days_active'] <= 7
            ],
            'inactive_users': user_metrics_df[
                user_metrics_df['last_activity_days_ago'] > 30
            ]
        }
        return segments
```

### 5.3 Predictive Analytics
```python
class PredictiveAnalytics:
    def predict_churn(self, user_activity_data):
        """Predict user churn probability"""
        # Simple rule-based prediction
        # Can be enhanced with ML models
        
    def forecast_growth(self, historical_data):
        """Forecast memory growth"""
        # Time series forecasting
```

## Phase 6: Integration & Testing (Week 4)

### 6.1 Integration Points

1. **Memory Provider Integration**
   - Update mem0ai provider to include analytics hooks
   - Ensure backward compatibility

2. **API Endpoints**
   ```python
   # Add to existing API
   @app.get("/api/analytics/overview")
   async def get_analytics_overview():
       return analytics.get_overview_metrics()
   
   @app.get("/api/analytics/user/{user_id}")
   async def get_user_analytics(user_id: str):
       return analytics.get_user_metrics(user_id)
   ```

3. **Scheduled Jobs**
   ```python
   # Add to scheduler
   schedule.every(5).minutes.do(collect_metrics)
   schedule.every().hour.do(generate_hourly_report)
   schedule.every().day.at("02:00").do(cleanup_old_metrics)
   ```

### 6.2 Testing Strategy

| Test Type | Coverage | Tools |
|-----------|----------|-------|
| Unit Tests | Analytics functions, Metrics calculations | pytest |
| Integration Tests | Qdrant connection, Mem0 integration | pytest + fixtures |
| Load Tests | Dashboard performance, Query efficiency | locust |
| E2E Tests | Full analytics pipeline | selenium |

## Phase 7: Deployment & Monitoring (Week 5)

### 7.1 Deployment Architecture
```yaml
# docker-compose.yml addition
services:
  analytics-dashboard:
    build: ./dashboard
    ports:
      - "8501:8501"
    environment:
      - QDRANT_URL=${QDRANT_URL}
      - QDRANT_API_KEY=${QDRANT_API_KEY}
    depends_on:
      - xiaozhi-server
  
  metrics-collector:
    build: ./analytics
    environment:
      - COLLECTION_INTERVAL=300
    depends_on:
      - analytics-dashboard
```

### 7.2 Monitoring Setup
- Set up alerts for anomalies
- Monitor dashboard performance
- Track analytics accuracy

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Setup | Qdrant configured, Dependencies installed |
| 1-2 | Analytics Infrastructure | Base classes, Analytics module |
| 2 | Metrics Collection | Collector implemented, Wrapper created |
| 2-3 | Dashboard | Basic dashboard with 5 pages |
| 3-4 | Advanced Features | Quality scoring, Segmentation, Predictions |
| 4 | Integration & Testing | Fully integrated, Tests passing |
| 5 | Deployment | Production deployment, Monitoring active |

## Success Metrics

1. **Technical Success**
   - Analytics latency < 100ms
   - Dashboard load time < 2s
   - 99% uptime

2. **Business Success**
   - Daily active dashboard users
   - Actionable insights generated
   - Memory quality improvement

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mem0 schema changes | High | Version detection, Schema discovery |
| Qdrant performance | Medium | Caching, Indexing optimization |
| Dashboard scalability | Medium | Pagination, Data aggregation |

## Next Steps

1. Review and approve plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Weekly progress reviews

## Appendix: Configuration Templates

### A. Environment Variables
```bash
# .env
MEM0_API_KEY=your-mem0-key
QDRANT_URL=https://your-qdrant.qdrant.io
QDRANT_API_KEY=your-qdrant-key
ANALYTICS_ENABLED=true
DASHBOARD_PORT=8501
```

### B. Monitoring Alerts
```yaml
# alerts.yaml
alerts:
  - name: high_memory_latency
    condition: avg(memory_save_latency) > 1000ms
    action: notify_slack
    
  - name: low_retrieval_rate
    condition: memory_retrieval_success_rate < 80%
    action: notify_ops_team
```

This implementation plan provides a structured approach to building a comprehensive analytics system on top of mem0 and Qdrant, giving you the best of both worlds!