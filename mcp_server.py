"""MCP Server — exposes AI memory/tasks/insights/skills as MCP tools over stdio."""
import sys
import os
import json
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_db import (
    log_session, get_recent_sessions,
    add_task, update_task, list_tasks, get_task, delete_task,
    log_decision, get_decisions,
    add_insight, get_insights, search_insights,
    add_skill, get_skills, increment_skill,
    set_memory, get_memory, delete_memory, list_memory,
    add_goal, update_goal, list_goals,
    log_event, get_events, get_db
)
from memory_manager import (
    pre_session, post_session, extract_insights_from_outcome,
    evolve_skills, complete_task, block_task, get_status_summary, manual_insight
)

JSON_RPC_VERSION = "2.0"

# ── Tool definitions ─────────────────────────────

TOOLS = [
    {
        "name": "search_memory",
        "description": "Search agent memory by key or category",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Memory key (exact or prefix)"},
                "category": {"type": "string", "description": "Filter by category"}
            }
        }
    },
    {
        "name": "set_memory",
        "description": "Store a key-value pair in persistent memory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "value": {"type": "string"},
                "category": {"type": "string", "default": "general"}
            },
            "required": ["key", "value"]
        }
    },
    {
        "name": "get_insights",
        "description": "Retrieve extracted insights, optionally filtered by type",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "Filter: worked/failed/pattern/lesson/preference/decision"},
                "limit": {"type": "integer", "default": 20}
            }
        }
    },
    {
        "name": "search_insights",
        "description": "Search insights by keyword content",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 20}
            },
            "required": ["query"]
        }
    },
    {
        "name": "add_insight",
        "description": "Manually log an insight for later skill evolution",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["worked", "failed", "pattern", "lesson", "preference", "decision"]},
                "content": {"type": "string"},
                "source": {"type": "string"}
            },
            "required": ["type", "content"]
        }
    },
    {
        "name": "get_skills",
        "description": "List evolved skills ordered by usage",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20}
            }
        }
    },
    {
        "name": "evolve_skills",
        "description": "Trigger skill evolution from recent insights",
        "inputSchema": {
            "type": "object",
            "properties": {
                "min_confidence": {"type": "number", "default": 0.7}
            }
        }
    },
    {
        "name": "log_session_end",
        "description": "Log a completed session and extract insights",
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "session_type": {"type": "string", "default": "task"},
                "duration_min": {"type": "integer"},
                "rating": {"type": "integer"},
                "decisions": {"type": "array", "items": {"type": "object"}},
                "outcome": {"type": "string"}
            },
            "required": ["description"]
        }
    },
    {
        "name": "get_tasks",
        "description": "List tasks, optionally filtered by status",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["active", "blocked", "completed"]}
            }
        }
    },
    {
        "name": "add_task",
        "description": "Create a new task",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "category": {"type": "string"},
                "notes": {"type": "string"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "complete_task",
        "description": "Mark a task done with optional outcome (triggers insight extraction)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"},
                "outcome": {"type": "string"},
                "rating": {"type": "integer"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "block_task",
        "description": "Mark a task as blocked",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"},
                "reason": {"type": "string"}
            },
            "required": ["task_id", "reason"]
        }
    },
    {
        "name": "get_decisions",
        "description": "View recent decisions made",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20}
            }
        }
    },
    {
        "name": "status",
        "description": "Get a compact summary of current agent state",
        "inputSchema": {"type": "object", "properties": {}}
    },
]

RESOURCES = [
    {
        "uri": "memory://summary",
        "name": "Agent Memory Summary",
        "description": "Compact status overview",
        "mimeType": "application/json",
    },
]


# ── JSON-RPC dispatcher ──────────────────────────

