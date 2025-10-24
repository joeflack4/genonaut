# Performance Regression Alerts - Future Enhancement

## Overview
Implement an alerting system that monitors performance metrics and notifies administrators when significant performance degradation is detected in API endpoints or generation services.

## User Story
As a system administrator, I want to be automatically alerted when API endpoint response times or generation job durations exceed established thresholds, so that I can proactively investigate and resolve performance issues before they significantly impact users.

## Current State
- Route analytics data is collected and stored in PostgreSQL
- Generation analytics data is collected and stored in PostgreSQL
- Data is visible in the Analytics page but requires manual monitoring
- No automated alerts or notifications for performance degradation
- No threshold configuration or baseline tracking

## Proposed Enhancement

### Alert Types

**1. Route Performance Alerts**
- Slow endpoint alert (P95 latency exceeds threshold)
- Endpoint error rate spike (errors > threshold %)
- Traffic surge alert (requests spike beyond normal)
- Timeout frequency alert (statement_timeout errors)

**2. Generation Performance Alerts**
- Slow generation alert (avg duration exceeds threshold)
- High failure rate alert (failure % exceeds threshold)
- Queue backlog alert (queue length exceeds threshold)
- Generation throughput drop (completions/hour drops below threshold)

**3. System Health Alerts**
- Database query performance degradation
- Redis memory usage high
- Celery worker queue depth
- Disk space low

### Alert Configuration

**Threshold Types:**
1. **Static Thresholds** - Fixed values (e.g., P95 > 1000ms)
2. **Dynamic Thresholds** - Based on historical baselines (e.g., 2x normal)
3. **Percentage Change** - Relative to previous period (e.g., +50% increase)

**Example Configuration:**
```json
{
  "alerts": {
    "route_performance": {
      "enabled": true,
      "checks": [
        {
          "name": "Slow API Endpoint",
          "metric": "p95_latency_ms",
          "threshold_type": "static",
          "threshold_value": 1000,
          "comparison": "greater_than",
          "time_window_minutes": 15,
          "min_requests": 10,
          "severity": "warning"
        },
        {
          "name": "Critical Endpoint Latency",
          "metric": "p95_latency_ms",
          "threshold_type": "static",
          "threshold_value": 5000,
          "comparison": "greater_than",
          "time_window_minutes": 5,
          "min_requests": 5,
          "severity": "critical"
        },
        {
          "name": "Endpoint Error Rate Spike",
          "metric": "error_rate_percent",
          "threshold_type": "static",
          "threshold_value": 10,
          "comparison": "greater_than",
          "time_window_minutes": 10,
          "severity": "error"
        }
      ]
    },
    "generation_performance": {
      "enabled": true,
      "checks": [
        {
          "name": "Slow Image Generation",
          "metric": "avg_generation_duration_seconds",
          "threshold_type": "dynamic",
          "baseline_multiplier": 2.0,
          "time_window_minutes": 30,
          "severity": "warning"
        },
        {
          "name": "High Generation Failure Rate",
          "metric": "failure_rate_percent",
          "threshold_type": "static",
          "threshold_value": 15,
          "comparison": "greater_than",
          "time_window_minutes": 15,
          "min_generations": 10,
          "severity": "error"
        }
      ]
    }
  }
}
```

### Alert Delivery Channels

**1. In-App Notifications**
- Show in notification bell (existing NotificationBell component)
- Toast notification for critical alerts
- Red badge on Analytics page if active alerts

**2. Email Notifications**
- Send to admin email addresses
- Group by severity (immediate for critical, digest for warnings)
- Include alert details, metrics, and direct link to Analytics page

**3. Webhook Notifications**
- POST alert data to configured webhook URL
- For integration with Slack, Discord, PagerDuty, etc.
- Include alert metadata and context

**4. Dashboard Widget** (future)
- Active alerts widget on Dashboard page
- Color-coded by severity
- Click to view details

### Alert States

**Alert Lifecycle:**
1. **Triggered** - Threshold exceeded, alert created
2. **Active** - Alert is ongoing (condition still met)
3. **Acknowledged** - Admin has seen and acknowledged alert
4. **Resolved** - Condition no longer met, alert auto-resolved
5. **Silenced** - Admin has temporarily suppressed alert

**Alert Cooldown:**
- Don't re-trigger same alert within cooldown period (default: 1 hour)
- Prevents alert fatigue from persistent issues
- Configurable per alert type

### UI Design

**Analytics Page - Alert Banner:**
- Show prominent banner at top of page if active alerts
- Color-coded by severity:
  - Red: Critical
  - Orange: Error
  - Yellow: Warning
- Text: "X active alerts - [Alert name] (View Details)"
- Click expands to show alert details
- "Acknowledge" and "Silence" buttons

