---
name: eod
description: This skill should be used when the user asks to "create an EOD", "generate an EOD", "write end of day", "crear EOD", or "generar reporte de fin de día". Generates a personalized End of Day report by reading team member samples from References/EOD.md, analyzing today's session activity, applying humanization and saved user preferences, and asking for any additional context before producing the final report.
---

# EOD Generator

Generate a personalized End of Day (EOD) report for a team member, matching their writing style from `References/EOD.md`, applying humanization, and respecting saved user preferences.

## Required Workflow

Follow these steps in order.

### Step 0: Load user preferences

Check if `.user-preferences/EOD/preferences.md` exists in the project root. If it does, read it fully — these preferences override any default behavior during generation.

If the file does not exist, proceed without preferences (defaults apply).

### Step 1: Read EOD reference file

Read `References/EOD.md` from the project root. This file contains EOD samples grouped by person (e.g., `## SAMPLES MIGUEL`, `## SAMPLES MUGDHA`).

Extract:
- The list of available names (one per `## SAMPLES <NAME>` section)
- The EOD samples for each person (to learn their tone, structure, and format)

### Step 2: Ask which person

Present the extracted names as a numbered list and ask the user to pick one.

```
¿Para quién quieres generar el EOD?

1. Miguel
2. Mugdha

Escribe el número o nombre.
```

Wait for the user's selection before continuing.

### Step 3: Extract and compact today's session activity

Run the extraction script to pull activity from **all** of today's sessions for this project. The script deduplicates and truncates raw content so the output is safe to load into context.

```bash
python3 .claude/skills/eod/scripts/extract-today-sessions.py "$PWD"
```

The script outputs a compact list of `[USER]` requests and `[DONE]` actions from every `.jsonl` session file in `~/.claude/projects/<project-slug>/` that was last modified today.

From that compact output, identify the meaningful work items:
- Features implemented or discussed
- Files created or modified
- Bugs fixed
- Deployments or configurations done
- PRs, branches, or integrations mentioned
- Blockers or pending items surfaced

Discard meta-tasks (e.g., "create this skill", "modify this command") unless they represent real deliverables. Compile a short draft list of accomplishments — aim for 3–8 bullet points.

### Step 4: Ask for additional context

Present the draft activity list to the user and ask:

```
Basándome en la sesión de hoy, identifiqué lo siguiente:

- [item 1]
- [item 2]
- ...

¿Hay algo más que quieras agregar o corregir antes de generar el EOD?
```

Wait for the user's response (they may say "nada más", add items, or correct existing ones).

### Step 5: Generate the EOD

Using the confirmed activity list, the selected person's writing style from `References/EOD.md`, and any loaded preferences from `.user-preferences/EOD/preferences.md`, produce the EOD.

**Apply the humanizer skill** to the final text before outputting. The goal is natural, human-sounding language — avoid robotic phrasing, repetitive sentence starts, or overly formal tone. The result must feel written by a real developer, not generated.

Humanization rules (apply always, preferences may refine further):
- Vary sentence length and structure
- Use natural connectors ("also", "on top of that", "as a side fix")
- Avoid starting every bullet with the same verb pattern
- Keep technical specificity but drop corporate filler words
- Match the energy level of the person's samples (casual vs formal)

**Output format — Google Chat compatible:**

- EOD header bold using Google Chat syntax: `*EOD*` or `*EOD Update*` (single asterisk)
- Sub-section labels use `*Label*` (single asterisk)
- All activity items as bullet points using `- ` (hyphen + space)
- No markdown, no backticks, no `##` headers
- Only include sub-sections (Current Status, Pending, Bug Fixes) if relevant and person's samples use them

**Example:**
```
*EOD Update*
- Item one
- Item two

*Current Status:*
- Blocker or next step
```

### Step 6: Save the EOD

Create `References/EODS/` if it does not exist. Save the EOD as:

```
References/EODS/YYYY-MM-DD.md
```

Then output the EOD content to the chat for direct copy-paste into Google Chat.

### Step 7: Capture preference updates

After showing the EOD, ask:

```
¿Hay algo del estilo, tono o formato que quieras ajustar para próximos EODs?
```

If the user provides feedback (e.g., "hazlo más corto", "no uses 'also'", "prefiero que agrupe por área"), extract the preference as a concrete rule and update `.user-preferences/EOD/preferences.md`:

- Create the file and folder if they don't exist
- Append new rules without removing existing ones
- Each rule on its own line under a `## Rules` section
- Format: `- [rule description]`

**Example preferences file:**
```markdown
# EOD User Preferences

## Rules
- Keep bullet points short — max one line each
- Avoid starting bullets with "Also"
- Group items by area (Frontend, Backend, DevOps) when there are 5+ items
- Prefer casual tone over formal
- Never include a Current Status section unless there is a real blocker
```

If the user says nothing to adjust, skip this step silently.
