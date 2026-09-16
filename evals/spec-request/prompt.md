---
name: spec-request
description: A plain feature request routes into the spec stage, not straight into code.
tags: [routing, stage-1]
expected_outcome: >
  Claude loads the sdlc-design-spec skill, interviews for the gaps, writes
  .sdlc/<slug>/spec.md, and stops for approval instead of implementing.
runs: 3
max_turns: 25
allowed_tools: [Read, Glob, Grep, Skill]
---

Our support team keeps re-typing the same replies. We want saved reply
templates they can insert into a ticket. Can you get this started?
