# Runbook: High Latency Response

## Overview

This runbook provides step-by-step instructions for diagnosing and resolving high latency issues in our services.

## Severity Levels

- **P1 (Critical)**: Latency > 2x SLA, affecting > 50% of requests
- **P2 (High)**: Latency > 1.5x SLA, affecting > 25% of requests
- **P3 (Medium)**: Latency > SLA, affecting < 25% of requests

## Service Latency Thresholds

| Service | P95 SLA | P99 SLA | Critical Threshold |
|---------|---------|---------|-------------------|
| Auth Service | 150ms | 300ms | 300ms |
| Payment Service | 200ms | 500ms | 400ms |
| User Service | 100ms | 200ms | 200ms |

## Diagnosis Steps

### Step 1: Verify the Issue

1. Check monitoring dashboard
   - Navigate to Grafana: https://grafana.company.com
   - Select service dashboard
   - Verify latency metrics (p50, p95, p99)

2. Check recent deployments
   ```bash
   kubectl rollout history deployment/<service-name> -n production
   ```

3. Review error logs
   ```bash
   kubectl logs -n production deployment/<service-name> --tail=100
   ```

### Step 2: Identify the Bottleneck

#### Database Performance

1. Check database metrics
   - Query execution time
   - Connection pool usage
   - Lock wait time
   - Slow query log

2. Identify slow queries
   ```sql
   SELECT query, mean_exec_time, calls
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```

3. Check for missing indexes
   ```sql
   SELECT schemaname, tablename, attname, n_distinct, correlation
   FROM pg_stats
   WHERE schemaname = 'public'
   ORDER BY correlation;
   ```

#### Cache Performance

1. Check Redis metrics
   - Hit rate
   - Eviction rate
   - Memory usage
   - Connection count

2. Monitor cache hit ratio
   ```bash
   redis-cli INFO stats | grep keyspace
   ```

#### External Dependencies

1. Check third-party API latency
   - Payment gateway response time
   - Email service latency
   - SMS provider latency

2. Review circuit breaker status
   ```bash
   curl http://localhost:8080/actuator/health
   ```

#### Resource Constraints

1. Check CPU usage
   ```bash
   kubectl top pods -n production
   ```

2. Check memory usage
   ```bash
   kubectl describe pod <pod-name> -n production
   ```

3. Check network I/O
   ```bash
   kubectl exec -it <pod-name> -n production -- netstat -s
   ```

### Step 3: Immediate Mitigation

#### Option 1: Scale Horizontally

```bash
kubectl scale deployment/<service-name> -n production --replicas=10
```

#### Option 2: Increase Resource Limits

Edit deployment:
```yaml
resources:
  limits:
    cpu: "2000m"
    memory: "4Gi"
  requests:
    cpu: "1000m"
    memory: "2Gi"
```

Apply changes:
```bash
kubectl apply -f deployment.yaml
```

#### Option 3: Enable Cache Warming

```bash
curl -X POST http://<service-url>/admin/cache/warm
```

#### Option 4: Rollback Deployment

```bash
kubectl rollout undo deployment/<service-name> -n production
```

### Step 4: Long-term Resolution

#### Database Optimization

1. Add missing indexes
   ```sql
   CREATE INDEX idx_users_email ON users(email);
   CREATE INDEX idx_orders_user_id ON orders(user_id);
   ```

2. Optimize slow queries
   - Use EXPLAIN ANALYZE
   - Add appropriate indexes
   - Rewrite inefficient queries
   - Consider query caching

3. Implement connection pooling
   - Configure max connections
   - Set connection timeout
   - Enable connection reuse

#### Code Optimization

1. Profile application code
   - Use APM tools (New Relic, DataDog)
   - Identify hot paths
   - Optimize algorithms

2. Implement caching
   - Cache frequently accessed data
   - Use appropriate TTL
   - Implement cache invalidation

3. Optimize API calls
   - Batch requests
   - Implement pagination
   - Use GraphQL for selective fields

#### Infrastructure Optimization

1. Enable auto-scaling
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: service-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: service-name
     minReplicas: 3
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

2. Optimize load balancer settings
   - Adjust health check interval
   - Configure connection draining
   - Enable keep-alive

3. Implement CDN caching
   - Cache static assets
   - Configure cache headers
   - Use edge locations

## Monitoring and Alerts

### Alert Configuration

```yaml
alert: HighLatency
expr: http_request_duration_seconds{quantile="0.95"} > 0.3
for: 5m
labels:
  severity: warning
annotations:
  summary: "High latency detected on {{ $labels.service }}"
  description: "P95 latency is {{ $value }}s"
```

### Dashboard Widgets

1. Latency percentiles (p50, p95, p99)
2. Request rate
3. Error rate
4. Resource utilization
5. Database query time

## Escalation

### P1 (Critical)
- Immediately page on-call engineer
- Notify engineering manager
- Create incident in PagerDuty
- Start war room in Slack (#incidents)

### P2 (High)
- Notify on-call engineer
- Create ticket in Jira
- Update status page

### P3 (Medium)
- Create ticket in Jira
- Assign to service owner
- Schedule for next sprint

## Post-Incident Review

1. Document root cause
2. Timeline of events
3. Actions taken
4. Lessons learned
5. Action items to prevent recurrence

## References

- [Service Architecture](./architecture.md)
- [Monitoring Dashboard](https://grafana.company.com)
- [Incident Management](https://wiki.company.com/incident-management)
- [On-Call Rotation](https://pagerduty.company.com)

## Contact

- On-Call Engineer: oncall@company.com
- Platform Team: platform-team@company.com
- Database Team: dba-team@company.com
