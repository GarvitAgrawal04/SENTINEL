# andrej-karpathy-skills --- Skill definitions inspired by Andrej Karpathy AI engineering principles
# D:\Repositories\andrej-karpathy-skills\CLAUDE.md

## What This Is
Skill definitions inspired by Andrej Karpathy AI engineering principles. Neural network debugging, training optimization, model evaluation, and ML engineering best practices encoded as executable skills.

## When to Load This
- Primary use case for this tool
- Integration with development workflows
- Automation and productivity enhancement
- Team collaboration and knowledge sharing
- Development environment setup
- Quality and testing workflows
- Cross-platform compatibility

---

## CORE CONCEPTS

### Overview
Skill definitions inspired by Andrej Karpathy AI engineering principles. This repository provides essential functionality for the autonomous
engineering system. It integrates with the broader platform through standardized
interfaces and follows established patterns for cross-department communication.

### Key Features
- Core functionality as described above
- Integration with the autonomous engineering pipeline
- Standardized API and interface patterns
- Cross-department routing and communication
- Self-healing and error recovery capabilities
- Comprehensive documentation and examples

### Usage Patterns

| Pattern | Description | When to Use |
|---|---|---|
| Direct integration | Use APIs and tools directly | Simple, single-service tasks |
| Pipeline integration | Chain with other repos | Multi-step workflows |
| Agent delegation | Delegate via agent system | Complex autonomous tasks |
| Event-driven | React to webhooks/events | Asynchronous processing |
| Batch processing | Process multiple items | Bulk operations |

### Configuration

| Setting | Default | Description |
|---|---|---|
| log_level | info | Logging verbosity (debug, info, warn, error) |
| timeout | 30s | Default operation timeout |
| retry_count | 3 | Number of retry attempts on failure |
| max_concurrency | 4 | Maximum parallel operations |
| cache_ttl | 300s | Cache time-to-live |

### Integration Protocol
1. Read this CLAUDE.md to understand capabilities
2. Check if the functionality is needed for the current task
3. Load relevant API patterns from the core concepts section
4. Integrate following the established patterns
5. Test the integration with standard verification
6. Monitor for errors using self-healing table

---

## SELF-HEALING

| Error | Fix |
|---|---|
| Module not found | Install dependencies: check package.json or requirements |
| Connection refused | Verify service is running and accessible |
| Authentication failed | Check API keys, tokens, and credentials |
| Timeout error | Increase timeout or check network connectivity |
| Permission denied | Verify user permissions and access rights |
| Configuration error | Validate config file syntax and required fields |
| Version mismatch | Update to latest compatible version |
| Resource exhausted | Monitor and increase disk, memory, or CPU limits |
| Data corruption | Restore from backup and rebuild indexes |
| Rate limited | Implement backoff or increase rate limits |

## ANTI-PATTERNS

- Do NOT skip reading documentation before integration
- Do NOT use default credentials in any environment
- Do NOT ignore error logs and warning messages
- Do NOT skip backup before major configuration changes
- Do NOT expose internal services without proper authentication
- Do NOT use development settings in production deployment
- Do NOT skip testing after any configuration changes
- Do NOT store sensitive credentials in version control
- Do NOT bypass the self-healing protocol on errors
- Do NOT duplicate functionality that exists in other repos

---

## CROSS-DEPARTMENT ROUTING

| Department | Repo | Relationship |
|---|---|---|
| BACKEND | hono | API integration |
| AI | ai | AI SDK integration |
| INFRA | compose | Docker deployment |
| QUALITY | vitest | Testing integration |
| CLAUDE META | claude-code | Claude Code integration |

## OPERATIONAL NOTES

### Monitoring Checklist
- Verify service health at regular intervals
- Monitor resource usage (CPU, memory, disk I/O)
- Set up alerting for critical failure conditions
- Review application logs for errors and anomalies
- Track key performance metrics over time

### Security Best Practices
- Use strong, unique authentication credentials
- Encrypt all sensitive data in transit and at rest
- Apply the principle of least privilege for access control
- Keep all software updated to latest stable versions
- Audit access logs and review permissions periodically
- Use environment variables for secrets management

### Backup and Recovery
- Back up configuration before any changes
- Test backup restoration procedures regularly
- Store backups in geographically separate location
- Automate backup scheduling with verification
- Document recovery procedures for the team

### Troubleshooting Steps
1. Check service status and recent log entries
2. Verify configuration file syntax and values
3. Test network connectivity to all dependencies
4. Verify credentials and authentication tokens
5. Check available disk space and system resources
6. Review recent configuration or code changes
7. Restart the service and monitor for errors
8. Escalate to team if issue persists after retry

## OUTPUT CONTRACT
Delivers: Skill definitions inspired by Andrej Karpathy AI engineering principles.
Docs: See repository README for full documentation.

## DETAILED CAPABILITY MATRIX

### Core Capabilities
| Capability | Status | Notes |
|---|---|---|
| API Integration | Active | REST/JSON standard |
| CLI Interface | Active | Command-line tools available |
| Docker Support | Active | Container deployment |
| Authentication | Active | Token/key based |
| Logging | Active | Structured logging |
| Error Handling | Active | Self-healing patterns |
| Documentation | Active | CLAUDE.md contract |
| Testing | Active | Unit and integration |
| CI/CD | Active | Pipeline integration |
| Monitoring | Active | Health check endpoints |

### Version History
| Version | Changes |
|---|---|
| v1.0 | Initial release with core features |
| v2.0 | Added API integration and MCP support |
| v3.0 | Self-healing protocols and cross-department routing |
| v4.0 | Multi-agent orchestration patterns |
| v5.0 | Max-advanced documentation standard |

### Dependencies
- Node.js 18+ or Python 3.10+ (varies by repo)
- Docker and Docker Compose for containerized deployment
- Git for version control and collaboration
- Environment variables for configuration management

### Performance Benchmarks
| Metric | Target | Notes |
|---|---|---|
| Response time | < 200ms | P95 latency |
| Throughput | > 100 req/s | Under normal load |
| Memory usage | < 512MB | Per instance |
| CPU usage | < 50% | Single core |
| Startup time | < 5s | Cold start |

### Data Flow Architecture
1. Request received via API, CLI, or event trigger
2. Authentication and authorization validation
3. Input validation and sanitization
4. Core processing with error handling
5. Data persistence or transformation
6. Response formatting and delivery
7. Logging, metrics, and audit trail
8. Cache invalidation if applicable

### Deployment Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Health check endpoint verified
- [ ] SSL/TLS certificates installed
- [ ] Firewall rules configured
- [ ] Monitoring and alerting set up
- [ ] Backup procedures documented
- [ ] Rollback plan prepared
- [ ] Load testing completed
- [ ] Security audit passed

### Common Integration Hooks
| Hook | Trigger | Action |
|---|---|---|
| on_start | Service startup | Initialize connections |
| on_request | Incoming request | Validate and route |
| on_error | Error detected | Log and self-heal |
| on_complete | Task completed | Emit metrics |
| on_shutdown | Service stopping | Cleanup resources |