**Alert Details Page:**
- New page: `/settings/alerts`
- List of all alerts (active, acknowledged, resolved)
- Filters: Severity, Status, Date Range
- Each alert shows:
  - Alert name and description
  - Metric value vs threshold
  - Time triggered
  - Affected endpoint/service
  - Actions: Acknowledge, Silence, View Metrics
- Chart showing metric over time with threshold line

**Alert Configuration Page:**
- New page: `/settings/alerts/config`
- List of all alert rules
- Toggle to enable/disable each rule
- Edit button to modify thresholds
- Test button to simulate alert
- Create new alert rule form

### Database Schema

**Alerts Table:**
```sql
CREATE TABLE performance_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_rule_id INTEGER NOT NULL,
    alert_type VARCHAR(50) NOT NULL,  -- 'route_performance', 'generation_performance'
    alert_name VARCHAR(200) NOT NULL,
    severity VARCHAR(20) NOT NULL,    -- 'warning', 'error', 'critical'
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    threshold_value FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL,      -- 'triggered', 'active', 'acknowledged', 'resolved', 'silenced'
    triggered_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by_user_id UUID REFERENCES users(id),
    silenced_until TIMESTAMPTZ,
    context JSONB,                    -- Additional context (endpoint, route, etc.)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_perf_alerts_status ON performance_alerts(status);
CREATE INDEX idx_perf_alerts_severity ON performance_alerts(severity);
CREATE INDEX idx_perf_alerts_triggered ON performance_alerts(triggered_at DESC);
CREATE INDEX idx_perf_alerts_type ON performance_alerts(alert_type);
```

**Alert Rules Table:**
```sql
CREATE TABLE alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    alert_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    threshold_type VARCHAR(20) NOT NULL,  -- 'static', 'dynamic', 'percentage'
    threshold_value FLOAT,
    baseline_multiplier FLOAT,
    comparison VARCHAR(20),               -- 'greater_than', 'less_than', 'equal_to'
    time_window_minutes INTEGER NOT NULL,
    min_data_points INTEGER,
    severity VARCHAR(20) NOT NULL,
    cooldown_minutes INTEGER DEFAULT 60,
    enabled BOOLEAN DEFAULT TRUE,
    notification_channels JSONB,         -- ['in_app', 'email', 'webhook']
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Backend Implementation

**Celery Background Task:**
```python
@celery_app.task
def check_performance_alerts():
    """
    Run every 5 minutes to check for performance threshold violations.

    Steps:
    1. Load enabled alert rules from database
    2. For each rule, query recent analytics data
    3. Compare metric value to threshold
    4. If threshold exceeded, create or update alert
    5. If threshold not exceeded, resolve any active alerts
    6. Send notifications for new/critical alerts
    """
    alert_rules = get_enabled_alert_rules()

    for rule in alert_rules:
        metric_value = get_recent_metric_value(
            rule.alert_type,
            rule.metric_name,
            rule.time_window_minutes
        )

        threshold_exceeded = evaluate_threshold(
            metric_value,
            rule.threshold_value,
            rule.comparison
        )

        if threshold_exceeded:
            handle_alert_triggered(rule, metric_value)
        else:
            resolve_active_alerts(rule)
```

**Alert Evaluation Logic:**
```python
def evaluate_threshold(metric_value, threshold, comparison):
    """Evaluate if metric exceeds threshold."""
    if comparison == 'greater_than':
        return metric_value > threshold
    elif comparison == 'less_than':
        return metric_value < threshold
    elif comparison == 'equal_to':
        return metric_value == threshold
    return False

def calculate_dynamic_threshold(metric_name, baseline_multiplier):
    """Calculate threshold based on historical baseline."""
    # Get average of metric over last 7 days
    baseline = get_metric_baseline(metric_name, days=7)
    return baseline * baseline_multiplier

def get_recent_metric_value(alert_type, metric_name, time_window_minutes):
    """Query analytics data for recent metric value."""
    if alert_type == 'route_performance':
        return query_route_analytics_metric(metric_name, time_window_minutes)
    elif alert_type == 'generation_performance':
        return query_generation_analytics_metric(metric_name, time_window_minutes)
```

**Notification Service:**
```python
def send_alert_notification(alert, channels):
    """Send alert notification via configured channels."""
    if 'in_app' in channels:
        create_in_app_notification(alert)

    if 'email' in channels:
        send_alert_email(alert)

    if 'webhook' in channels:
        send_alert_webhook(alert)

def create_in_app_notification(alert):
    """Create notification in database for NotificationBell."""
    # Use existing notifications table
    pass

def send_alert_email(alert):
    """Send email to admin addresses."""
    recipients = get_admin_email_addresses()
    subject = f"[{alert.severity.upper()}] {alert.alert_name}"
    body = format_alert_email_body(alert)
    send_email(recipients, subject, body)

