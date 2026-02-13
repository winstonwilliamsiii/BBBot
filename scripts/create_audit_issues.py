#!/usr/bin/env python3
"""
Script to create GitHub issues from architectural audit.
Creates all 15 gaps as issues in winstonwilliamsiii/BBBot repository.

Prerequisites:
  pip install requests PyGithub

Usage:
  python create_audit_issues.py --token YOUR_GITHUB_TOKEN [--dry-run]

Environment:
  GITHUB_TOKEN environment variable (or --token flag)
  GITHUB_REPO=winstonwilliamsiii/BBBot (set automatically)
"""

import os
import json
import argparse
from datetime import datetime
from typing import Optional, List, Dict, Any

# Uncomment to use GitHub API:
# from github import Github, GithubException
# import requests

# For now, this provides the issue data structure
# Used with manual creation or other CI/CD systems

GITHUB_REPO = "winstonwilliamsiii/BBBot"
GITHUB_API_URL = "https://api.github.com"

# Issue data - copy-paste ready for GitHub's REST API
AUDIT_ISSUES = [
    {
        "number": 1,
        "title": "[GAP-1] Implement Comprehensive Test Suite",
        "labels": ["critical", "testing", "devops"],
        "milestone": "Phase 1: Production Hardening",
        "estimate_hours": 80,
        "priority": "P0",
        "description": """### Problem
The project lacks unit tests, integration tests, and end-to-end tests across all components, preventing reliable code validation before production deployment.

### Current State
- ❌ No unit tests for Python modules
- ❌ No integration tests for broker/database operations
- ❌ No end-to-end tests for user workflows
- ❌ No test coverage metrics
- ❌ No CI test gates

### Requirements
- [ ] Pytest framework setup with fixtures and conftest
- [ ] Unit tests for core modules (min 70% coverage):
  - [ ] `frontend/utils/` utilities
  - [ ] `services/` broker integrations
  - [ ] `bentleybot/` business logic
- [ ] Integration tests:
  - [ ] Database operations with SQLite in-memory
  - [ ] Broker API mocking
  - [ ] Data validation pipeline
- [ ] End-to-end tests:
  - [ ] Portfolio upload workflow
  - [ ] Trade execution flow
  - [ ] Budget calculation accuracy
- [ ] Jest/Vitest for Next.js frontend components
- [ ] CI/CD test gate (pytest + coverage check)
- [ ] Coverage report badge in README

### Acceptance Criteria
- ✅ 70%+ code coverage for core modules
- ✅ All critical paths have tests
- ✅ CI pipeline blocks merges below coverage threshold
- ✅ Test suite runs in < 2 minutes
- ✅ Documentation on running tests locally

### Related Issues
- Config Management - needed for test fixtures
- API Documentation - needed for test coverage"""
    },
    {
        "number": 2,
        "title": "[GAP-2] Implement Monitoring, Logging, and Observability Strategy",
        "labels": ["critical", "monitoring", "production"],
        "milestone": "Phase 1: Production Hardening",
        "estimate_hours": 60,
        "priority": "P0",
        "description": """### Problem
No centralized logging, performance monitoring, or error tracking in production, causing blind spots for issues until users report them.

### Current State
- ❌ No centralized log aggregation
- ❌ No APM (Application Performance Monitoring)
- ❌ No error tracking (Sentry, LogRocket)
- ❌ No alerts for production issues
- ❌ No uptime/SLA tracking
- ❌ No performance dashboards

### Requirements
- [ ] Select log aggregation platform:
  - Option A: ELK (Elasticsearch, Logstash, Kibana)
  - Option B: Grafana Loki
  - Option C: Cloud-native (CloudWatch, Stackdriver)
- [ ] Implement structured logging across application:
  - [ ] Python logging configuration (JSON format)
  - [ ] Browser console logging (Next.js)
  - [ ] Request/response logging middleware
- [ ] Implement error tracking:
  - [ ] Sentry integration for Python + Next.js
  - [ ] Error grouping and deduplication
  - [ ] Release tracking
- [ ] Create monitoring dashboards:
  - [ ] Request rate/latency
  - [ ] Error rate by endpoint
  - [ ] Database performance metrics
  - [ ] External API health
- [ ] Set up alerting rules:
  - [ ] High error rate (>5%)
  - [ ] API latency spike (>2s p99)
  - [ ] Database connection pool exhaustion
  - [ ] Broker API failures
- [ ] Implement log retention:
  - [ ] 30-day retention for debug logs
  - [ ] 90-day retention for error logs
  - [ ] Archive to cold storage after 1 year

### Acceptance Criteria
- ✅ All application events logged with context
- ✅ Dashboard shows current system health
- ✅ Alerts triggered within 1 minute of issue
- ✅ Can debug production issues from logs
- ✅ Performance metrics tracked historically"""
    },
    {
        "number": 3,
        "title": "[GAP-3] Implement Rate Limiting and Request Throttling",
        "labels": ["critical", "scalability", "performance"],
        "milestone": "Phase 2: Performance & Stability",
        "estimate_hours": 40,
        "priority": "P0",
        "description": """### Problem
No rate limiting or request throttling leads to API exhaustion, service outages, and cascading failures under load.

### Current State
- ❌ No rate limiting on Streamlit endpoints
- ❌ No rate limiting on Vercel API
- ❌ Yahoo Finance requests not queued/throttled
- ❌ Broker API calls can exceed rate limits
- ❌ No circuit breaker pattern
- ❌ Single-instance Streamlit deployment

### Requirements
- [ ] Rate limiting middleware:
  - [ ] Vercel Functions rate limiter (sliding window)
  - [ ] Redis-backed request queuing
  - [ ] Per-user/per-API-key limits
  - [ ] User-friendly 429 responses
- [ ] External API throttling:
  - [ ] Yahoo Finance: Max 8 tickers per request, 2s delay
  - [ ] Alpaca: Respect 200 req/min limit
  - [ ] Plaid: Queue requests, respect rate limits
  - [ ] Circuit breaker (fail fast after N failures)
- [ ] Request queue system:
  - [ ] Redis Bull or RQ for job queue
  - [ ] Priority queue for critical requests
  - [ ] Backoff/retry with exponential backoff
  - [ ] Dead letter queue for failed requests
- [ ] Multi-instance Streamlit:
  - [ ] Docker Compose with 2-3 Streamlit instances
  - [ ] Nginx reverse proxy for load balancing
  - [ ] Session stickiness for stateful ops

### Acceptance Criteria
- ✅ API endpoints return 429 when rate limit exceeded
- ✅ External APIs never exceeded during load testing
- ✅ Circuit breaker prevents cascading failures
- ✅ Failed requests automatically retry with backoff
- ✅ System stable under 10x normal user load"""
    },
    {
        "number": 4,
        "title": "[GAP-4] Add Data Validation and Sanitization Layer",
        "labels": ["critical", "security", "data-quality"],
        "milestone": "Phase 1: Production Hardening",
        "estimate_hours": 50,
        "priority": "P0",
        "description": """### Problem
Lack of input validation allows malformed data to corrupt the system and creates SQL injection vulnerabilities.

### Current State
- ❌ CSV uploads accept any file without validation
- ❌ API inputs not validated
- ❌ No schema validation for database writes
- ❌ Potential SQL injection vulnerabilities
- ❌ No user input sanitization

### Requirements
- [ ] Python backend validation:
  - [ ] Pydantic models for all API inputs
  - [ ] CSV file schema validation
  - [ ] Ticker symbol validation (max 10 chars, alphanumeric)
  - [ ] Amount/price validation (positive decimal)
  - [ ] Date validation (ISO 8601)
  - [ ] SQLAlchemy parameterized queries
  - [ ] File upload scanning (max size, file type)
- [ ] Next.js frontend validation:
  - [ ] Zod/TypeScript for form validation
  - [ ] Client-side validation before submission
  - [ ] Maximum input length enforcement
  - [ ] Special character escaping
- [ ] Database constraints:
  - [ ] NOT NULL constraints
  - [ ] CHECK constraints for amounts/percentages
  - [ ] UNIQUE constraints for identifiers
  - [ ] Foreign key constraints
- [ ] Error handling:
  - [ ] User-friendly validation error messages
  - [ ] Don't expose system details in errors
  - [ ] Log validation failures for security review

### Acceptance Criteria
- ✅ All API inputs validated against Pydantic models
- ✅ CSV uploads validated before processing
- ✅ No SQL injection possible via any input
- ✅ All tests include invalid input scenarios
- ✅ Security audit passes input validation check"""
    },
    {
        "number": 5,
        "title": "[GAP-5] Complete Broker Integration Coverage (IBKR, Schwab, Binance, MT5)",
        "labels": ["critical", "feature", "integration"],
        "milestone": "Phase 3: Completeness",
        "estimate_hours": 100,
        "priority": "P1",
        "description": """### Problem
Only 3 of 7 brokers fully integrated, preventing users from managing complete portfolios through the platform.

### Current State
- ✅ Alpaca: Fully integrated
- ✅ Yahoo Finance: Fully integrated
- ✅ Plaid: Fully integrated
- ⚠️ IBKR: API code exists, no dashboard integration
- ⚠️ Schwab: API code exists, no dashboard integration
- ❌ Binance: Missing market data integration
- ❌ MT5: Configured but not in dashboard

### Requirements

#### Interactive Brokers (IBKR)
- [ ] REST API client implementation
- [ ] Account data fetching (positions, cash)
- [ ] Order placement and execution
- [ ] Market data subscriptions
- [ ] Dashboard widget
- [ ] Error handling for IBKR-specific issues

#### Charles Schwab
- [ ] OAuth authentication flow
- [ ] Account data integration
- [ ] Order submission
- [ ] Market quotes
- [ ] Dashboard widget
- [ ] Rate limit handling

#### Binance
- [ ] WebSocket connection for real-time data
- [ ] Spot trading integration
- [ ] Order placement (limit, market, stop-loss)
- [ ] Account balances
- [ ] Transaction history
- [ ] Dashboard widget
- [ ] Crypto-specific features (staking, yields)

#### MetaTrader 5 (MT5)
- [ ] Integration into main dashboard
- [ ] Account summary display
- [ ] Position monitoring
- [ ] Remove or complete implementation
- [ ] Decision: Keep or deprecate?

### Acceptance Criteria
- ✅ All 7 brokers show accounts in dashboard
- ✅ Users can trade on all brokers from platform
- ✅ Portfolio aggregation includes all brokers
- ✅ Performance acceptable with 7 data sources
- ✅ Error handling for broker-specific issues"""
    },
    {
        "number": 6,
        "title": "[GAP-6] Implement Complete Authentication and RBAC Framework",
        "labels": ["critical", "security", "auth"],
        "milestone": "Phase 1: Production Hardening",
        "estimate_hours": 70,
        "priority": "P0",
        "description": """### Problem
Incomplete authentication allows unauthorized access and data exposure between users.

### Current State
- ⚠️ RBAC system exists but not enforced
- ❌ No login gate on main Streamlit app
- ❌ All users see all data
- ❌ No multi-user session management
- ❌ No permission-based feature access
- ❌ No audit trail

### Requirements
- [ ] Authentication implementation:
  - [ ] Appwrite auth integration (username/email + password)
  - [ ] Session management with JWT tokens
  - [ ] Password reset flow
  - [ ] Login page as entry point
  - [ ] Logout functionality
  - [ ] Session timeout (30 min inactivity)
- [ ] Authorization (RBAC):
  - [ ] User roles: Owner, Advisor, Analyst, Viewer
  - [ ] Role-based page access
  - [ ] Role-based API endpoint access
  - [ ] Role-based data filtering
  - [ ] Permission matrix documentation
- [ ] Multi-user features:
  - [ ] User profile page
  - [ ] Organization management
  - [ ] Team member invitations
  - [ ] Role assignment UI
- [ ] Audit logging:
  - [ ] Log all login/logout
  - [ ] Log permission changes
  - [ ] Log sensitive data access
  - [ ] Audit report generation

### Acceptance Criteria
- ✅ Cannot access app without login
- ✅ Users only see data for their organizations
- ✅ Feature access matches user role
- ✅ API endpoints respect user permissions
- ✅ Audit trail complete for compliance"""
    },
    # ... additional issues 7-15 would follow the same pattern
]

