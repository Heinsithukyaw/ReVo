# 📋 reVoAgent Operational Runbook

**Version**: 1.0  
**Date**: June 11, 2025  
**Target**: Production Operations Team

---

## 🎯 Daily Operations Checklist

### Morning Health Check (9:00 AM)

```bash
#!/bin/bash
# Daily health check script

echo "🌅 reVoAgent Daily Health Check - $(date)"
echo "================================================"

# 1. Check all services are running
echo "📊 Service Status:"
docker-compose ps
kubectl get pods -l app=revoagent

# 2. Check system resources
echo -e "\n💻 System Resources:"
free -h
df -h /
docker system df

# 3. Check API health
echo -e "\n🔍 API Health:"
curl -f http://localhost:8000/health || echo "❌ API Health Check Failed"

# 4. Check monitoring
echo -e "\n📈 Monitoring Status:"
curl -f http://localhost:9090/-/healthy || echo "❌ Prometheus Down"
curl -f http://localhost:3000/api/health || echo "❌ Grafana Down"

# 5. Check recent errors
echo -e "\n🚨 Recent Errors (Last 1 hour):"
docker logs revoagent-api --since 1h | grep -i error | tail -5

# 6. Check cost optimization
echo -e "\n💰 Cost Optimization Status:"
curl -s http://localhost:8000/api/v1/metrics/cost | jq '.local_usage_percentage'

echo -e "\n✅ Daily health check completed!"
```

### Evening Maintenance (6:00 PM)

```bash
#!/bin/bash
# Evening maintenance script

echo "🌆 reVoAgent Evening Maintenance - $(date)"
echo "============================================="

# 1. Backup databases
echo "💾 Creating backups..."
pg_dump -h localhost -U revoagent revoagent_prod > /backup/db_$(date +%Y%m%d).sql
redis-cli --rdb /backup/redis_$(date +%Y%m%d).rdb

# 2. Clean up logs
echo "🧹 Cleaning up logs..."
find /var/log/revoagent -name "*.log" -mtime +7 -delete
docker system prune -f

# 3. Update security patches
echo "🔒 Checking for security updates..."
apt list --upgradable | grep -i security

# 4. Generate daily report
echo "📊 Generating daily report..."
python /app/scripts/generate_daily_report.py

echo "✅ Evening maintenance completed!"
```

---

## 📊 Monitoring & Alerting

### Key Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| API Response Time | > 2 seconds | Scale horizontally |
| CPU Usage | > 80% | Investigate load |
| Memory Usage | > 85% | Check for leaks |
| Disk Usage | > 90% | Clean up space |
| Error Rate | > 5% | Check logs |
| Local Model Usage | < 90% | Optimize routing |

### Alert Response Procedures

#### High CPU Usage Alert
```bash
# 1. Check current load
top -p $(pgrep -f revoagent)

# 2. Identify bottlenecks
docker stats revoagent-api

# 3. Scale if needed
kubectl scale deployment revoagent-api --replicas=5

# 4. Investigate root cause
docker logs revoagent-api --tail 100 | grep -i cpu
```

#### Memory Leak Alert
```bash
# 1. Check memory usage trend
free -h
docker stats --no-stream

# 2. Restart affected service
docker-compose restart revoagent-api

# 3. Monitor for recurrence
watch -n 5 'docker stats --no-stream | grep revoagent'

# 4. Collect heap dump if needed
docker exec revoagent-api python -c "import gc; gc.collect(); print('GC completed')"
```

---

## 🔄 Deployment Procedures

### Rolling Deployment

```bash
#!/bin/bash
# Rolling deployment script

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

echo "🚀 Starting rolling deployment to version $VERSION"

# 1. Update image version
kubectl set image deployment/revoagent-api revoagent-api=revoagent:$VERSION

# 2. Wait for rollout
kubectl rollout status deployment/revoagent-api --timeout=300s

# 3. Verify health
sleep 30
curl -f http://localhost:8000/health || {
    echo "❌ Health check failed, rolling back..."
    kubectl rollout undo deployment/revoagent-api
    exit 1
}

# 4. Run smoke tests
python /app/tests/smoke_tests.py || {
    echo "❌ Smoke tests failed, rolling back..."
    kubectl rollout undo deployment/revoagent-api
    exit 1
}

echo "✅ Deployment completed successfully!"
```

### Blue-Green Deployment

