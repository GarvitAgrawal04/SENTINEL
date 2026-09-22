# airbyte --- Open-source data integration platform
# D:\Repositories\airbyte\CLAUDE.md

## What This Is
Open-source data integration platform. ELT pipeline builder. 300+ source connectors (databases, APIs, SaaS). Incremental sync. Schema detection. Transformations via dbt. Docker-based. REST API. Self-hosted or Airbyte Cloud.

## When to Load This
- Data integration and ELT pipelines
- Database replication
- SaaS data extraction
- Data warehouse loading
- Incremental data sync
- Self-hosted Fivetran alternative

---

## CORE SETUP

```bash
git clone https://github.com/airbytehq/airbyte.git
cd airbyte
./run-ab-platform.sh
# Access at http://localhost:8000
```

## COMMANDS REFERENCE

| Command | Description |
|---|---|
| `./run-ab-platform.sh` | Start Airbyte |
| `docker compose down` | Stop Airbyte |
| `curl localhost:8006/health` | Health check |

## ALTERNATIVES AND COMPARISON

Fivetran for managed. Singer for taps. dbt for transforms only.

---

## SELF-HEALING

| Error | Fix |
|---|---|
| Connection failed | Check network connectivity and endpoint URL |
| Authentication error | Verify API keys, tokens, or credentials |
| Permission denied | Check user permissions and access rights |
| Process crashed | Check logs, restart service, verify config |
| Configuration invalid | Validate config file syntax and values |
| Resource exhausted | Monitor disk, memory, CPU usage |
| Timeout error | Increase timeout or check network latency |
| Version mismatch | Update to latest compatible version |
| Dependency missing | Install required dependencies |
| Data corruption | Restore from backup, rebuild index |

## ANTI-PATTERNS

- Do NOT skip reading documentation before setup
- Do NOT use default credentials in production environments
- Do NOT ignore error logs and warning messages
- Do NOT skip backup before making major configuration changes
- Do NOT expose internal services without proper authentication
- Do NOT use development settings in production deployment
- Do NOT skip testing after configuration changes
- Do NOT store sensitive credentials in plain text or version control

---

## INTEGRATION POINTS --- CROSS-DEPARTMENT ROUTING

| Department | Repo | Relationship |
|---|---|---|
| DATA | drizzle-orm | Same databases as targets |
| DATA | neon | Neon as destination |
| ANALYTICS | metabase | Metabase queries Airbyte-loaded data |
| INFRA | compose | Docker Compose deployment |

## CONFIGURATION REFERENCE

| Setting | Default | Description |
|---|---|---|
| log_level | info | Logging verbosity (debug, info, warn, error) |
| timeout | 30s | Default operation timeout |
| retry_count | 3 | Number of retry attempts on failure |
| port | varies | Service port number |
| config_path | varies | Path to configuration file |
| data_dir | varies | Data storage directory |

## OPERATIONAL NOTES

### Monitoring
- Check process health at regular intervals
- Monitor resource usage (CPU, memory, disk I/O)
- Set up alerting for critical failure conditions
- Review application logs for errors and warnings
- Track key performance metrics over time

### Security Best Practices
- Use strong, unique authentication credentials
- Encrypt all sensitive data in transit and at rest
- Apply the principle of least privilege for access
- Keep software updated to the latest stable version
- Audit access logs and review permissions periodically
- Use environment variables for secrets, never hardcode

### Backup Strategy
- Back up configuration files before any changes
- Test backup restoration procedures regularly
- Store backups in a geographically separate location
- Automate backup scheduling with verification
- Document recovery procedures for the team

### Troubleshooting Checklist
1. Check service status and recent logs
2. Verify configuration file syntax and values
3. Test network connectivity to dependencies
4. Verify credentials and authentication tokens
5. Check available disk space and system resources
6. Review recent configuration or code changes
7. Restart the service and monitor for errors
8. Escalate to team if issue persists after retries

## OUTPUT CONTRACT
Delivers: Open-source data integration platform.
Docs: See repository README for documentation.

## ENVIRONMENT VARIABLES

| Variable | Purpose |
|---|---|
| API_KEY | Authentication token |
| API_URL | Service endpoint URL |
| LOG_LEVEL | Logging verbosity |
| TIMEOUT | Operation timeout |
| DATA_DIR | Data storage path |
| CONFIG_PATH | Configuration file path |

## ARCHITECTURE OVERVIEW

### System Components
- Core service engine
- Configuration management layer
- Authentication and authorization
- Data persistence layer
- Logging and monitoring hooks
- API/CLI interface layer

### Data Flow
1. Input received via API/CLI/webhook
2. Authentication and validation
3. Core processing engine
4. Data persistence and caching
5. Response formatting and delivery
6. Logging and metrics emission

### Deployment Patterns

| Pattern | Description | Use Case |
|---|---|---|
| Docker | Containerized deployment | Standard production |
| Docker Compose | Multi-service deployment | Full stack |
| Kubernetes | Orchestrated containers | Enterprise scale |
| Bare Metal | Direct installation | Simple setups |
| Serverless | Cloud function deployment | Event-driven |

### Performance Optimization
- Cache frequently accessed data
- Use connection pooling for databases
- Implement request batching where possible
- Monitor and tune memory usage
- Use async operations for I/O-bound tasks
- Profile and optimize hot code paths

### Upgrade Strategy
1. Review changelog for breaking changes
2. Back up current configuration and data
3. Test upgrade in staging environment
4. Apply upgrade during maintenance window
5. Verify functionality after upgrade
6. Roll back if critical issues detected

### Compliance Notes
- Review data handling policies for GDPR
- Ensure PII is properly encrypted
- Maintain audit trail for access
- Document data retention policies
- Regular security assessments

### Team Workflow
- Use version control for all configuration
- Document operational procedures
- Maintain runbook for common issues
- Schedule regular reviews of setup
- Share knowledge across team members

### Additional Resources
- Official documentation and guides
- Community forums and discussions
- GitHub issues for bug reports
- Stack Overflow for common questions
- Discord/Slack community channels
- Blog posts and tutorials
- Video walkthroughs and demos
- API reference documentation
- Configuration examples and templates
- Migration guides from alternatives