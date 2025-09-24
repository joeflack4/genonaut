# Development Monitoring Strategy

## Overview

This document outlines monitoring approaches for the development phase of Genonaut, focusing on pagination performance and application health during feature development and testing.

## Options Worth Considering

### Option 1: Built-in Logging + Simple Middleware
**Pros:**
- Zero external dependencies
- Immediate implementation
- Full control over what's logged
- No costs

**Cons:**
- Manual log analysis
- No visual dashboards
- Basic alerting only
- Requires log parsing scripts

### Option 2: Prometheus + Grafana (Self-hosted)
**Pros:**
- Industry standard metrics collection
- Beautiful, customizable dashboards
- Advanced alerting capabilities
- Open source and free
- Great learning experience
- Scales to production if needed

**Cons:**
- Initial setup complexity
- Need to manage infrastructure
- Learning curve for PromQL
- Resource overhead

### Option 3: Simple APM Tools (Lightweight SaaS)
**Pros:**
- Quick setup (SDK integration)
- Professional dashboards
- Automatic database monitoring
- Usually have free tiers

**Cons:**
- External dependency
- Limited customization
- May have data limits on free tier

## Recommended Course of Action

**For development phase: Prometheus + Grafana with simple FastAPI middleware**

### Why This Approach:
1. **Learning Value**: Understanding metrics collection will help in production
2. **No External Dependencies**: Keep development environment self-contained
3. **Scalability**: Can evolve into production monitoring
4. **Cost**: Completely free
5. **Flexibility**: Full control over metrics and dashboards
6. **Docker Integration**: Easy to add to existing docker-compose setup

## Implementation Specification

### Architecture
```
FastAPI App → Prometheus Middleware → Prometheus Server → Grafana Dashboards
     ↓
Application Logs → Structured JSON → Log Analysis Scripts
```

### Metrics to Collect

#### API Performance Metrics
- Request duration by endpoint
- Request count by status code
- Pagination-specific metrics (page size, offset, response time)
- Database query time
- Error rates

#### System Metrics
- Memory usage
- CPU usage
- Database connection pool stats
- Cache hit rates (when implemented)

#### Pagination-Specific Metrics
- Average pagination query time
- Page size distribution
- Most requested pages/offsets
- Cache hit rates (frontend)
- Pre-fetch efficiency

### Dashboard Requirements

#### Main Development Dashboard
- Request rate and response time trends
- Error rate monitoring
- Database performance
- Pagination performance metrics

#### Pagination Performance Dashboard
- Query time by page size
- Response time by offset range
- Most expensive pagination queries
- Cache performance metrics

## Task List

### Phase 1: Basic Infrastructure Setup

#### Task 1.1: Set up Prometheus + Grafana (USER)
- **Who**: User
- **Description**: Add Prometheus and Grafana services to docker-compose
- **Deliverables**:
  - Updated `docker-compose.yml` with Prometheus and Grafana services
  - Prometheus configuration file (`prometheus.yml`)
  - Grafana provisioning configuration
- **Estimated Time**: 2-3 hours
- **Notes**: Can use existing Docker knowledge, plenty of tutorials available

#### Task 1.2: Create basic monitoring middleware (AGENT)
- **Who**: Agent
- **Description**: Implement FastAPI middleware for basic metrics collection
- **Deliverables**:
  - `genonaut/api/middleware/metrics.py` - Prometheus metrics middleware
  - Integration with FastAPI app
  - Basic metrics: request_duration, request_count, error_rate
- **Test Command**: `make test-unit`

#### Task 1.3: Create structured logging (AGENT)
- **Who**: Agent
- **Description**: Enhance logging with structured JSON format
- **Deliverables**:
  - Updated logging configuration
  - Structured log format for easy parsing
  - Pagination-specific log entries
- **Files to modify**:
  - `genonaut/api/main.py`
  - `genonaut/api/config.py`

### Phase 2: Pagination Monitoring

#### Task 2.1: Add pagination-specific metrics (AGENT)
- **Who**: Agent
- **Description**: Extend middleware to track pagination performance
- **Deliverables**:
  - Pagination query time metrics
  - Page size and offset tracking
  - Database query time measurement
