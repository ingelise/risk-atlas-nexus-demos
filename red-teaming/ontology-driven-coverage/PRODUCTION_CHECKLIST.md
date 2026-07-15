# Production Readiness Checklist

Before deploying the red-team planning agent to production, verify the following:

## Critical (Must Complete)

- [ ] **Real Ontology Loaded**
  - [ ] `ai_atlas_nexus` library is installed: `pip install ai-atlas-nexus>=1.1.0`
  - [ ] Ontology loads without errors on server startup
  - [ ] Test query: `nexus.get_all_risks()` returns risks (should be 40+)
  - [ ] Confirm taxonomy: `get_all_risks(taxonomy="ibm-ai-risk-atlas")` works

- [ ] **Persistent Storage**
  - [ ] Coverage state backed by database (not in-memory `COVERAGE` dict)
  - [ ] Database connection tested and working
  - [ ] Migrations run successfully
  - [ ] Verify coverage survives server restart

- [ ] **Authentication & Authorization**
  - [ ] MCP server requires API key or OAuth token
  - [ ] Invalid tokens are rejected
  - [ ] RBAC configured (who can read/write coverage?)
  - [ ] No unauthenticated access from untrusted networks

- [ ] **Input Validation**
  - [ ] Objectives validated (not empty, < 500 chars)
  - [ ] Risk IDs validated against known risks
  - [ ] Owner enum strictly checked (no free-form input)
  - [ ] Reject objectives containing obvious payload patterns (e.g., `rm -rf`, jailbreak keywords)

- [ ] **Error Handling & Logging**
  - [ ] All tool calls logged with timestamp and actor
  - [ ] Exceptions caught and logged (not thrown to client)
  - [ ] Failed queries return meaningful error messages
  - [ ] Ontology connection failures detected and reported

- [ ] **Testing**
  - [ ] Unit tests for all 4 tools pass
  - [ ] Integration test: end-to-end planning session works
  - [ ] Test with invalid inputs (bad risk IDs, empty objectives)
  - [ ] Test database unavailability handling

## High Priority (Must Have for General Release)

- [ ] **Ticketing Integration**
  - [ ] When `owner="human_redteam"`, ticket is filed automatically
  - [ ] Ticket includes risk ID, objective, and link back to coverage
  - [ ] Ticket status syncs back to coverage state
  - [ ] Stale tickets (> 30 days open, no progress) flagged in reports

- [ ] **Benchmark Integration**
  - [ ] `linked_benchmarks` field populated from ontology
  - [ ] If a benchmark exists, auto-run it and mark test as passed/failed
  - [ ] Coverage report shows: "automated: 3/5 passed, 2/5 needs review"
  - [ ] Failed benchmarks bubble up as high-priority gaps

- [ ] **Multi-System Scoping**
  - [ ] Add `system_id` parameter to all tools
  - [ ] Coverage is keyed by (system_id, risk_id)
  - [ ] Coverage report shows: "System A: 75%, System B: 50%, gaps by category"
  - [ ] Query coverage across multiple systems

- [ ] **Governance Reporting**
  - [ ] Pre-built compliance report template
  - [ ] Export coverage snapshot as JSON/CSV/PDF
  - [ ] Coverage trends over time (graph)
  - [ ] Risk heatmap: which categories are systematically undertested?

- [ ] **Operational Tools**
  - [ ] `clear_coverage(system_id)` — reset for re-planning
  - [ ] `export_coverage(system_id, format)` — export snapshot
  - [ ] `bulk_log_objectives(system_id, objectives)` — batch import
  - [ ] Health check endpoint (`/health`) for monitoring

- [ ] **Deployment & Ops**
  - [ ] Docker image created and tested
  - [ ] Kubernetes manifests (if applicable)
  - [ ] Health checks and liveness probes configured
  - [ ] Monitoring alerts set up (server down, DB unavailable, high error rate)
  - [ ] Runbooks documented (e.g., "Ontology is out of date", "Coverage DB is full")

