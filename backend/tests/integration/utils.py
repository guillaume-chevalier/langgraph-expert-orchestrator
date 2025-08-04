"""
Integration test utilities.
"""


def collect_sse(text: str):
    """Parse SSE event stream into structured events."""
    events = []
    for block in text.strip().split("\n\n"):
        if not block.strip():
            continue
        ev = {}
        for line in block.split("\n"):
            line = line.strip()
            if line.startswith("event:"):
                ev["event"] = line[6:].strip()
            elif line.startswith("data:"):
                import json

                try:
                    ev.update(json.loads(line[5:].strip()))
                except json.JSONDecodeError:
                    continue
        if ev:  # Only add non-empty events
            events.append(ev)
    return events
