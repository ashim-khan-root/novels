"""Memory Manager — session lifecycle, insight extraction, skill evolution."""
import json
import re
from datetime import datetime
from ai_db import (
    log_session, get_recent_sessions,
    add_task, update_task, list_tasks, get_task,
    log_decision, get_decisions,
    add_insight, get_insights, search_insights,
    add_skill, get_skills, increment_skill,
    set_memory, get_memory,
    add_goal, update_goal, list_goals,
    log_event, get_events, get_db
)

# ── Session Lifecycle ────────────────────────────

def pre_session(task_description=None):
    """Run at session start. Loads context, sets up tracking."""
    recent = get_recent_sessions(5)
    active_tasks = list_tasks("active")
    goals = list_goals("active")
    skills = get_skills(5)

    context = {
        "recent_sessions": [
            {"desc": s["description"], "type": s["session_type"], "rating": s["rating"]}
            for s in recent
        ],
        "active_tasks": len(active_tasks),
        "active_goals": len(goals),
        "top_skills": [s["name"] for s in skills],
    }
    log_event("session_start", "memory_manager", {"task": task_description, "context": context})
    return context


def post_session(description, session_type="task", duration_min=None, rating=None, decisions=None, outcome=None):
    """Run at session end. Stores session, extracts insights."""
    sid = log_session(session_type, description, duration_min, rating, decisions, outcome)

    for d in (decisions or []):
        log_decision(d["decision"], d.get("reason"), {"session_id": sid, "context": d.get("context")})

    if outcome:
        extract_insights_from_outcome(description, outcome, source=f"session:{sid}")

    log_event("session_end", "memory_manager", {
        "session_id": sid, "type": session_type, "rating": rating
    })
    return sid


# ── Insight Extraction ───────────────────────────

PATTERN_RULES = [
    (r"(?i)(worked|success|great|good|excellent)", "worked"),
    (r"(?i)(failed|broke|bug|error|issue|wrong)", "failed"),
    (r"(?i)(always|never|whenever|every time)", "pattern"),
    (r"(?i)(learned|lesson|next time|note to self)", "lesson"),
    (r"(?i)(prefer|better|faster|easier|simpler)", "preference"),
]


def extract_insights_from_outcome(description, outcome, source=None):
    """Auto-detect patterns from session outcomes and store as insights."""
    text = f"{description} {outcome}"
    found_types = set()

    for pattern, insight_type in PATTERN_RULES:
        if re.search(pattern, text):
            if insight_type not in found_types:
                # Extract the relevant sentence
                sentences = re.split(r'[.!?\n]', text)
                relevant = [s.strip() for s in sentences if re.search(pattern, s)]
                for sentence in relevant[:2]:
                    add_insight(insight_type, sentence, source, confidence=0.8)
                found_types.add(insight_type)

    # Extract any explicit decisions
    decision_patterns = re.findall(r"(?:decided|chose|opted for|switched to|picked)\s+([^.!?\n]+)", text)
    for dp in decision_patterns[:3]:
        add_insight("decision", dp.strip(), source, confidence=0.9)


def manual_insight(insight_type, content, source=None, tags=None):
    """Manually log an insight (called by user or agent)."""
    add_insight(insight_type, content, source, confidence=1.0, tags=tags)
    log_event("insight_added", "manual", {"type": insight_type, "content": content[:80]})


# ── Skill Evolution ──────────────────────────────

def evolve_skills(min_confidence=0.7):
    """Cluster recent insights into reusable skills."""
    recent_insights = get_insights(100)
    if len(recent_insights) < 3:
        return []

    # Group by content similarity (simple keyword overlap)
    clusters = {}
    for ins in recent_insights:
        if ins["confidence"] < min_confidence:
            continue
        words = set(ins["content"].lower().split())
        key = _find_cluster(clusters, words)
        if key is None:
            # Use first meaningful keyword as cluster key
            key_words = [w for w in words if len(w) > 4]
            key = key_words[0] if key_words else ins["content"][:20]
        clusters.setdefault(key, []).append(ins)

    new_skills = []
    for key, cluster in clusters.items():
        if len(cluster) < 2:
            continue

        types = set(c["type"] for c in cluster)
        contents = [c["content"] for c in cluster]
        example = max(contents, key=len)
        insight_ids = [c["id"] for c in cluster]

        if "worked" in types and "failed" in types:
            skill_type = "best_practice"
            desc = f"Best practice: {key}"
            when = f"When dealing with {key}"
        elif "pattern" in types:
            skill_type = "pattern"
            desc = f"Pattern: {key}"
            when = f"When you observe {key}"
        else:
            skill_type = "general"
            desc = f"Knowledge: {key}"
            when = "When relevant"

        try:
            add_skill(
                name=f"{skill_type}:{key[:50]}",
                description=f"{desc}. Based on {len(cluster)} observations.",
                when_to_use=when,
                example=example[:300],
                source_insight_ids=insight_ids
            )
            new_skills.append(key)
        except Exception:
            pass

    if new_skills:
        log_event("skills_evolved", "memory_manager", {"skills": new_skills, "cluster_count": len(clusters)})

    return new_skills


def _find_cluster(clusters, words):
    """Find a cluster that has significant word overlap."""
    for key, items in clusters.items():
        key_words = set(key.lower().split())
        overlap = len(words & {w for item in items for w in item["content"].lower().split()})
        if overlap > 2:
            return key
    return None


# ── Task Workflow ────────────────────────────────

def complete_task(task_id, outcome=None, rating=None):
    """Mark a task complete, extract insights from the outcome."""
    task = get_task(task_id)
    if not task:
        return None

    update_task(task_id, status="completed")
    title = task["title"]

    if outcome:
        extract_insights_from_outcome(title, outcome, source=f"task:{task_id}")
        log_event("task_completed", "memory_manager", {"task_id": task_id, "title": title, "rating": rating})

    return task


def block_task(task_id, blocker_reason):
    """Mark a task as blocked."""
    update_task(task_id, status="blocked", blocker=blocker_reason)
    log_event("task_blocked", "memory_manager", {"task_id": task_id, "blocker": blocker_reason})


# ── Summary / Status ─────────────────────────────

def get_status_summary():
    """Get a compact summary of current state."""
    active = list_tasks("active")
    blocked = list_tasks("blocked")
    goals = list_goals("active")
    recent_insights = get_insights(5)
    top_skills = get_skills(3)

    return {
        "active_tasks": len(active),
        "blocked_tasks": len(blocked),
        "active_goals": len(goals),
        "recent_insights": [
            f"[{i['type']}] {i['content'][:100]}"
            for i in recent_insights
        ],
        "top_skills": [s["name"] for s in top_skills],
    }
