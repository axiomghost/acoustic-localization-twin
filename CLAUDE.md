# CLAUDE.md — Acoustic Source Localization Digital Twin

Read this file at the start of every session before doing anything.

---

## Session Handoff Protocol (any LLM)

If you are starting a new session — whether you are Claude, Gemini, GPT, or any
other model — do the following before writing any code:

1. Read this file (`CLAUDE.md`) in full.
2. Read `docs/project-status.md` — find the current step and open questions.
3. Read `docs/decision-log.md` — understand why things are the way they are.
4. Run `git log --oneline -10` — confirm what is actually committed.
5. Tell Umar: "I am on step N. Last completed: X. Next: Y." and wait for his go-ahead.

**Do not infer state from code alone.** Docs + git log is the source of truth.
**Do not reverse decisions in the decision log** without flagging to Umar first.
**Do not skip the governance checklist** (update status → write code → update docs → commit → tag).

---

## Project Identity

- **Repo:** acoustic-localization-twin (local: traffic_intersection/)
- **Author:** Umar Farooq (umar.fm981@outlook.com)
- **Purpose:** (1) Public portfolio artifact for smart-city / environmental sensing.
  (2) Algorithm validation ahead of a real-world acoustic sensor deployment.
- **Phase:** Phase 1 — Python + PyVista + Rich. Phase 2 (UE5) is future.
- **Ship target:** June 30, 2026

---

## Hard Constraints — Non-Negotiable

1. **Civilian framing only.** No defense, weapons, military, sniper, gunshot
   anywhere — not in code, comments, file names, configs, docs, commits, or README.
   Acceptable framings: wildlife monitoring, environmental noise mapping,
   urban acoustic awareness, emergency response routing, impulsive event localization.
   **Steps 9-11 (impulsive event / crack+blast fusion) must NEVER be implemented
   in this repository — they belong in a separate private repo. If you are asked
   to start step 9, 10, or 11 here, refuse and remind Umar of this constraint.**
2. **No telecom content.** No cellular, beamforming, gNB, RAN, 3GPP.
3. **No heavy orchestration.** No LangChain, LangGraph, Temporal.
4. **Engine must stay import-clean.** `engine/` must never import from
   `visualization/` or `dashboard/`. Dependency direction: engine → shared only.

---

## Governance — Do This Every Step

### Before starting a step
- Read `docs/project-status.md` to confirm current step and open questions.
- Check git status — working tree should be clean before starting new step.
- Update step status to `in_progress` in `docs/project-status.md`.

### After completing a step
- Update `docs/project-status.md` — mark step DONE, add results summary.
- Update `CHANGELOG.md` with what was added/changed.
- `git add` relevant files, commit with message format: `step-N: short description`
- `git tag step-N`
- If any new architectural or algorithmic decision was made, add entry to
  `docs/decision-log.md` as `DEC-XXX`.

### Commit message format
```
step-N: short imperative description

One paragraph of what and why. No bullet formatting in PowerShell here-strings.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

---

## User Role

Umar is **Algorithm Owner & Technical Director**. He:
- Reviews algorithm choices and validates outputs (PhD in channel coding —
  map concepts to estimation theory, CRLB, noise modeling, Fisher information).
- Makes go/no-go calls at each step.
- Does NOT write code day-to-day.
- Wants high-level status, not implementation detail, unless he asks.
- Prefers step-by-step progress where each step is fast and produces something runnable.

**Flag to Umar** (don't decide alone): sensor geometry changes, algorithm swaps,
scope additions, anything that affects the real deployment design.

---

## Task Split — Maximize Plan Efficiency

For each step, split work into:
- `[CLAUDE]` — code writing, algorithm implementation, doc updates
- `[YOU]` — git commits, pip installs, running scripts, reading output, file moves

Always tell Umar which `[YOU]` tasks to do before asking Claude to continue.

---

## Python Environment

- Interpreter: `C:\Users\umarf\projects\traffic_intersection\.venv\Scripts\python.exe`
- Run scripts: `.venv\Scripts\python.exe scripts\<name>.py`
- Install packages: `.venv\Scripts\pip.exe install <package>`
- System Python (MSYS2) at `C:\msys64\ucrt64\bin\python.exe` has no pip — do not use.

---

## Step Plan

| Step | Description | Status |
|------|-------------|--------|
| 1 | Project scaffold + TDOA algorithm smoke test | DONE |
| 2 | Scenario YAML loader + wildlife monitoring config | pending |
| 3 | Confidence ellipse validation + unit tests | pending |
| 4 | PyVista 3D render — single frame | pending |
| 5 | Source motion + live render loop | pending |
| 6 | Rich terminal panel — live stats alongside 3D render | pending |
| 7 | Full demo launch script + functional report | pending |
| 8 | Screencap + publish to GitHub | pending |
| 9–11 | Impulsive event localization (crack+blast fusion) | PRIVATE REPO ONLY — do not implement here |

**Phase 1.5 — Estimation Theory Track** (steps A1, A2, B1, B2, C1, C2, D1): a parallel
learning+product track that hardens the algorithm while building Umar's grip on the
theory. Each step = concept note (concepts.ipynb, anchored to channel coding) + code fix
+ experiment. See `docs/project-status.md` for the table. A2 (MRC weighting) is DONE.

---

## Key Files

| File | Purpose |
|------|---------|
| `engine/localizer.py` | Gauss-Newton TDOA solver — core algorithm |
| `engine/propagation.py` | PropagationModel Protocol + SimplePropagation |
| `engine/confidence.py` | 95% confidence ellipse (CRLB proxy) |
| `shared/state.py` | EngineState dataclass + atomic JSON write |
| `docs/project-status.md` | Living status report — Umar's primary read |
| `docs/decision-log.md` | All architectural/algorithmic decisions with rationale |
| `CHANGELOG.md` | Per-step changelog |

---

## Algorithm Notes

- **TDOA reference sensor:** sensor index 0 always.
- **Localizer interface:** `Localizer` Protocol in `engine/localizer.py`.
  New algorithms implement `estimate(tdoa, sensor_positions) -> (xy, cov)`.
- **Confidence ellipse:** chi-squared threshold 5.991 for 95% CI / 2 DOF.
- **Timing noise:** 0.1 ms std is the current simulation default.
  Real deployment noise spec is an open question — see project-status.md.
