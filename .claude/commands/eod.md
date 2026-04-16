# /eod - Generate End of Day Report

Generate a personalized EOD report for a team member, matching their writing style, applying humanization, and respecting saved user preferences.

## Usage

`/eod`

## Process

Follow these steps in order:

### Step 0: Load user preferences

Read `.user-preferences/EOD/preferences.md` if it exists. These preferences take effect during generation. If absent, proceed with defaults.

### Step 1: Read EOD reference file

Read `References/EOD.md` from the project root. Extract:
- All person names from `## SAMPLES <NAME>` section headers
- The EOD samples for each person (to learn their tone, structure, and format)

### Step 2: Ask which person

```
¿Para quién quieres generar el EOD?

1. [Name 1]
2. [Name 2]
...

Escribe el número o nombre.
```

Wait for the user's selection before continuing.

### Step 3: Extract and compact today's session activity

```bash
python3 .claude/skills/eod/scripts/extract-today-sessions.py "$PWD"
```

Reads every `.jsonl` in `~/.claude/projects/<project-slug>/` modified today, deduplicates and truncates content, outputs a compact `[USER]` / `[DONE]` summary.

From that output, identify meaningful work items:
- Features implemented or discussed
- Files created or modified
- Bugs fixed
- Deployments or configurations done
- PRs, branches, or integrations mentioned
- Blockers or pending items

Discard meta-tasks unless they are real deliverables. Compile 3–8 bullet points.

### Step 4: Ask for additional context

```
Basándome en la sesión de hoy, identifiqué lo siguiente:

- [item 1]
- [item 2]
...

¿Hay algo más que quieras agregar o corregir antes de generar el EOD?
```

Wait for the user's response before generating.

### Step 5: Generate the EOD

Using the confirmed activity list, the person's writing style from `References/EOD.md`, and loaded preferences, produce the EOD.

**Apply the humanizer skill** to the final text. The result must sound like a real developer wrote it — not generated. Vary sentence starts, avoid robotic phrasing, keep technical specificity.

**Output format — Google Chat compatible:**
- `*EOD*` or `*EOD Update*` as header (single asterisk = bold in Google Chat)
- Sub-section labels: `*Label*`
- Bullets: `- item` (hyphen + space)
- No markdown, no `##`, no backticks
- Sub-sections only if relevant and person's samples use them

### Step 6: Save the file

Create `References/EODS/` if needed. Save as:
```
References/EODS/YYYY-MM-DD.md
```

Output the EOD to chat for copy-paste into Google Chat.

### Step 7: Capture preference updates

Ask:
```
¿Hay algo del estilo, tono o formato que quieras ajustar para próximos EODs?
```

If the user provides feedback, extract it as a concrete rule and update `.user-preferences/EOD/preferences.md`:
- Create file/folder if they don't exist
- Append rules under a `## Rules` section — never remove existing ones
- Format: `- [rule description]`

If no feedback, skip silently.
