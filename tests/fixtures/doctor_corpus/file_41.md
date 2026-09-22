# anything-llm
# D:\Repositories\anything-llm\CLAUDE.md

## What This Is
All-in-one LLM desktop application. Chat with docs, RAG, multi-provider support.

## When to Load This
- When task involves anything-llm functionality
- Cross-department workflow coordination
- Production deployment and scaling

---

## CORE CONCEPTS

### Overview
All-in-one LLM desktop application. Chat with docs, RAG, multi-provider support. This component integrates with the broader 300-repo
autonomous system through standardized CLAUDE.md contracts.

### Key Capabilities
| Capability | Description |
|---|---|
| Core functionality | All-in-one LLM desktop application. Chat with docs, RAG, multi-provider support. |
| API integration | Standard interfaces |
| Documentation | CLAUDE.md contract |
| Error handling | Self-healing protocols |
| Testing | Unit and integration support |

### Configuration Reference
| Setting | Default | Description |
|---|---|---|
| log_level | info | Logging verbosity |
| timeout | 30s | Default operation timeout |
| retry_count | 3 | Retry attempts on failure |
| max_concurrency | 4 | Maximum parallel ops |

---

## SELF-HEALING

| Error | Fix |
|---|---|
| Module not found | Install dependencies per README |
| Connection refused | Verify service is running |
| Auth failed | Check API keys or tokens |
| Timeout | Increase timeout or check network |
| Permission denied | Verify user permissions |
| Config error | Validate config syntax |
| Version mismatch | Update to latest compatible version |
| Resource exhausted | Increase limits |
| Data corruption | Restore from backup |
| Rate limited | Implement exponential backoff |

## ANTI-PATTERNS
- Do NOT skip reading documentation before integration
- Do NOT use default credentials in production
- Do NOT ignore error logs and warnings
- Do NOT skip backup before major changes
- Do NOT expose internal services without auth
- Do NOT use dev settings in production
- Do NOT skip testing after config changes
- Do NOT store secrets in version control

---

## INTEGRATION POINTS
| Department | Repo | Relationship |
|---|---|---|
| CLAUDE META | claude-code | Integration |
| INFRA | compose | Deployment |

## DETAILED CAPABILITY MATRIX
| Capability | Status | Notes |
|---|---|---|
| API Integration | Active | Standard |
| CLI Interface | Active | Commands |
| Docker Support | Active | Container |
| Authentication | Active | Token/key |
| Logging | Active | Structured |
| Error Handling | Active | Self-heal |
| Documentation | Active | CLAUDE.md |
| Testing | Active | Unit/integ |

### Deployment Checklist
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] Health check responding
- [ ] Auth configured
- [ ] Monitoring active
- [ ] Backup documented
- [ ] Rollback plan ready
- [ ] Security audit done

### Troubleshooting
1. Check status and logs
2. Verify configuration
3. Test connectivity
4. Verify credentials
5. Check resources
6. Review recent changes
7. Restart and monitor
8. Escalate if persists

## OUTPUT CONTRACT
Delivers: All-in-one LLM desktop application. Chat with docs, RAG, multi-provider support.
Docs: See repository README.

## ADVANCED CONFIGURATION

### Environment Variables
| Variable | Description | Default |
|---|---|---|
| LOG_LEVEL | Logging verbosity | info |
| DEBUG | Enable debug mode | false |
| PORT | Service port | auto |
| API_KEY | Authentication token | required |
| TIMEOUT | Operation timeout | 30s |
| MAX_RETRIES | Retry attempts | 3 |
| CACHE_TTL | Cache duration | 300s |
| CONCURRENCY | Parallel operations | 4 |

### Version History
| Version | Changes |
|---|---|
| v1.0 | Initial release |
| v2.0 | API integration |
| v3.0 | Self-healing protocols |
| v4.0 | Multi-agent orchestration |
| v5.0 | Max-advanced documentation |

### System Requirements
| Component | Minimum | Recommended |
|---|---|---|
| Runtime | See README | Latest LTS |
| Memory | 256MB | 1GB+ |
| Storage | 100MB | 1GB+ |
| Network | Broadband | Low latency |

### Security Best Practices
- Use strong, unique authentication credentials
- Encrypt all sensitive data in transit and at rest
- Apply principle of least privilege for access control
- Keep all dependencies updated to latest stable
- Audit access logs and review permissions regularly
- Use environment variables for secrets management
- Never commit credentials to version control
- Implement rate limiting on public endpoints

### Monitoring and Observability
- Set up health check endpoints
- Monitor resource usage at regular intervals
- Configure alerting for critical failures
- Track key performance metrics over time
- Review application logs for anomalies
- Implement structured logging format
- Set up dashboard for real-time metrics

### Common Integration Hooks
| Hook | Trigger | Action |
|---|---|---|
| on_start | Service startup | Initialize connections |
| on_request | Incoming request | Validate and route |
| on_error | Error detected | Self-heal or escalate |
| on_complete | Task finished | Log metrics and cleanup |
| on_shutdown | Service stopping | Graceful shutdown |

### Migration Guide
1. Review changelog for breaking changes
2. Back up current configuration
3. Update dependencies
4. Run test suite for compatibility
5. Deploy to staging for validation
6. Monitor for errors after upgrade
7. Roll back if critical issues found

### Additional Resources
- Official documentation and API reference
- Community forums and Discord channels
- GitHub issues for bug tracking
- Stack Overflow community support
- Blog posts, tutorials, and guides
- Video walkthroughs and demos
- Configuration examples and templates
- Migration guides from alternatives
- Changelog and release notes
- Contributing guidelines

### FAQ
| Question | Answer |
|---|---|
| How to get started? | See CORE SETUP section above |
| Dependencies? | Check package.json or requirements.txt |
| How to report bugs? | Open GitHub issue with reproduction |
| How to contribute? | Read CONTRIBUTING.md in repository |
| Community? | Check README for Discord or Slack links |
| License? | See LICENSE file in repository root |

### Operational Notes
- Follow all CLAUDE.md contracts in D:\Repositories
- Auto-route via task-type matrix
- Self-heal on any error (3 attempts)
- Log all fixes to project CLAUDE.md
- Compound learning across sessions