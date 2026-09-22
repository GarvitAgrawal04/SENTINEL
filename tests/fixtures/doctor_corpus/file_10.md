# advertising-ops
# D:\Repositories\advertising-ops\CLAUDE.md

## What This Is
CMO in a Box for Claude Code. Scrapes winning ads from Meta Ad Library, tears down video creative frame by frame, generates aligned ad copy and image/video variations ready to launch. Media buyer automation.

## When to Load This
- Tasks involving advertising-ops functionality
- Cross-department integration with this capability
- Production deployment and scaling

---

## CORE CONCEPTS

### Overview
CMO in a Box for Claude Code. Scrapes winning ads from Meta Ad Library, tears down video creative frame by frame, generates aligned ad copy and image/video variations ready to launch. Media buyer automation. This component integrates with the 300-repo autonomous system.

### Key Capabilities
| Capability | Description |
|---|---|
| Core | CMO in a Box for Claude Code. Scrapes winning ads from Meta Ad Library, tears down video creative frame by frame, generates aligned ad copy and image/video variations ready to launch. Media buyer automation. |
| Integration | Standard CLAUDE.md contract |
| Error handling | Self-healing protocols active |
| Testing | Unit and integration support |

### Configuration
| Setting | Default | Description |
|---|---|---|
| log_level | info | Logging verbosity |
| timeout | 30s | Default operation timeout |
| retry_count | 3 | Retry attempts on failure |

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
| Version mismatch | Update to latest version |
| Rate limited | Implement backoff |

## ANTI-PATTERNS
- Do NOT skip reading documentation before integration
- Do NOT use default credentials in production
- Do NOT ignore error logs and warnings
- Do NOT skip testing after config changes
- Do NOT expose internal services without auth
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
| Documentation | Active | CLAUDE.md |
| Error Handling | Active | Self-heal |
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
Delivers: CMO in a Box for Claude Code. Scrapes winning ads from Meta Ad Library, tears down video creative frame by frame, generates aligned ad copy and image/video variations ready to launch. Media buyer automation.
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
- Track error rates and response times

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
2. Back up current configuration and data
3. Update all dependencies to latest
4. Run full test suite for compatibility
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
- Changelog and release notes
- Contributing guidelines

### FAQ
| Question | Answer |
|---|---|
| How to get started? | See CORE SETUP section above |
| Dependencies? | Check package.json or requirements.txt |
| How to report bugs? | Open GitHub issue with reproduction |
| How to contribute? | Read CONTRIBUTING.md in repository |
| Community? | Check README for Discord or Slack |
| License? | See LICENSE file in repository root |

### Operational Notes
- Follow all CLAUDE.md contracts in D:\Repositories
- Auto-route via task-type matrix in master CLAUDE.md
- Self-heal on any error with 3 attempts before escalation
- Log all fixes to project CLAUDE.md under Learned section
- Compound learning across sessions for continuous improvement

### Runtime Notes
- This repo is part of the 300-repo autonomous system
- All changes must comply with CLAUDE.md contracts
- Self-healing protocol applies to all operations
- Log all errors and fixes for compounding learning
- Route through task-type matrix for cross-repo work
- Check existing solutions before building from scratch
- Every session starts smarter than the last
- Zero questions, zero broken output, ship