class MCPServer:
    def __init__(self):
        self.request_id = 0

    def send(self, msg):
        line = json.dumps(msg, ensure_ascii=False, default=str)
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    def error(self, req_id, code, message, data=None):
        err = {"code": code, "message": message}
        if data:
            err["data"] = data
        self.send({"jsonrpc": JSON_RPC_VERSION, "id": req_id, "error": err})

    def result(self, req_id, result_data):
        self.send({"jsonrpc": JSON_RPC_VERSION, "id": req_id, "result": result_data})

    def notify(self, method, params=None):
        msg = {"jsonrpc": JSON_RPC_VERSION, "method": method}
        if params:
            msg["params"] = params
        self.send(msg)

    def handle_initialize(self, req_id, params):
        self.result(req_id, {
            "protocolVersion": "2025-11-25",
            "capabilities": {
                "tools": {},
                "resources": {},
            },
            "serverInfo": {
                "name": "ai-worker-mcp",
                "version": "1.0.0",
            },
        })

    def handle_list_tools(self, req_id, _params):
        self.result(req_id, {"tools": TOOLS})

    def handle_call_tool(self, req_id, params):
        name = params.get("name", "")
        args = params.get("arguments", {})
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            return self.error(req_id, -32601, f"Unknown tool: {name}")
        try:
            result_data = handler(args)
            self.result(req_id, {"content": [{"type": "text", "text": json.dumps(result_data, ensure_ascii=False, default=str, indent=2)}]})
        except Exception as e:
            self.error(req_id, -32000, str(e), traceback.format_exc())

    def handle_list_resources(self, req_id, _params):
        self.result(req_id, {"resources": RESOURCES})

    def handle_read_resource(self, req_id, params):
        uri = params.get("uri", "")
        if uri == "memory://summary":
            self.result(req_id, {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(get_status_summary(), ensure_ascii=False, default=str, indent=2),
                    }
                ]
            })
        else:
            self.error(req_id, -32001, f"Unknown resource: {uri}")

    def dispatch(self, msg):
        req_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "initialize":
            return self.handle_initialize(req_id, params)
        elif method in ("list_tools", "tools/list"):
            return self.handle_list_tools(req_id, params)
        elif method in ("call_tool", "tools/call"):
            return self.handle_call_tool(req_id, params)
        elif method in ("list_resources", "resources/list"):
            return self.handle_list_resources(req_id, params)
        elif method in ("read_resource", "resources/read"):
            return self.handle_read_resource(req_id, params)
        elif method == "notifications/initialized":
            return  # no response expected
        elif method == "ping":
            return self.result(req_id, {})
        elif method.startswith("notifications/"):
            return  # no response expected for notifications
        else:
            self.error(req_id, -32601, f"Method not found: {method}")

    def run(self):
        try:
            pre_session("MCP server started")
        except Exception as e:
            self.send({"jsonrpc": JSON_RPC_VERSION, "method": "logging/notification", "params": {"level": "warning", "message": f"pre_session failed: {e}"}})
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                self.dispatch(msg)
            except json.JSONDecodeError:
                self.error(None, -32700, "Parse error")
            except Exception as e:
                self.error(None, -32000, str(e), traceback.format_exc())


# ── Tool handlers ────────────────────────────────

def _search_memory(args):
    key = args.get("key")
    category = args.get("category")
    if key:
        val = get_memory(key)
        return {"key": key, "value": val} if val else {"message": "Not found"}
    rows = list_memory(category)
    return [{"key": r["key"], "value": r["value"][:200], "category": r["category"]} for r in rows]

def _set_memory(args):
    set_memory(args["key"], args["value"], args.get("category", "general"))
    return {"status": "ok", "key": args["key"]}

def _get_insights(args):
    rows = get_insights(args.get("limit", 20), args.get("type"))
    return [{"id": r["id"], "type": r["type"], "content": r["content"][:200], "source": r["source"], "confidence": r["confidence"]} for r in rows]

def _search_insights(args):
    rows = search_insights(args["query"], args.get("limit", 20))
    return [{"id": r["id"], "type": r["type"], "content": r["content"][:200], "confidence": r["confidence"]} for r in rows]

def _add_insight(args):
    manual_insight(args["type"], args["content"], args.get("source"))
    return {"status": "ok"}

def _get_skills(args):
    rows = get_skills(args.get("limit", 20))
    return [{"name": r["name"], "description": r["description"][:200], "usage_count": r["usage_count"], "when_to_use": r["when_to_use"][:100]} for r in rows]

def _evolve_skills(args):
    created = evolve_skills(args.get("min_confidence", 0.7))
    return {"skills_created": created}

def _log_session_end(args):
    sid = post_session(
        description=args["description"],
        session_type=args.get("session_type", "task"),
        duration_min=args.get("duration_min"),
        rating=args.get("rating"),
        decisions=args.get("decisions", []),
        outcome=args.get("outcome")
    )
    return {"session_id": sid}

def _get_tasks(args):
    rows = list_tasks(args.get("status"))
    return [{"id": r["id"], "title": r["title"], "status": r["status"], "priority": r["priority"], "blocker": r["blocker"]} for r in rows]

def _add_task(args):
    tid = add_task(args["title"], args.get("priority", "medium"), args.get("category"), args.get("notes"))
    return {"task_id": tid}

def _complete_task(args):
    t = complete_task(args["task_id"], args.get("outcome"), args.get("rating"))
    return {"task_id": args["task_id"], "title": t["title"]} if t else {"error": "not found"}

def _block_task(args):
    block_task(args["task_id"], args["reason"])
    return {"status": "blocked", "task_id": args["task_id"]}

def _get_decisions(args):
    rows = get_decisions(args.get("limit", 20))
    return [{"date": r["date"], "decision": r["decision"][:200], "reason": r["reason"][:200] if r["reason"] else None} for r in rows]

def _status(_args):
    return get_status_summary()


TOOL_HANDLERS = {
    "search_memory": _search_memory,
    "set_memory": _set_memory,
    "get_insights": _get_insights,
    "search_insights": _search_insights,
    "add_insight": _add_insight,
    "get_skills": _get_skills,
    "evolve_skills": _evolve_skills,
    "log_session_end": _log_session_end,
    "get_tasks": _get_tasks,
    "add_task": _add_task,
    "complete_task": _complete_task,
    "block_task": _block_task,
    "get_decisions": _get_decisions,
    "status": _status,
}


if __name__ == "__main__":
    MCPServer().run()
