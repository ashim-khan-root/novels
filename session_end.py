"""Session end — run at the end of a work session."""
import sys
import json
from memory_manager import post_session

if __name__ == "__main__":
    desc = sys.argv[1] if len(sys.argv) > 1 else "Session ended"
    rating = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    decisions = []
    decision_file = ".agent/_decisions.json"
    try:
        with open(decision_file) as f:
            decisions = json.load(f)
    except Exception:
        pass
    
    sid = post_session(
        description=desc,
        session_type="task",
        duration_min=None,
        rating=rating,
        decisions=decisions,
        outcome=f"Session completed: {desc}"
    )
    print(f"Session logged (id={sid})")
    
    # Clean up temp files
    import os
    try:
        os.remove(decision_file)
    except Exception:
        pass
