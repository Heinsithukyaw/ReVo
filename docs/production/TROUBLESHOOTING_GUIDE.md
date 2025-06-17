# 🔧 reVoAgent Production Troubleshooting Guide

**Version**: 1.0  
**Date**: June 11, 2025  
**Target**: Production Operations Team

---

## 📋 Table of Contents

1. [Common Issues](#common-issues)
2. [Performance Issues](#performance-issues)
3. [Security Issues](#security-issues)
4. [Monitoring & Alerting](#monitoring--alerting)
5. [Database Issues](#database-issues)
6. [Container & Kubernetes Issues](#container--kubernetes-issues)
7. [AI Model Issues](#ai-model-issues)
8. [Network & Connectivity](#network--connectivity)
9. [Emergency Procedures](#emergency-procedures)

---

## 🚨 Common Issues

### Issue: API Server Not Responding

**Symptoms**:
- HTTP 500/502/503 errors
- Timeout errors
- Connection refused

**Diagnosis**:
```bash
# Check container status
docker ps | grep revoagent-api

# Check logs
docker logs revoagent-api --tail 100

# Check health endpoint
curl -f http://localhost:8000/health
```

**Solutions**:
1. **Restart API server**:
   ```bash
   docker-compose restart revoagent-api
   ```

2. **Check resource usage**:
   ```bash
   docker stats revoagent-api
   ```

3. **Scale horizontally** (Kubernetes):
   ```bash
   kubectl scale deployment revoagent-api --replicas=3
   ```

### Issue: High Memory Usage

**Symptoms**:
- OOMKilled containers
- Slow response times
- Memory alerts firing

**Diagnosis**:
```bash
# Check memory usage
free -h
docker stats --no-stream

# Check for memory leaks
ps aux --sort=-%mem | head -10
```

**Solutions**:
1. **Increase memory limits**:
   ```yaml
   # docker-compose.yml
   services:
     revoagent-api:
       deploy:
         resources:
           limits:
             memory: 4G
   ```

2. **Enable garbage collection**:
   ```bash
   # Add to environment variables
   PYTHONOPTIMIZE=1
   MALLOC_TRIM_THRESHOLD_=100000
   ```

---

## ⚡ Performance Issues

### Issue: Slow API Response Times

**Symptoms**:
- Response times > 2 seconds
- High latency alerts
- User complaints

**Diagnosis**:
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health

# Monitor with ab
ab -n 100 -c 10 http://localhost:8000/api/v1/health
```

**Solutions**:
1. **Enable caching**:
   ```python
   # Add Redis caching
   CACHE_TTL = 300  # 5 minutes
   REDIS_URL = "redis://redis:6379/0"
   ```

2. **Optimize database queries**:
   ```sql
   -- Add indexes
   CREATE INDEX idx_user_id ON requests(user_id);
   CREATE INDEX idx_created_at ON requests(created_at);
   ```

3. **Enable connection pooling**:
   ```python
   # Database connection pool
   DATABASE_POOL_SIZE = 20
   DATABASE_MAX_OVERFLOW = 30
   ```

### Issue: High CPU Usage

**Symptoms**:
- CPU usage > 80%
- Slow processing
- CPU alerts firing

**Solutions**:
1. **Optimize AI model usage**:
   ```python
   # Use local models first
   MODEL_PRIORITY = ["deepseek-r1", "llama-3.1", "gpt-4"]
   LOCAL_MODEL_THRESHOLD = 0.95
   ```

2. **Enable async processing**:
   ```python
   # Use async/await for I/O operations
   import asyncio
   import aiohttp
   ```

---

## 🔒 Security Issues

### Issue: Authentication Failures

**Symptoms**:
- 401 Unauthorized errors
- JWT token errors
- Login failures

**Diagnosis**:
```bash
# Check JWT configuration
grep -r "JWT_SECRET" /app/config/

# Verify token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/user/profile
```

**Solutions**:
1. **Regenerate JWT secret**:
   ```bash
   # Generate new secret
   openssl rand -hex 32
   
   # Update configuration
   JWT_SECRET_KEY="new_secret_here"
   ```

2. **Check token expiration**:
   ```python
   # Increase token lifetime
   JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
   ```

### Issue: SSL/TLS Certificate Problems

**Symptoms**:
- Certificate expired warnings
- SSL handshake failures
- Browser security warnings

**Solutions**:
1. **Renew certificates**:
   ```bash
   # Let's Encrypt renewal
   certbot renew --nginx
   
   # Restart nginx
   systemctl reload nginx
   ```

2. **Check certificate validity**:
   ```bash
   openssl x509 -in /etc/ssl/certs/revoagent.crt -text -noout
   ```

---

## 📊 Monitoring & Alerting

### Issue: Prometheus Not Scraping Metrics

**Symptoms**:
- Missing metrics in Grafana
- Prometheus targets down
- No data in dashboards

**Diagnosis**:
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check service discovery
curl http://localhost:9090/api/v1/label/__name__/values
```

**Solutions**:
1. **Fix service discovery**:
   ```yaml
   # prometheus.yml
   scrape_configs:
     - job_name: 'revoagent-api'
       static_configs:
         - targets: ['revoagent-api:8000']
       metrics_path: '/metrics'
   ```

2. **Restart monitoring stack**:
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart
   ```

### Issue: Grafana Dashboard Not Loading

**Solutions**:
1. **Check datasource connection**:
   ```bash
   # Test Prometheus connection
   curl http://grafana:3000/api/datasources/proxy/1/api/v1/query?query=up
   ```

2. **Reimport dashboards**:
   ```bash
   # Copy dashboard files
   cp monitoring/grafana/dashboards/*.json /var/lib/grafana/dashboards/
   ```

---

## 🗄️ Database Issues

### Issue: Database Connection Failures

**Symptoms**:
- Connection timeout errors
- Database unavailable
- Connection pool exhausted

**Solutions**:
1. **Check database status**:
   ```bash
   # PostgreSQL
   docker exec -it postgres psql -U revoagent -c "SELECT version();"
   
   # Redis
   docker exec -it redis redis-cli ping
   ```

2. **Increase connection limits**:
   ```sql
   -- PostgreSQL
   ALTER SYSTEM SET max_connections = 200;
   SELECT pg_reload_conf();
   ```

### Issue: Database Performance Issues

**Solutions**:
1. **Analyze slow queries**:
   ```sql
   -- Enable slow query log
   ALTER SYSTEM SET log_min_duration_statement = 1000;
   
   -- Check slow queries
   SELECT query, mean_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC LIMIT 10;
   ```

2. **Optimize indexes**:
   ```sql
   -- Find missing indexes
   SELECT schemaname, tablename, attname, n_distinct, correlation 
   FROM pg_stats 
   WHERE schemaname = 'public' 
   ORDER BY n_distinct DESC;
   ```

---

## 🐳 Container & Kubernetes Issues

### Issue: Pod CrashLoopBackOff

**Symptoms**:
- Pods constantly restarting
- CrashLoopBackOff status
- Application not starting

**Diagnosis**:
```bash
# Check pod status
kubectl get pods -l app=revoagent

# Check pod logs
kubectl logs -f deployment/revoagent-api

# Describe pod for events
kubectl describe pod <pod-name>
```

**Solutions**:
1. **Fix resource limits**:
   ```yaml
   # deployment.yaml
   resources:
     requests:
       memory: "512Mi"
       cpu: "250m"
     limits:
       memory: "2Gi"
       cpu: "1000m"
   ```

2. **Fix health checks**:
   ```yaml
   livenessProbe:
     httpGet:
       path: /health
       port: 8000
     initialDelaySeconds: 30
     periodSeconds: 10
   ```

### Issue: Service Discovery Problems

**Solutions**:
1. **Check service endpoints**:
   ```bash
   kubectl get endpoints revoagent-api
   kubectl get svc revoagent-api
   ```

2. **Verify network policies**:
   ```bash
   kubectl get networkpolicies
   kubectl describe networkpolicy revoagent-network-policy
   ```

---

## 🤖 AI Model Issues

### Issue: Local Models Not Loading

**Symptoms**:
- Falling back to cloud models
- Model loading errors
- High cloud costs

**Diagnosis**:
```bash
# Check model files
ls -la /app/models/

# Check model loading logs
docker logs revoagent-api | grep -i "model"

# Test model endpoint
curl http://localhost:8000/api/v1/models/status
```

**Solutions**:
1. **Download missing models**:
   ```bash
   # Download DeepSeek R1
   wget -O /app/models/deepseek-r1.bin https://huggingface.co/deepseek-ai/deepseek-r1/resolve/main/model.bin
   ```

2. **Increase model timeout**:
   ```python
   MODEL_LOAD_TIMEOUT = 300  # 5 minutes
   MODEL_INFERENCE_TIMEOUT = 60  # 1 minute
   ```

### Issue: High Model Inference Latency

**Solutions**:
1. **Enable model caching**:
   ```python
   MODEL_CACHE_SIZE = 1000
   MODEL_CACHE_TTL = 3600  # 1 hour
   ```

2. **Use GPU acceleration**:
   ```yaml
   # docker-compose.yml
   services:
     revoagent-api:
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1
                 capabilities: [gpu]
   ```

---

## 🌐 Network & Connectivity

### Issue: External API Timeouts

**Solutions**:
1. **Increase timeout values**:
   ```python
   HTTP_TIMEOUT = 30
   API_RETRY_COUNT = 3
   API_RETRY_DELAY = 1
   ```

2. **Implement circuit breaker**:
   ```python
   from circuit_breaker import CircuitBreaker
   
   @CircuitBreaker(failure_threshold=5, recovery_timeout=30)
   def call_external_api():
       # API call logic
       pass
   ```

### Issue: Load Balancer Issues

**Solutions**:
1. **Check health checks**:
   ```bash
   # AWS ALB
   aws elbv2 describe-target-health --target-group-arn <arn>
   
   # NGINX
   curl http://localhost/nginx_status
   ```

2. **Update health check configuration**:
   ```yaml
   # ALB target group
   HealthCheckPath: /health
   HealthCheckIntervalSeconds: 30
   HealthyThresholdCount: 2
   UnhealthyThresholdCount: 5
   ```

---

## 🚨 Emergency Procedures

### Critical System Failure

**Immediate Actions**:
1. **Activate incident response**:
   ```bash
   # Page on-call engineer
   curl -X POST https://api.pagerduty.com/incidents \
     -H "Authorization: Token token=<token>" \
     -d '{"incident": {"type": "incident", "title": "reVoAgent Critical Failure"}}'
   ```

2. **Switch to backup systems**:
   ```bash
   # Failover to backup region
   kubectl config use-context backup-cluster
   kubectl apply -f k8s/emergency-deployment.yaml
   ```

3. **Enable maintenance mode**:
   ```bash
   # Update load balancer
   kubectl patch service revoagent-api -p '{"spec":{"selector":{"app":"maintenance"}}}'
   ```

### Data Recovery

**Backup Restoration**:
```bash
# Restore database from backup
pg_restore -h localhost -U revoagent -d revoagent_prod backup_20250611.sql

# Restore Redis data
redis-cli --rdb /backup/redis_backup.rdb

# Restore application data
rsync -av /backup/app_data/ /app/data/
```

### Security Incident

**Immediate Actions**:
1. **Isolate affected systems**:
   ```bash
   # Block suspicious IPs
   iptables -A INPUT -s <suspicious_ip> -j DROP
   
   # Disable compromised accounts
   kubectl delete secret user-<compromised_user>
   ```

2. **Rotate all secrets**:
   ```bash
   # Generate new secrets
   kubectl create secret generic app-secrets \
     --from-literal=jwt-secret=$(openssl rand -hex 32) \
     --from-literal=db-password=$(openssl rand -base64 32)
   ```

---

## 📞 Support Contacts

### Escalation Matrix

| Severity | Contact | Response Time |
|----------|---------|---------------|
| P0 - Critical | On-call Engineer | 15 minutes |
| P1 - High | Team Lead | 1 hour |
| P2 - Medium | Support Team | 4 hours |
| P3 - Low | Support Ticket | 24 hours |

### Emergency Contacts

- **On-call Engineer**: +1-555-ONCALL
- **Team Lead**: +1-555-TEAMLEAD  
- **Security Team**: security@revoagent.com
- **Infrastructure Team**: infra@revoagent.com

---

## 📚 Additional Resources

- [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Security Hardening Guide](../security/SECURITY_GUIDE.md)
- [Monitoring Setup Guide](../monitoring/MONITORING_GUIDE.md)
- [API Documentation](../api/API_REFERENCE.md)

---

**Last Updated**: June 11, 2025  
**Next Review**: July 11, 2025