def send_alert_webhook(alert):
    """POST alert to webhook URL."""
    webhook_url = get_webhook_url()
    payload = {
        'alert_id': alert.id,
        'alert_name': alert.alert_name,
        'severity': alert.severity,
        'metric_name': alert.metric_name,
        'metric_value': alert.metric_value,
        'threshold_value': alert.threshold_value,
        'triggered_at': alert.triggered_at.isoformat(),
        'context': alert.context
    }
    requests.post(webhook_url, json=payload)
```

### API Endpoints

```python
# Get active alerts
GET /api/v1/alerts?status=active&severity=critical

# Get alert details
GET /api/v1/alerts/{alert_id}

# Acknowledge alert
POST /api/v1/alerts/{alert_id}/acknowledge

# Silence alert
POST /api/v1/alerts/{alert_id}/silence
Body: { "duration_minutes": 60 }

# Resolve alert (manual)
POST /api/v1/alerts/{alert_id}/resolve

# Get alert rules
GET /api/v1/alerts/rules

# Create alert rule
POST /api/v1/alerts/rules
Body: { "name": "...", "threshold_value": 1000, ... }

# Update alert rule
PATCH /api/v1/alerts/rules/{rule_id}

# Delete alert rule
DELETE /api/v1/alerts/rules/{rule_id}
```

### Frontend Implementation

**React Components:**
- `AlertBanner` - Banner at top of Analytics page
- `AlertsList` - List of alerts on Alerts page
- `AlertDetails` - Detailed view of single alert
- `AlertRulesList` - List of alert rules on config page
- `AlertRuleForm` - Form to create/edit alert rule

**React Query Hooks:**
- `useActiveAlerts()` - Fetch active alerts
- `useAlertDetails(alertId)` - Fetch alert details
- `useAcknowledgeAlert()` - Mutation to acknowledge
- `useSilenceAlert()` - Mutation to silence
- `useAlertRules()` - Fetch alert rules
- `useCreateAlertRule()` - Mutation to create rule

### Testing Requirements
- Unit test: Threshold evaluation logic
- Unit test: Dynamic baseline calculation
- Unit test: Alert cooldown logic
- Integration test: Celery task creates alerts correctly
- Integration test: Notifications are sent
- E2E test: User sees alert banner when alert triggered
- E2E test: User can acknowledge and silence alerts
- E2E test: Alert configuration page works

### Configuration Management
Store alert configuration in:
1. `config/base.json` - Default alert rules
2. Database - User-customized rules override defaults
3. Environment variables - Webhook URLs, email addresses

### Security Considerations
- Only admin users can configure alerts
- Rate limit webhook notifications to prevent abuse
- Validate webhook URLs before saving
- Sanitize alert context data (no PII)
- Encrypt webhook URLs in database

### Performance Considerations
- Alert checking task runs every 5 minutes (configurable)
- Batch query analytics data (don't query per-rule)
- Cache baseline calculations (refresh daily)
- Limit active alerts per rule (prevent spam)
- Archive resolved alerts after 90 days

### Monitoring the Monitoring
- Alert if alert system itself fails (meta-alert)
- Log all alert evaluations for debugging
- Track alert accuracy (false positives/negatives)
- Measure time from trigger to resolution

### Success Metrics
- Alerts trigger within 5 minutes of threshold violation
- False positive rate < 10%
- False negative rate < 1%
- Average time to acknowledge < 15 minutes
- Average time to resolution < 2 hours
- No missed critical alerts

### Dependencies
- Route analytics system must be operational
- Generation analytics system must be operational
- Email service configured (SMTP or SendGrid)
- Celery Beat for scheduled tasks
- Notification system in place

### Future Enhancements (beyond this task)
- Machine learning for anomaly detection
- Predictive alerts (forecast threshold violations)
- Alert correlation (group related alerts)
- Runbook automation (auto-remediation)
- Alert escalation policies
- On-call rotation integration
- Mobile push notifications
- Slack bot for alert management

### Estimated Effort
- Database schema and migrations: 2-3 hours
- Backend alert evaluation logic: 6-8 hours
- Backend API endpoints: 4-5 hours
- Frontend components: 8-10 hours
- Notification service: 4-5 hours
- Testing (unit + integration + E2E): 6-8 hours
- Configuration and documentation: 3-4 hours
- **Total: 33-43 hours (1-2 weeks)**

### Priority
**Low-Medium** - Valuable for production monitoring but not required for initial Analytics page launch. Should be implemented before production deployment to busy environments. Can be phased:
- Phase 1: Basic static thresholds + in-app notifications
- Phase 2: Dynamic thresholds + email notifications
- Phase 3: Webhook integration + advanced features
