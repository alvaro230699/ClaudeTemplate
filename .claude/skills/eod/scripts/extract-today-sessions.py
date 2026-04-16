#!/usr/bin/env python3
"""
Extract and compact today's Claude session activity for the current project.
Outputs a short summary of what was worked on — safe to load into context.

Usage: python3 extract-today-sessions.py [project_path]
  project_path defaults to the current working directory.
"""

import json
import os
import re
import sys
from datetime import date, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
MAX_TEXT_LEN   = 300   # truncate individual messages before summarising
MAX_ITEMS      = 60    # max raw items collected before compacting
TODAY          = date.today().isoformat()  # e.g. "2026-04-07"

# ── Resolve project slug ───────────────────────────────────────────────────────
project_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
slug = re.sub(r"[^a-zA-Z0-9]", "-", project_path)
sessions_dir = Path.home() / ".claude" / "projects" / slug

if not sessions_dir.exists():
    print(f"[eod] No sessions directory found for: {project_path}")
    sys.exit(0)

# ── Find today's session files ─────────────────────────────────────────────────
today_files = [
    f for f in sessions_dir.glob("*.jsonl")
    if date.fromtimestamp(f.stat().st_mtime).isoformat() == TODAY
]

if not today_files:
    print(f"[eod] No sessions found for today ({TODAY}).")
    sys.exit(0)

# ── Extract raw activity ───────────────────────────────────────────────────────
items = []

for session_file in sorted(today_files):
    with open(session_file, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            rtype = record.get("type")

            # User messages — what was requested
            if rtype == "user":
                content = record.get("message", {}).get("content", "")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text = block.get("text", "").strip()
                            if text:
                                items.append(("user", text[:MAX_TEXT_LEN]))
                elif isinstance(content, str) and content.strip():
                    items.append(("user", content.strip()[:MAX_TEXT_LEN]))

            # Assistant messages — what was done/explained
            elif rtype == "assistant":
                content = record.get("message", {}).get("content", "")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text = block.get("text", "").strip()
                            if text:
                                items.append(("assistant", text[:MAX_TEXT_LEN]))
                elif isinstance(content, str) and content.strip():
                    items.append(("assistant", content.strip()[:MAX_TEXT_LEN]))

            if len(items) >= MAX_ITEMS:
                break
    if len(items) >= MAX_ITEMS:
        break

# ── Compact: deduplicate and summarise ─────────────────────────────────────────
# Collapse consecutive same-role entries and strip boilerplate phrases
SKIP_PHRASES = [
    "let me", "i'll", "i will", "sure", "of course", "great", "understood",
    "listo", "entendido", "claro", "ok", "okay", "por supuesto",
]

def is_boilerplate(text: str) -> bool:
    lower = text.lower().strip()
    return any(lower.startswith(p) for p in SKIP_PHRASES) and len(lower) < 60

compacted = []
for role, text in items:
    if is_boilerplate(text):
        continue
    # Avoid near-duplicates
    if compacted and compacted[-1][1][:80] == text[:80]:
        continue
    compacted.append((role, text))

# ── Output ─────────────────────────────────────────────────────────────────────
print(f"# Session activity summary — {TODAY}")
print(f"# Sessions analysed: {len(today_files)}  |  Items extracted: {len(compacted)}\n")

for role, text in compacted:
    label = "USER" if role == "user" else "DONE"
    # Truncate long assistant responses to first sentence/line
    if role == "assistant":
        text = text.split("\n")[0][:200]
    print(f"[{label}] {text}")