```bash
#!/bin/bash
# Blue-green deployment script

VERSION=$1
CURRENT_ENV=$(kubectl get service revoagent-api -o jsonpath='{.spec.selector.version}')
NEW_ENV=$([ "$CURRENT_ENV" = "blue" ] && echo "green" || echo "blue")

echo "🔄 Blue-Green Deployment: $CURRENT_ENV -> $NEW_ENV (version $VERSION)"

# 1. Deploy to inactive environment
kubectl apply -f k8s/deployment-$NEW_ENV.yaml
kubectl set image deployment/revoagent-api-$NEW_ENV revoagent-api=revoagent:$VERSION

# 2. Wait for deployment
kubectl rollout status deployment/revoagent-api-$NEW_ENV

# 3. Test new environment
curl -f http://revoagent-api-$NEW_ENV:8000/health || {
    echo "❌ New environment health check failed"
    exit 1
}

# 4. Switch traffic
kubectl patch service revoagent-api -p '{"spec":{"selector":{"version":"'$NEW_ENV'"}}}'

# 5. Verify switch
sleep 10
curl -f http://localhost:8000/health || {
    echo "❌ Traffic switch failed, reverting..."
    kubectl patch service revoagent-api -p '{"spec":{"selector":{"version":"'$CURRENT_ENV'"}}}'
    exit 1
}

echo "✅ Blue-Green deployment completed!"
```

---

## 🔧 Maintenance Procedures

### Weekly Maintenance (Sundays 2:00 AM)

```bash
#!/bin/bash
# Weekly maintenance script

echo "🔧 reVoAgent Weekly Maintenance - $(date)"
echo "=========================================="

# 1. Full system backup
echo "💾 Creating full system backup..."
tar -czf /backup/full_backup_$(date +%Y%m%d).tar.gz \
    /app/data \
    /app/config \
    /var/log/revoagent

# 2. Database maintenance
echo "🗄️ Database maintenance..."
docker exec postgres psql -U revoagent -d revoagent_prod -c "VACUUM ANALYZE;"
docker exec postgres psql -U revoagent -d revoagent_prod -c "REINDEX DATABASE revoagent_prod;"

# 3. Update AI models
echo "🤖 Checking for model updates..."
python /app/scripts/update_models.py

# 4. Security scan
echo "🔒 Running security scan..."
docker run --rm -v /app:/app aquasec/trivy fs /app

# 5. Performance optimization
echo "⚡ Performance optimization..."
python /app/performance/weekly_optimization.py

# 6. Clean old backups (keep 30 days)
echo "🧹 Cleaning old backups..."
find /backup -name "*.tar.gz" -mtime +30 -delete
find /backup -name "*.sql" -mtime +30 -delete

echo "✅ Weekly maintenance completed!"
```

### Monthly Maintenance (First Sunday 1:00 AM)

```bash
#!/bin/bash
# Monthly maintenance script

echo "📅 reVoAgent Monthly Maintenance - $(date)"
echo "==========================================="

# 1. Security updates
echo "🔒 Applying security updates..."
apt update && apt upgrade -y

# 2. Certificate renewal
echo "🔐 Renewing SSL certificates..."
certbot renew --nginx

# 3. Dependency updates
echo "📦 Updating dependencies..."
pip install --upgrade -r requirements.txt

# 4. Performance review
echo "📊 Generating performance report..."
python /app/scripts/monthly_performance_report.py

# 5. Capacity planning
echo "📈 Capacity planning analysis..."
python /app/scripts/capacity_planning.py

# 6. Disaster recovery test
echo "🚨 Testing disaster recovery..."
python /app/scripts/dr_test.py

echo "✅ Monthly maintenance completed!"
```

---

## 🚨 Incident Response

### Incident Classification

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| P0 | Complete service outage | 15 minutes | Immediate |
| P1 | Major functionality impaired | 1 hour | Team Lead |
| P2 | Minor functionality impaired | 4 hours | Support Team |
| P3 | Cosmetic issues | 24 hours | Next sprint |

### Incident Response Workflow