- **Files to modify**:
  - `genonaut/api/middleware/metrics.py`
  - Repository classes for query time tracking

#### Task 2.2: Create Grafana dashboards (USER)
- **Who**: User
- **Description**: Build dashboards for development monitoring
- **Deliverables**:
  - Main application performance dashboard
  - Pagination-specific performance dashboard
  - Database performance dashboard
- **Estimated Time**: 3-4 hours
- **Notes**: Agent can provide dashboard JSON configurations to import

#### Task 2.3: Database query monitoring (AGENT)
- **Who**: Agent
- **Description**: Add detailed database query performance tracking
- **Deliverables**:
  - SQLAlchemy event listeners for query timing
  - Slow query identification and logging
  - Query pattern analysis
- **Files to modify**:
  - `genonaut/api/dependencies.py`
  - Database configuration

### Phase 3: Development Tools

#### Task 3.1: Create monitoring utilities (AGENT)
- **Who**: Agent
- **Description**: Build helper scripts for development monitoring
- **Deliverables**:
  - Log analysis scripts
  - Performance testing utilities
  - Metrics export tools
- **Files to create**:
  - `scripts/analyze_logs.py`
  - `scripts/performance_test.py`
  - `scripts/export_metrics.py`

#### Task 3.2: Set up basic alerting (USER)
- **Who**: User
- **Description**: Configure Grafana alerts for critical issues
- **Deliverables**:
  - Alert rules for high error rates
  - Alert rules for slow pagination queries
  - Notification channels (email/Slack)
- **Estimated Time**: 1-2 hours

## Configuration Examples

### Prometheus Configuration (prometheus.yml)
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'genonaut-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

### Docker Compose Addition
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### FastAPI Metrics Endpoint Structure
```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics to implement
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration')
PAGINATION_QUERY_TIME = Histogram('pagination_query_duration_seconds', 'Pagination query time')
DATABASE_QUERY_TIME = Histogram('database_query_duration_seconds', 'Database query time')
```

## Success Criteria

### Technical Success
- [ ] Prometheus successfully collecting metrics from FastAPI
- [ ] Grafana dashboards showing real-time application performance
- [ ] Pagination metrics accurately tracked and visualized
- [ ] Database query performance visible in dashboards
- [ ] Basic alerting functional for critical issues

### Development Workflow Success
- [ ] Developers can quickly identify performance issues
- [ ] Pagination performance regressions are immediately visible
- [ ] Database query optimization guided by metrics
- [ ] Easy to correlate application changes with performance impact

## Timeline

### Week 1
- User: Set up Prometheus + Grafana infrastructure
- Agent: Implement basic monitoring middleware

### Week 2
- Agent: Add pagination-specific monitoring
- User: Create initial Grafana dashboards

### Week 3
- Agent: Enhance database query monitoring
- User: Set up basic alerting
- Both: Test and refine monitoring setup

## Resource Requirements

### System Resources
- **Additional Memory**: ~200MB for Prometheus + Grafana
- **Additional Disk**: ~1GB for metrics storage (development volumes)
- **Additional CPU**: Minimal impact during development

### Developer Time
- **User Tasks**: ~6-8 hours total setup and configuration
- **Agent Tasks**: ~8-10 hours implementation and testing
- **Ongoing**: ~30 minutes per week for dashboard maintenance

## Benefits for Development

1. **Immediate Feedback**: See performance impact of code changes instantly
2. **Regression Detection**: Catch performance regressions early
3. **Optimization Guidance**: Data-driven optimization decisions
4. **Production Readiness**: Smooth transition to production monitoring
5. **Learning Experience**: Gain valuable DevOps and monitoring skills

## Migration Path to Production

This development monitoring setup provides a clear path to production:
1. **Keep the same metrics structure** - just change collection endpoints
2. **Export Grafana dashboards** - can be imported to production Grafana
3. **Monitoring code is production-ready** - just needs configuration changes
4. **Alert rules transfer** - same alert logic works in production
5. **Operational knowledge** - team familiar with metrics and dashboards