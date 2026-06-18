# Claude Code Hooks — Reference

**Official docs:** https://docs.anthropic.com/en/docs/claude-code/hooks

---

## What hooks are

Shell commands wired to Claude Code lifecycle events via `.claude/settings.json`.
When an event fires, Claude Code runs the command, reads stdout, and acts on the JSON response.

---

## Settings file locations

| File | Scope | Committed to git |
|------|-------|-----------------|
| `~/.claude/settings.json` | Global — all projects | No |
| `.claude/settings.json` | This project — all users | Yes (we use this) |
| `.claude/settings.local.json` | This project — you only | No (gitignored) |

Later files override earlier ones.

---

## Hook events (lifecycle order)

| Event | When it fires |
|-------|--------------|
| `SessionStart` | Once when a Claude session opens |
| `UserPromptSubmit` | When you submit a message |
| `PreToolUse` | Before Claude runs a tool (can block it) |
| `PostToolUse` | After a tool succeeds |
| `PostToolUseFailure` | After a tool fails |
| `Stop` | After every Claude response |
| `PreCompact` | Before context compaction |
| `PostCompact` | After context compaction |

---

## Config structure

```json
{
    "hooks": {
        "EventName": [
            {
                "matcher": "ToolName",
                "hooks": [
                    {
                        "type": "command",
                        "command": "your-script-here",
                        "shell": "powershell",
                        "timeout": 10,
                        "statusMessage": "Shown in spinner..."
                    }
                ]
            }
        ]
    }
}
```

`matcher` is optional — omit it to match all tools (used by `Stop` and `SessionStart`).  
For `PreToolUse`/`PostToolUse`, matcher filters by tool name: `"Bash"`, `"Write|Edit"`, etc.

---

## Hook stdout JSON protocol

Your command writes JSON to stdout. Claude Code reads it and acts:

```json
{ "systemMessage": "Text shown as banner in UI" }
```

```json
{ "continue": false, "stopReason": "Blocked: reason shown to user" }
```

```json
{
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "Text injected into Claude context invisibly"
    }
}
```

Silent exit (no output) = no action, no noise.

---

## Hook types

| Type | Use for |
|------|---------|
| `command` | Shell script — most common |
| `prompt` | LLM evaluates a condition |
| `agent` | Full agent with tools runs |

---

## What hooks cannot do

- Run inside Gemini, GPT, or any non-Claude-Code environment
- Replace doc-based sync protocol for multi-LLM handoffs
- Write meaningful content to docs (no session context)

---

## Hooks in this project

| Hook | Script | Purpose |
|------|--------|---------|
| `SessionStart` | `scripts/session_start.ps1` | Prints current step + git state on session open |
| `Stop` | `scripts/governance_check.ps1` | Reminds to commit/tag if step is in_progress and git is dirty |