```bash
#!/bin/bash
# Incident response script

SEVERITY=$1
DESCRIPTION="$2"

echo "🚨 INCIDENT RESPONSE ACTIVATED"
echo "Severity: $SEVERITY"
echo "Description: $DESCRIPTION"
echo "Time: $(date)"

case $SEVERITY in
    P0)
        echo "🔥 P0 CRITICAL INCIDENT"
        # 1. Page on-call
        curl -X POST https://api.pagerduty.com/incidents \
            -H "Authorization: Token token=$PD_TOKEN" \
            -d "{\"incident\": {\"type\": \"incident\", \"title\": \"P0: $DESCRIPTION\"}}"
        
        # 2. Create war room
        slack_notify "#incident-response" "🚨 P0 INCIDENT: $DESCRIPTION - War room: #incident-$(date +%Y%m%d-%H%M)"
        
        # 3. Activate backup systems
        kubectl apply -f k8s/emergency-deployment.yaml
        ;;
        
    P1)
        echo "⚠️ P1 HIGH SEVERITY"
        # 1. Notify team lead
        slack_notify "#alerts" "⚠️ P1 INCIDENT: $DESCRIPTION"
        
        # 2. Scale resources
        kubectl scale deployment revoagent-api --replicas=5
        ;;
        
    P2|P3)
        echo "ℹ️ P$SEVERITY INCIDENT"
        # Create ticket
        curl -X POST https://api.jira.com/rest/api/2/issue \
            -H "Content-Type: application/json" \
            -d "{\"fields\": {\"project\": {\"key\": \"REVO\"}, \"summary\": \"$DESCRIPTION\", \"issuetype\": {\"name\": \"Bug\"}}}"
        ;;
esac

echo "✅ Incident response initiated"
```

---

## 📈 Performance Optimization

### Daily Performance Check

```bash
#!/bin/bash
# Daily performance optimization

echo "⚡ Daily Performance Check - $(date)"
echo "===================================="

# 1. Check response times
echo "📊 API Response Times:"
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health

# 2. Check local model usage
echo "🤖 Local Model Usage:"
LOCAL_USAGE=$(curl -s http://localhost:8000/api/v1/metrics/cost | jq -r '.local_usage_percentage')
echo "Local usage: $LOCAL_USAGE%"

if (( $(echo "$LOCAL_USAGE < 90" | bc -l) )); then
    echo "⚠️ Local usage below 90%, optimizing routing..."
    python /app/scripts/optimize_model_routing.py
fi

# 3. Check cache hit rates
echo "💾 Cache Performance:"
CACHE_HIT_RATE=$(redis-cli info stats | grep keyspace_hits | cut -d: -f2)
echo "Cache hit rate: $CACHE_HIT_RATE"

# 4. Database performance
echo "🗄️ Database Performance:"
docker exec postgres psql -U revoagent -d revoagent_prod -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE mean_time > 1000 
ORDER BY mean_time DESC LIMIT 5;"

echo "✅ Performance check completed"
```

---

## 🔐 Security Operations

### Daily Security Check

```bash
#!/bin/bash
# Daily security check

echo "🔒 Daily Security Check - $(date)"
echo "=================================="

# 1. Check for failed login attempts
echo "🚨 Failed Login Attempts (Last 24h):"
docker logs revoagent-api --since 24h | grep -i "authentication failed" | wc -l

# 2. Check SSL certificate status
echo "🔐 SSL Certificate Status:"
openssl x509 -in /etc/ssl/certs/revoagent.crt -noout -dates

# 3. Check for security updates
echo "🛡️ Security Updates Available:"
apt list --upgradable | grep -i security | wc -l

# 4. Scan for vulnerabilities
echo "🔍 Vulnerability Scan:"
docker run --rm -v /app:/app aquasec/trivy fs /app --severity HIGH,CRITICAL

# 5. Check firewall status
echo "🔥 Firewall Status:"
ufw status

echo "✅ Security check completed"
```

---

## 📞 Contact Information

### On-Call Rotation

| Week | Primary | Secondary | Backup |
|------|---------|-----------|--------|
| Week 1 | Alice (+1-555-0101) | Bob (+1-555-0102) | Charlie (+1-555-0103) |
| Week 2 | Bob (+1-555-0102) | Charlie (+1-555-0103) | Alice (+1-555-0101) |
| Week 3 | Charlie (+1-555-0103) | Alice (+1-555-0101) | Bob (+1-555-0102) |

### Escalation Contacts

- **CTO**: cto@revoagent.com (+1-555-CTO1)
- **Security Lead**: security-lead@revoagent.com (+1-555-SEC1)
- **Infrastructure Lead**: infra-lead@revoagent.com (+1-555-INF1)

---

**Last Updated**: June 11, 2025  
**Next Review**: July 11, 2025