## Medium Priority (Nice to Have)

- [ ] **Performance Optimization**
  - [ ] Connection pooling for database
  - [ ] Cache frequently-accessed risks (LRU cache)
  - [ ] Pagination for large coverage reports
  - [ ] Query optimization for multi-system reports
  - [ ] Response time < 1s for all tools (p95)

- [ ] **Advanced Features**
  - [ ] ML-based risk scoping (use BenchmarkRiskDetector instead of keyword matching)
  - [ ] Incident linking (map production bugs to risk nodes)
  - [ ] Control effectiveness scoring (which mitigations reduce risk most?)
  - [ ] Multi-taxonomy support (OWASP, NIST, custom)

- [ ] **Documentation & Training**
  - [ ] API reference (tools, parameters, examples)
  - [ ] Integration guide for clients (Claude Code, custom scripts)
  - [ ] Troubleshooting guide (common errors)
  - [ ] Video walkthrough for security team

- [ ] **Data Privacy & Compliance**
  - [ ] Data retention policy (when to purge old coverage records)
  - [ ] PII sanitization (objectives might mention real systems/users)
  - [ ] Encryption at rest (if coverage data is sensitive)
  - [ ] Audit trail immutable (all changes logged with timestamp, actor, reason)

## Quality Gates

Before declaring "production ready", ensure:

1. **Correctness**: 
   - Agent produces test objectives that red-teamers recognize as useful
   - Coverage reports match expected results (no blindspots)
   - Risk scoping doesn't miss applicable categories

2. **Reliability**:
   - Server up-time > 99.5% (targets)
   - All queries complete within SLA (< 2s)
   - No data loss on crashes (durable coverage state)

3. **Security**:
   - No unauthenticated access
   - Objectives can't be used to inject payloads
   - Coverage data access controlled (no cross-team leakage)

4. **Usability**:
   - Red-teamers report time savings vs. manual planning
   - Coverage reports generate no false positives (gap list is actionable)
   - Integration with ticketing system reduces manual work

## Rollout Plan

### Phase 1: Internal Testing (Week 1-2)
- [ ] Deploy to staging environment
- [ ] Security team tests planning for 3-5 systems
- [ ] Collect feedback on objectives and coverage
- [ ] Verify ticketing integration works

### Phase 2: Beta (Week 3-4)
- [ ] Deploy to production (read-only access, no coverage writes)
- [ ] Monitor error rates and response times
- [ ] Red-teamers query coverage reports, give feedback
- [ ] Fix any issues discovered

### Phase 3: General Release (Week 5+)
- [ ] Enable read-write access
- [ ] Full monitoring and alerting active
- [ ] Runbooks ready for ops
- [ ] Documentation complete

## Monitoring & Alerts

Once in production, monitor:

| Metric | Threshold | Action |
|--------|-----------|--------|
| Server uptime | < 99% | Page oncall |
| Query latency p95 | > 2s | Investigate DB/CPU |
| Error rate | > 1% | Check logs |
| Coverage DB size | > 100GB | Archive old snapshots |
| Human red-team SLA | Tickets > 30 days | Escalate |

## Incident Response

If something goes wrong:

1. **Server down**:
   - Check MCP server logs
   - Verify database connectivity
   - Restart server
   - If persists, rollback to previous version

2. **Coverage data corrupted**:
   - Stop all write operations
   - Restore from last known-good backup
   - Audit what went wrong

3. **Ontology out of date**:
   - Upgrade `ai_atlas_nexus` library
   - Re-run risk scoping for all systems
   - Compare new coverage to old (should mostly overlap)
   - Flag any new high-priority gaps

## Success Metrics

You know this is production-ready when:

- Red-teamers can plan coverage for a new system in < 15 minutes
- Coverage reports match what they'd expect by hand (no missed categories)
- Integration with ticketing system eliminates manual task filing
- Security stakeholders can query "which systems have gaps in fairness risks?" and get an answer
- Incident response is faster because risk nodes point to known mitigations
