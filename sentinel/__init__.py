"""Sentinel - what do the files your AI coding agent obeys make it do?

sentinel.core      static rules, score, render, the gate, ed25519 sign/verify, redaction, fixtures, self-test
sentinel.detonate  sandbox: fake tools, canary secrets, base-vs-head differential
sentinel.lock      AGENTS.lock: build, approve, sign, verify, key pinning
sentinel.gitdiff   base vs head through git; approvals and the public key are read from the BASE branch
sentinel.render    the pull-request comment
sentinel.contract  the v1 JSON shape the frontend and the VS Code extension consume
sentinel.cli / sentinel.api
"""
__version__ = "0.8.3"
