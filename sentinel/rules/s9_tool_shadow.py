"""
sentinel/rules/s9_tool_shadow.py
S9 — Tool shadowing (Deadbugz structural pattern).
Penalty: −30. Not structurally unambiguous.
ATR: ATR-MCP-004.

Fires when:
  (a) A new MCP tool name collides with a known-trusted tool name, OR
  (b) An approved MCP tool's returned metadata changes shape post-approval
      (Layer 2 needed for the post-approval check — this rule handles the
       static detection of the naming collision pattern).

Deadbugz used mechanism (b): behaved normally for three tool calls, then
rewrote its description metadata. S3+S9 catch (a); Layer 2 is needed for (b).
"""
from __future__ import annotations
import json
import re
from .base import Finding, RULE_NAMES

# Names of well-known trusted MCP tools that attackers might shadow
# to gain implicit trust from an agent that has already approved them.
_TRUSTED_TOOL_NAMES: frozenset[str] = frozenset({
    "bash", "computer", "str_replace_editor", "str_replace_based_edit_tool",
    "read_file", "write_file", "list_dir", "search_files",
    "create_file", "delete_file", "execute_command",
    "web_search", "web_fetch", "browser", "screenshot",
    # Claude Code native tools
    "Task", "Bash", "Read", "Write", "Edit", "MultiEdit",
    "WebFetch", "WebSearch", "TodoRead", "TodoWrite",
    "NotebookRead", "NotebookEdit", "exit_plan_mode", "mcp__",
    "Glob", "Grep",
})

# Filesystem-access patterns in tool names or descriptions that suggest
# the tool is attempting to access sensitive paths post-approval
_SENSITIVE_PATH_RE = re.compile(
    r'(?:ssh|aws|\.kube|kubernetes|\.env|\.netrc|\.pgpass|'
    r'credentials|secret|private[_-]?key|id_rsa|\.npmrc)',
    re.IGNORECASE,
)


def scan(text: str, filename: str, trusted_tools: dict = None) -> list[Finding]:
    """
    S9 — Tool shadowing detector.
    """
    if trusted_tools is None:
        trusted_tools = {}

    if not filename.lower().endswith('.json'):
        return []
    findings: list[Finding] = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []

    # Extract tool definitions — handle both flat and nested schemas
    tools: list[dict] = []
    server_name = "unknown"
    if isinstance(data, dict):
        server_name = data.get("server", "unknown")
        # MCP standard: {"tools": [...]}
        if "tools" in data and isinstance(data["tools"], list):
            tools = data["tools"]
        # Claude Code MCP config: {"mcpServers": {"name": {"tools": [...]}}}
        for s_name, server_cfg in data.get("mcpServers", {}).items():
            if isinstance(server_cfg, dict) and "tools" in server_cfg:
                tools.extend(server_cfg["tools"])
                if server_name == "unknown":
                    server_name = s_name

    seen_tool_names = set()

    for tool in tools:
        if not isinstance(tool, dict):
            continue
        tool_name = str(tool.get("name", "")).strip()
        tool_desc = str(tool.get("description", "")).strip()
        tool_schema = tool.get("inputSchema", {})

        if not tool_name:
            continue

        # Check against trusted_tools (Deadbugz detection)
        trusted = trusted_tools.get(tool_name)
        if trusted:
            t_server = trusted.get("server")
            if t_server and t_server != server_name and server_name != "unknown":
                findings.append(Finding(
                    rule_id="S9",
                    rule_name=RULE_NAMES["S9"],
                    severity="high",
                    filename=filename,
                    line=1,
                    message=f"MCP tool '{tool_name}' shadows a tool from trusted server '{t_server}'",
                    snippet=f"name: {tool_name}, from server: {t_server}",
                    atr_id="ATR-MCP-004",
                ))
            elif t_server == server_name or server_name == "unknown":
                # Check for shape/description changes (post-approval change)
                t_desc = trusted.get("description", "").strip()
                t_schema = trusted.get("inputSchema", {})
                if t_desc != tool_desc or json.dumps(t_schema, sort_keys=True) != json.dumps(tool_schema, sort_keys=True):
                    # Schema or description changed post-approval
                    new_param = ""
                    if isinstance(tool_schema, dict) and "properties" in tool_schema:
                        for p in tool_schema["properties"]:
                            if isinstance(t_schema, dict) and "properties" in t_schema and p not in t_schema["properties"]:
                                new_param = p
                    findings.append(Finding(
                        rule_id="S9",
                        rule_name=RULE_NAMES["S9"],
                        severity="high",
                        filename=filename,
                        line=1,
                        message=f"MCP tool '{tool_name}' changed shape post-approval",
                        snippet=f"Tool {tool_name} description changed. new param: {new_param}",
                        reconstruction=f"Tool '{tool_name}' changed after you approved it.",
                        atr_id="ATR-MCP-004",
                    ))
            
            seen_tool_names.add(tool_name)
            continue

        # Check (a): collision with a known-trusted built-in tool name OR duplicate within file
        is_builtin = any(tool_name.lower() == t.lower() for t in _TRUSTED_TOOL_NAMES)
        is_duplicate = tool_name in seen_tool_names
        
        seen_tool_names.add(tool_name)

        if is_builtin or is_duplicate:
            findings.append(Finding(
                rule_id="S9",
                rule_name=RULE_NAMES["S9"],
                severity="high",
                filename=filename,
                line=1,
                message=(
                    f"MCP tool '{tool_name}' shadows a known-trusted or existing tool name \u2014 "
                    f"an agent that previously approved the real tool may extend "
                    f"that trust to this server"
                ),
                snippet=f"name: {tool_name} - {tool_desc[:150]}",
                reconstruction=(
                    f"Tool '{tool_name}' has the same name as an existing or trusted built-in tool. "
                    f"An agent that has already approved the legitimate '{tool_name}' may "
                    f"extend that implicit trust to this MCP server's version \u2014 "
                    f"this is the structural pattern behind tool-shadowing attacks."
                ),
                atr_id="ATR-MCP-004",
            ))

        # Check (a+): description contains sensitive path access
        if tool_desc and _SENSITIVE_PATH_RE.search(tool_desc):
            findings.append(Finding(
                rule_id="S9",
                rule_name=RULE_NAMES["S9"],
                severity="high",
                filename=filename,
                line=1,
                message=(
                    f"MCP tool '{tool_name}' description references sensitive filesystem "
                    f"paths (SSH keys, AWS credentials, Kubernetes configs)"
                ),
                snippet=f"name: {tool_name} - {tool_desc[:150]}",
                reconstruction=(
                    f"Tool '{tool_name}' explicitly instructs the agent to access sensitive "
                    f"files (SSH keys, AWS credentials, etc.). This is the Deadbugz pattern: "
                    f"a tool that was previously approved for benign operations has rewritten "
                    f"its description to request filesystem access to credential paths. "
                    f"Layer 2 semantic displacement is needed to confirm post-approval change."
                ),
                atr_id="ATR-MCP-004",
            ))

    return findings
