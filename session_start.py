"""Session start — run at the beginning of a work session."""
import sys
from memory_manager import pre_session, evolve_skills

if __name__ == "__main__":
    desc = sys.argv[1] if len(sys.argv) > 1 else "Work session"
    ctx = pre_session(desc)
    new_skills = evolve_skills(min_confidence=0.5)
    
    print(f"Session started: {desc}")
    print(f"  Active tasks: {ctx['active_tasks']}")
    print(f"  Active goals: {ctx['active_goals']}")
    if ctx['active_tasks'] > 0:
        from ai_db import list_tasks
        for t in list_tasks("active"):
            print(f"    [{t['id']}] {t['title']} ({t['priority']})")
    if ctx['top_skills']:
        print(f"  Top skills: {', '.join(ctx['top_skills'])}")
    if new_skills:
        print(f"  New skills evolved: {', '.join(new_skills)}")