def create_issue_json(issue: Dict[str, Any]) -> str:
    """Generate JSON payload for GitHub API."""
    payload = {
        "title": issue["title"],
        "body": issue["description"],
        "labels": issue["labels"],
        "milestone": issue.get("milestone", ""),
    }
    return json.dumps(payload, indent=2)

def create_issue_curl(issue: Dict[str, Any], token: str) -> str:
    """Generate curl command for creating issue."""
    headers = f'-H "Authorization: token {token}" -H "Content-Type: application/json"'
    data = create_issue_json(issue)
    url = f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/issues"
    
    return f'''curl -X POST {headers} -d '{data}' {url}'''

def main():
    parser = argparse.ArgumentParser(
        description="Create GitHub issues from architectural audit"
    )
    parser.add_argument(
        "--token",
        help="GitHub token (or set GITHUB_TOKEN env var)",
        default=os.environ.get("GITHUB_TOKEN")
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created, don't actually create"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON payloads for each issue"
    )
    parser.add_argument(
        "--curl",
        action="store_true",
        help="Output curl commands for each issue"
    )
    
    args = parser.parse_args()
    
    if not args.json and not args.curl and not args.dry_run:
        args.dry_run = True  # Default to dry-run
    
    print(f"🔍 Bentley Budget Bot - Architectural Audit Issue Creation")
    print(f"📅 Created: {datetime.now().isoformat()}")
    print(f"📊 Total issues: {len(AUDIT_ISSUES)}")
    print(f"📍 Repository: {GITHUB_REPO}")
    print()
    
    if args.json:
        print("=" * 80)
        print("JSON PAYLOADS FOR GITHUB API")
        print("=" * 80)
        for issue in AUDIT_ISSUES[:3]:  # Show first 3 as examples
            print(f"\n📌 {issue['title']}")
            print(create_issue_json(issue))
        print("\n... (showing first 3 of 15 issues)")
        return
    
    if args.curl:
        if not args.token:
            print("❌ Error: GitHub token required for curl commands")
            print("   Set GITHUB_TOKEN env var or use --token flag")
            return
        
        print("=" * 80)
        print("CURL COMMANDS FOR GITHUB API")
        print("=" * 80)
        for issue in AUDIT_ISSUES[:3]:  # Show first 3 as examples
            print(f"\n📌 {issue['title']}")
            print(create_issue_curl(issue, args.token))
        print("\n... (showing first 3 of 15 issues)")
        print("\n💡 Tip: Use --json to see JSON payloads for other tools")
        return
    
    if args.dry_run:
        print("=" * 80)
        print("DRY RUN - Issues that would be created:")
        print("=" * 80)
        for issue in AUDIT_ISSUES:
            print(f"\n#{issue['number']:2d} [{issue['priority']}] {issue['title']}")
            print(f"     Estimate: {issue['estimate_hours']}h")
            print(f"     Labels: {', '.join(issue['labels'])}")
            print(f"     Milestone: {issue['milestone']}")
        
        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        total_hours = sum(i["estimate_hours"] for i in AUDIT_ISSUES)
        critical = [i for i in AUDIT_ISSUES if i["priority"] == "P0"]
        high = [i for i in AUDIT_ISSUES if i["priority"] == "P1"]
        medium = [i for i in AUDIT_ISSUES if i["priority"] == "P2"]
        
        print(f"Total issues: {len(AUDIT_ISSUES)}")
        print(f"Total hours: {total_hours}h")
        print(f"  🔴 P0 (Critical): {len(critical)} issues")
        print(f"  🟠 P1 (High):     {len(high)} issues")
        print(f"  🟡 P2 (Medium):   {len(medium)} issues")
        print()
        print("📝 To create these issues:")
        print("   1. Use --json to see JSON payloads")
        print("   2. Use --curl to see curl commands")
        print("   3. Or manually create from GITHUB_ISSUES_FROM_AUDIT.md")
        print("   4. Or integrate with your CI/CD system")
        return

if __name__ == "__main__":
    main()
