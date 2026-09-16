---
name: sdlc-design-spec
description: >
  This skill should be used at the start of any new piece of work, when the
  user says "write a spec", "spec this out", "let's design this", "here's what
  we need to build", or hands over a ticket, request, incident finding, or
  feature idea that has no spec yet. Produces a committed spec.md holding the
  problem, requirements, design, and flagged concerns, and stops at the
  approval gate before any planning or coding.
metadata:
  version: "0.1.0"
---

# Stage 1 — Spec

Requirements and design collapse into a single session. The output is one
file — `spec.md` — that a person approves and every later stage reads.

**Do not write code in this stage. Do not write an implementation plan.**
Naming a file to change is planning; that belongs to Stage 2.

## Procedure

### 1. Locate the work item

Ask for a kebab-case slug if none is given. Create `.sdlc/<slug>/`. If the
directory already exists with a spec, read it and treat this as a revision, not
a new item.

### 2. Interview the requester

Fill the gaps, do not fabricate them. Ask about anything unanswered, batched
into one round:

- **Problem** — what is wrong or missing today, in the requester's own words.
- **Outcome** — what is true once this ships. Prefer observable statements over adjectives.
- **Users** — who touches this, and how often.
- **Affected systems** — services, schemas, jobs, third-party integrations.
- **Constraints** — deadlines, budgets, contracts, platforms, existing decisions that cannot be reopened.
- **Explicitly out of scope** — what this change deliberately does not do.
- **Success criteria** — how anyone can tell afterwards whether it worked.

Where the requester does not know, record the question in **Open questions**
rather than inventing an answer.

### 3. Read the standing constraints

Before drafting, read what already governs this repo:

- `CLAUDE.md` — conventions, architecture, known mistakes.
- Any organization standards skills that apply (security, compliance, brand, UX, accessibility, data classification).
- Neighbouring code and existing specs in `.sdlc/`, for consistent patterns and terminology.

<!-- TODO: List the standards skills your organization expects a spec to be
     checked against, e.g. secure-api-review, data-classification,
     design-system. Name them here so this stage always applies them. -->

### 4. Draft the spec

Copy `${CLAUDE_PLUGIN_ROOT}/templates/spec.md` to `.sdlc/<slug>/spec.md` and
fill it in. Write the design at the level of behaviour, contracts, and data —
not line-level implementation.

For UI work, produce or reference a visual mock and link it from the spec, so
Stage 3 can verify the built screen against something concrete.

### 5. Flag, do not resolve

Anything that touches security, privacy, data classification, licensing,
pricing, accessibility, regulatory scope, or an irreversible migration goes
into the **Flagged concerns** table with a named owner. Flagging is the job.
Resolving without the owner is not.

| Concern | Standard or policy | Owner | Status |
|---|---|---|---|

### 6. Present and stop

Show the requester:

- A short prose summary of the design in plain language.
- The flagged concerns, each with the person who must resolve it.
- The open questions.

Then state: *"This needs your approval before build planning starts."* Wait.
Do not proceed to Stage 2 in the same turn.

### 7. Record the gate

Once approved, set the front matter and commit:

```yaml
status: approved
approved_by: <name>
approved_at: <date>
```

Commit message: `spec(<slug>): <one-line outcome>`.

Every flagged concern must be `resolved` or explicitly `accepted` before the
status can become `approved`. If one is still open, the spec stays `in-review`.

## Quality bar

A spec is done when an engineer who was not in the conversation could read it
and know what to build and what not to build, and a reviewer could later use it
to judge whether the shipped code did what was asked.

Reject your own draft if it:

- Describes a solution without stating the problem it removes.
- Uses "improve", "optimize", "streamline" without a measurable outcome.
- Leaves an affected system unnamed.
- Silently resolves a concern that needed an owner.
