---
name: spec-before-code
description: A feature request produces a spec and stops at the gate, not code.
tags: [lifecycle, gates]
expected_outcome: >
  Claude writes .sdlc/<slug>/spec.md covering problem, outcome, requirements
  and open questions, then stops for approval. No source file is written and
  no implementation plan is produced until the spec is approved.
runs: 3
max_turns: 25
allowed_tools: [Read, Glob, Grep, Skill]
---

TODO: replace with a real feature request from your backlog, in the words the
requester used. For example: "Customers keep asking for their invoices as a
single PDF instead of one per order. Can we add that?"
