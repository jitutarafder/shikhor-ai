# Shikhor AI — Production Operational Runbook & Incident Management Guide

> **Scope**: Operational readiness, monitoring, incident containment, rollback drills, and disaster recovery for Shikhor AI (Phase 10 — Hardening and Wider Release).
> Strictly adheres to [AGENTS.md](file:///d:/Shikhor%20AI/AGENTS.md) and [Security.md](file:///d:/Shikhor%20AI/Security.md).

---

## 1. System Architecture & Observability

### Health & Readiness Endpoints
- **Liveness Probe**: `GET /api/v1/health`
  - Returns: HTTP 200 `{ "status": "ok", "appName": "Shikhor AI", "environment": "production", "version": "0.1.0" }`
  - Frequency: Kubernetes liveness / Uptime monitor every 15 seconds.
- **Readiness Probe**: `GET /api/v1/health/readiness`
  - Validates:
    1. PostgreSQL / SQLite connectivity (`SELECT 1`).
    2. Private sanitized object storage connectivity.
    3. External provider circuit breaker states (Weather provider adapter, Crop AI inference adapter, OTP/SMS service).
  - Returns: HTTP 200 when ready, HTTP 503 Service Unavailable when DB is unreachable.

---

## 2. On-Call Triage & Incident Runbooks

### Incident Severity Levels

| Severity | Target Containment | Description |
| :--- | :--- | :--- |
| **SEV-1 (Critical)** | **< 1 hour** | System outage, credential leak, database compromise, or mass data corruption. |
| **SEV-2 (High)** | **< 4 hours** | Provider outage (Weather/AI failing), authentication degradation, active abuse flood. |
| **SEV-3 (Medium)** | **< 24 hours** | Non-critical UI regression, transient sync retry failure, localized listing glitch. |

---

### Runbook A: Credential / Secret Leakage
1. **Rotate Compromised Secret**:
   - Update the secret in production environment vault (`JWT_SECRET`, `AI_API_KEY`, etc.).
2. **Revoke Active Refresh Sessions**:
   - In SQL / Backend admin console, invalidate all active user sessions:
     ```sql
     UPDATE refresh_sessions SET is_revoked = TRUE WHERE is_revoked = FALSE;
     ```
3. **Redeploy API Services**:
   - Trigger rolling restart with updated environment variables.
4. **Audit Log Inspection**:
   - Review `/api/v1/admin/audit-logs` for any unauthorized actor activity during exposure window.

---

### Runbook B: Malicious Upload / Toxic Content
1. **Identify Content ID & Reporter**:
   - Query Moderation Reports queue via `/api/v1/admin/reports`.
2. **Execute Immediate Containment**:
   - Action: `hide_content` or `suspend_user`.
   - The backend service automatically revokes listing visibility and logs an immutable `AuditLog` entry.
3. **Purge Storage Derivative**:
   - Remove the derivative file from storage if content contains malicious payload.

---

### Runbook C: External Provider Failure (Weather or AI Adapter)
1. **Verify Circuit State**:
   - Check `GET /api/v1/health/readiness`.
2. **Automatic Graceful Fallbacks**:
   - **Weather Adapter**: If Open-Meteo or primary forecast fails/times out, backend serves cached 24h forecast and marks status `stale: true` (Rule 20).
   - **Crop AI Adapter**: If vision provider times out, returns `UNCERTAIN` state and escalates to official DAE agricultural helpline (16123).
3. **Quota Alerting**:
   - If rate quota exceeds 90%, switch to offline-reviewed advisory knowledge cache until quota reset.

---

## 3. Database Backup & Disaster Recovery Drill

### Daily Backup Execution
```bash
# PostgreSQL Production Backup
pg_dump -Fc --no-owner --clean shikhor_prod > /backup/shikhor_backup_$(date +%Y%m%d_%H%M%S).dump
```

### Point-in-Time Restore Verification Drill
1. Spin up isolated staging database container:
   ```bash
   createdb -h localhost shikhor_recovery_test
   ```
2. Restore from encrypted dump:
   ```bash
   pg_restore -d shikhor_recovery_test -c /backup/shikhor_backup_latest.dump
   ```
3. Validate schema integrity and record counts:
   ```bash
   psql -d shikhor_recovery_test -c "SELECT count(*) FROM users; SELECT count(*) FROM audit_logs;"
   ```
4. Confirm target Recovery Time Objective (RTO < 30 minutes) and Recovery Point Objective (RPO < 24 hours).

---

## 4. Rollback Procedures

### Backend Rollback
- If an Alembic migration introduces schema regressions:
  ```bash
  alembic downgrade -1
  ```
- Roll back container image tag to previous stable build.

### Frontend Rollback
- In Vite / CDN hosting, point traffic to previous immutable build bundle in storage bucket.

---

## 5. Escalation Contacts & Ownership Roster

| Role | Contact / Channel | Primary Responsibility |
| :--- | :--- | :--- |
| **National Agri Helpline** | **16123** | Official Bangladesh Agricultural Extension (DAE) Support |
| **Security Lead** | `security@shikhor.ai` | Vulnerability triage, credential rotation, incident lead |
| **Moderation Desk** | `moderation@shikhor.ai` | User report resolution, spam filtering, fraud prevention |
| **DevOps / On-Call** | `devops@shikhor.ai` | Uptime monitoring, database restore drills, CI/CD pipelines |
